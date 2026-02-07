import json
import pandas as pd
jsonl_files = ["train2.jsonl", "valid2.jsonl", "sven.jsonl"]
data = []
for file in jsonl_files:
    with open(f"raw/{file}", "r") as f:
        for line in f:
            data.append(json.loads(line))
dfNew = pd.DataFrame(data)

dfTest = pd.DataFrame(dfNew, columns=['target', 'func'])

from sentence_transformers import SentenceTransformer,util
model = SentenceTransformer('all-MiniLM-L6-v2')

sentences1 = dfNew['func']

embeddings1 = model.encode(sentences1, convert_to_tensor=True)
cosine_scores = util.cos_sim(embeddings1, embeddings1)
npArr = cosine_scores.cpu().detach().numpy()

f= open('outputEmbedding.txt','w')
for i in range(len(npArr)):
  for j in range(len(npArr)):
    f.write(str(npArr[i][j])+" ")
  f.write("\n")
f.close()
