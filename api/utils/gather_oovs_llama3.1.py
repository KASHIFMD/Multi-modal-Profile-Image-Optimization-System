import csv
from transformers import AutoTokenizer

# Load LLaMA 3.1 8B Tokenizer
model_name = "meta-llama/Llama-3.1-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load OOV words from CSV file
oov_words = []
with open("oov_words.csv", mode="r", newline="") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    for row in reader:
        if row:  # Ensure non-empty rows
            oov_words.append(row[0].strip())

# Check if words are in LLaMA 3.1 vocabulary
llama_vocab_check = []
for word in oov_words:
    tokens = tokenizer.tokenize(word)
    if tokens == [word]:  # Fully recognized
        llama_vocab_check.append([word, "Present"])
    else:  # Tokenized into subwords = OOV
        llama_vocab_check.append([word, "OOV"])

# Save results to CSV file
output_filename = "llama3_vocab_check.csv"
with open(output_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["word", "status"])  # Column Headers
    writer.writerows(llama_vocab_check)  # Write data

print(f"✅ Vocabulary check complete. Results saved to {output_filename}")
