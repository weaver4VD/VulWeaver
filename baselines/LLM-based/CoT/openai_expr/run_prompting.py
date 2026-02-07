import argparse
import os
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import openai
from openai import OpenAI
from openai._types import NOT_GIVEN

from utils import SYS_INST, PROMPT_INST, PROMPT_INST_COT, ONESHOT_ASSISTANT, ONESHOT_USER, TWOSHOT_USER, TWOSHOT_ASSISTANT

import tiktoken

file_lock = threading.Lock()
stats_lock = threading.Lock()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  
    base_url="https://api.deepseek.com" 
)

def count_tokens(text, model="cl100k_base"):
    if not isinstance(text, str) or len(text) == 0:
        return 0
    
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except:
        pass
    
    token_count = 0
    
    words = text.split()
    for word in words:
        if len(word) == 0:
            continue
        token_count += max(1, len(word)
    
    special_chars = text.count('\n') + text.count('\t')
    token_count += special_chars
    
    return max(1, token_count)


def truncate_tokens_from_messages(messages, model, max_gen_length):
    if "deepseek" in model:
        return messages

    if model == "gpt-3.5-turbo-0125":
        max_tokens = 16385 - max_gen_length
    elif model == "gpt-4-0125-preview":
        max_tokens = 128000 - max_gen_length
    else:
        max_tokens = 4096 - max_gen_length
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3

    num_tokens = 3  
    trunc_messages = []
    for message in messages:
        tm = {}
        num_tokens += tokens_per_message
        for key, value in message.items():
            encoded_value = encoding.encode(value)
            num_tokens += len(encoded_value)
            if num_tokens > max_tokens:
                print(f"Truncating message: {value[:100]}...")
                tm[key] = encoding.decode(encoded_value[:max_tokens - num_tokens])
                break
            else:
                tm[key] = value
        trunc_messages.append(tm)
    return trunc_messages


def get_openai_chat(prompt, args):
    if args.fewshot_eg:
        messages = [
            {"role": "system", "content": SYS_INST},
            {"role": "user", "content": ONESHOT_USER},
            {"role": "assistant", "content": ONESHOT_ASSISTANT},
            {"role": "user", "content": TWOSHOT_USER},
            {"role": "assistant", "content": TWOSHOT_ASSISTANT},
            {"role": "user", "content": prompt["prompt"]}
        ]
    else:
        messages = [
            {"role": "system", "content": SYS_INST},
            {"role": "user", "content": prompt["prompt"]}
        ]
    
    messages = truncate_tokens_from_messages(messages, args.model, args.max_gen_length)

    input_str = "".join([m["content"] for m in messages])
    input_tokens = count_tokens(input_str)

    try:
        start_time = time.time()

        response = client.chat.completions.create(
            model=args.model,
            messages=messages,
            max_tokens=args.max_gen_length,
            temperature=args.temperature,
            seed=args.seed,
            logprobs=args.logprobs,
            top_logprobs=5 if args.logprobs else NOT_GIVEN,
        )

        duration = time.time() - start_time

        response_content = response.choices[0].message.content
        response_logprobs = response.choices[0].logprobs.content[0].top_logprobs if args.logprobs else None
       
        output_tokens = count_tokens(response_content)
        
        log_prob_mapping = {}
        if response_logprobs:
            for topl in response_logprobs:
                log_prob_mapping[topl.token] = topl.logprob
        
        metrics = {
            "duration": duration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
        
        return response_content, log_prob_mapping, metrics

    except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as error:
        retry_time = error.retry_after if hasattr(error, "retry_after") else 5
        print(f"Rate Limit or Connection Error. Sleeping for {retry_time} seconds ...")
        time.sleep(retry_time)
        return get_openai_chat(prompt, args)
    
    except openai.BadRequestError as error:
        print(f"Bad Request Error: {error}")
        return None, None, {"duration": 0, "input_tokens": 0, "output_tokens": 0}


def process_single_prompt(prompt, args, output_file):
    response, logprobs, metrics = get_openai_chat(prompt, args)
    
    if logprobs:
        prompt["logprobs"] = logprobs
    
    if response is None:
        response = "ERROR"
    
    if metrics:
        prompt["metrics"] = metrics
    
    prompt["response"] = response
    
    with file_lock:
        with open(output_file, "a") as f:
            f.write(json.dumps(prompt))
            f.write("\n")
            f.flush()
    
    return metrics


def construct_prompts(input_file, inst):
    with open(input_file, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]
    prompts = []
    for sample in samples:
        key = sample["project"] + "_" + sample["commit_id"]
        p = {"sample_key": key}
        p["func"] = sample["func"]
        p["target"] = sample["target"]
        p["prompt"] = inst.format(func=sample["func"])
        prompts.append(p)
    return prompts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default="deepseek-chat", help='Model name')
    parser.add_argument('--prompt_strategy', type=str, choices=["std_cls", "cot"], default="std_cls", help='Prompt strategy')
    parser.add_argument('--data_path', type=str, help='Data path')
    parser.add_argument('--output_folder', type=str, help='Output folder')
    parser.add_argument('--temperature', type=float, default=0.0, help='Sampling temperature')
    parser.add_argument('--max_gen_length', type=int, default=1024)
    parser.add_argument('--seed', type=int, default=12345)
    parser.add_argument('--logprobs', action="store_true", help='Return logprobs')
    parser.add_argument('--fewshot_eg', action="store_true", help='Use few-shot examples')
    parser.add_argument('--num_threads', type=int, default=5, help='Number of concurrent threads')
    args = parser.parse_args()

    output_file = os.path.join(args.output_folder, f"{args.model}_{args.prompt_strategy}_logprobs{args.logprobs}_fewshoteg{args.fewshot_eg}.jsonl")
    
    open(output_file, "w").close()
    
    if args.prompt_strategy == "std_cls":
        inst = PROMPT_INST
    elif args.prompt_strategy == "cot":
        inst = PROMPT_INST_COT
    else:
        raise ValueError("Invalid prompt strategy")
    
    prompts = construct_prompts(args.data_path, inst)

    total_time = 0
    total_input_tokens = 0
    total_output_tokens = 0
    processed_count = 0

    print(f"Requesting {args.model} to respond to {len(prompts)} prompts using {args.num_threads} threads...")
    
    with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
        future_to_prompt = {
            executor.submit(process_single_prompt, p, args, output_file): p 
            for p in prompts
        }
        
        with tqdm(total=len(prompts)) as pbar:
            for future in as_completed(future_to_prompt):
                try:
                    metrics = future.result()
                    if metrics:
                        with stats_lock:
                            total_time += metrics["duration"]
                            total_input_tokens += metrics["input_tokens"]
                            total_output_tokens += metrics["output_tokens"]
                            processed_count += 1
                except Exception as exc:
                    print(f"Task generated an exception: {exc}")
                finally:
                    pbar.update(1)
    
    if processed_count > 0:
        print("\n" + "="*30)
        print(f"📊 Statistics for {processed_count} items:")
        print(f"⏱️  Average Time: {total_time / processed_count:.2f} s/item")
        print(f"📥 Average Input Tokens: {total_input_tokens / processed_count:.1f} tokens/item")
        print(f"📤 Average Output Tokens: {total_output_tokens / processed_count:.1f} tokens/item")
        print(f"💰 Average Total Tokens: {(total_input_tokens + total_output_tokens) / processed_count:.1f} tokens/item")
        print("="*30 + "\n")
    else:
        print("No items processed successfully.")


if __name__ == "__main__":
    main()