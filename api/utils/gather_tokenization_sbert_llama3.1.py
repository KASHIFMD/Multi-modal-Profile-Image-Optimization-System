import csv
import time
from transformers import AutoTokenizer

# Load LLaMA 3.1 8B Tokenizer
llama_model = "meta-llama/Llama-3.1-8B"
llama_tokenizer = AutoTokenizer.from_pretrained(llama_model)

# Load SBERT Tokenizer
model_path = "/main_dir/app/models_pretrained/all-mpnet-base-v2"
sbert_model = "sentence-transformers/all-mpnet-base-v2"
sbert_tokenizer = AutoTokenizer.from_pretrained(
    sbert_model, cache_dir=model_path, local_files_only=True
)

# Logging function
def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

log("Loading OOV words from CSV...")

# Load OOV words from CSV file
oov_words = []
with open("oov_words.csv", mode="r", newline="") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    for row in reader:
        if row:  # Ensure non-empty rows
            oov_words.append(row[0].strip())

log(f"Loaded {len(oov_words)} words. Performing tokenization...")

# Check vocabulary and tokenize
results = []
for word in oov_words:
    llama_tokens = llama_tokenizer.tokenize(word)
    sbert_tokens = sbert_tokenizer.tokenize(word)
    
    status = "Present" if llama_tokens == [word] else "OOV"
    
    results.append([word, status, ",".join(sbert_tokens), ",".join(llama_tokens)])

# Save results to CSV file
output_filename = "llama3_vocab_check_tokenizers.csv"
with open(output_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["word", "status", "sbert_tokenization", "llama_tokenization"])
    writer.writerows(results)

log(f"✅ Vocabulary check complete. Results saved to {output_filename}")
