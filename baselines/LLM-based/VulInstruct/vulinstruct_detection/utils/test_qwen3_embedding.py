
import torch
import torch.nn.functional as F
import time
import numpy as np
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def get_detailed_instruct(task_description: str, query: str) -> str:
    return f'Instruct: {task_description}\nQuery: {query}'

def test_qwen3_embedding_transformers():
    
    print("🚀 Starting test of Qwen3-Embedding-0.6B + Transformers")
    print("=" * 60)
    
    model_name = "/nfs100/zhuhao/models/public/Qwen3-Embedding-0.6B"
    
    try:
        print("📥 Loading model...")
        start_time = time.time()
        
        tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side='left')
        
        if torch.cuda.is_available():
            model = AutoModel.from_pretrained(
                model_name, 
                torch_dtype=torch.float16,
                device_map="auto"
            ).cuda()
            print("✅ Model loaded using GPU")
        else:
            model = AutoModel.from_pretrained(model_name)
            print("✅ Model loaded using CPU")
        
        load_time = time.time() - start_time
        print(f"✅ Model loading completed, time elapsed: {load_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return
    
    task_description = 'Given a web search query, retrieve relevant passages that answer the query'
    
    queries = [
        get_detailed_instruct(task_description, 'What is the capital of China?'),
        get_detailed_instruct(task_description, 'Explain gravity'),
        get_detailed_instruct(task_description, 'How does machine learning work?'),
        get_detailed_instruct(task_description, 'What is Python programming?'),
    ]
    
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
        "Python is a high-level programming language known for its simplicity and readability.",
        "The Great Wall of China is an ancient series of walls and fortifications built to protect Chinese states.",
        "Artificial intelligence is transforming various industries by automating complex tasks.",
        "Beijing is known for its rich history, cultural landmarks, and modern architecture.",
    ]
    
    all_texts = queries + documents
    
    print(f"📝 Preparing to test {len(queries)} queries and {len(documents)} documents")
    print("\nQuery examples:")
    for i, query in enumerate(queries[:2], 1):
        query_short = query.split("Query: ")[1] if "Query: " in query else query
        print(f"  {i}. {query_short}")
    
    print("\nDocument examples:")
    for i, doc in enumerate(documents[:3], 1):
        print(f"  {i}. {doc}")
    
    try:
        print("\n🔄 Generating embeddings...")
        start_time = time.time()
        
        max_length = 8192
        
        batch_dict = tokenizer(
            all_texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        
        batch_dict = batch_dict.to(model.device)
        
        with torch.no_grad():
            outputs = model(**batch_dict)
            embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        
        embeddings = F.normalize(embeddings, p=2, dim=1)
        
        embed_time = time.time() - start_time
        print(f"✅ Embedding generation completed, time elapsed: {embed_time:.3f} seconds")
        
        print(f"\n📊 Embedding info:")
        print(f"  - Shape: {embeddings.shape}")
        print(f"  - Data type: {embeddings.dtype}")
        print(f"  - Device: {embeddings.device}")
        print(f"  - Dimensions: {embeddings.shape[1]}")
        
        query_embeddings = embeddings[:len(queries)]
        doc_embeddings = embeddings[len(queries):]
        
        print("\n🔍 Calculating similarity...")
        similarity_scores = query_embeddings @ doc_embeddings.T
        
        print(f"\n📈 Similarity matrix ({len(queries)} x {len(documents)}):")
        print("=" * 60)
        
        for i, query in enumerate(queries):
            query_short = query.split("Query: ")[1] if "Query: " in query else query
            print(f"\nQuery {i+1}: {query_short}")
            print("Most relevant documents:")
            
            scores = similarity_scores[i]
            top_indices = torch.argsort(scores, descending=True)[:3]
            
            for rank, doc_idx in enumerate(top_indices, 1):
                score = scores[doc_idx].item()
                doc_preview = documents[doc_idx][:60] + "..." if len(documents[doc_idx]) > 60 else documents[doc_idx]
                print(f"  {rank}. Similarity: {score:.4f} - {doc_preview}")
        
        print(f"\n⚡ Performance statistics:")
        print(f"  - Model loading time: {load_time:.2f} seconds")
        print(f"  - Embedding generation time: {embed_time:.3f} seconds")
        print(f"  - Average per text: {embed_time/len(all_texts)*1000:.2f} milliseconds")
        print(f"  - Throughput: {len(all_texts)/embed_time:.1f} texts/second")
        
        if torch.cuda.is_available():
            memory_used = torch.cuda.max_memory_allocated() / 1024**3
            print(f"  - Peak GPU memory usage: {memory_used:.2f}GB")
        
        print(f"\n🔬 Embedding quality validation:")
        
        query_self_sim = query_embeddings @ query_embeddings.T
        avg_query_sim = (query_self_sim.sum() - query_self_sim.trace()) / (len(queries) * (len(queries) - 1))
        print(f"  - Average similarity between queries: {avg_query_sim:.4f} (lower is better)")
        
        doc_self_sim = doc_embeddings @ doc_embeddings.T
        avg_doc_sim = (doc_self_sim.sum() - doc_self_sim.trace()) / (len(documents) * (len(documents) - 1))
        print(f"  - Average similarity between documents: {avg_doc_sim:.4f}")
        
        max_similarities = similarity_scores.max(dim=1)[0]
        print(f"  - Highest similarity for each query: {max_similarities.tolist()}")
        
        print("\n✅ Testing completed!")
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return

def check_requirements():
    print("🔍 Checking environment requirements...")
    
    import sys
    print(f"Python version: {sys.version}")
    
    print(f"PyTorch version: {torch.__version__}")
    
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError:
        print("❌ Please install transformers: pip install transformers")
        return False
    
    if torch.cuda.is_available():
        print(f"CUDA available: ✅ (version: {torch.version.cuda})")
        print(f"GPU device: {torch.cuda.get_device_name()}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    else:
        print("CUDA available: ❌ (will use CPU)")
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    if check_requirements():
        test_qwen3_embedding_transformers()