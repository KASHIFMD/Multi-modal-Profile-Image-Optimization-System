import mysql.connector
import csv
import tqdm
import time
from transformers import AutoTokenizer
from app.config import db_config_dev

# Model Path (Ensure it exists)
model_path = "/main_dir/app/models_pretrained/all-mpnet-base-v2"

# Logging function
def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

log("Loading tokenizer ...")

# Load SBERT Tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/all-mpnet-base-v2", 
    cache_dir=model_path, 
    local_files_only=True
)

log("Tokenizer loaded.")

# Connect to MySQL
log("Connecting to database ...")
conn = mysql.connector.connect(**db_config_dev)
cursor = conn.cursor()
log("Database connected.")

# Fetch unique main_catname & national_catid values
log("Fetching distinct main_catname and national_catid values ...")
cursor.execute("SELECT DISTINCT main_catname, national_catid FROM category_docid_view")
rows = cursor.fetchall()
log(f"Retrieved {len(rows)} unique category names.")

# Track OOV words and prepare batch updates
oov_word_set = set()  # Store **only unique OOV words**
update_data = []  # Batch updates

log("Processing categories ...")

# Process each unique main_catname with progress bar
for (main_catname, national_catid) in tqdm.tqdm(rows, desc="Processing Categories"):
    if main_catname:  # Ensure it's not None
        words = main_catname.lower().split()  # Convert to lowercase
        
        # Identify OOV words using improved tokenization logic
        oov_words = [word for word in words if tokenizer.tokenize(word) != [word]]  # Fully OOV check
        oov_words_str = ",".join(oov_words) if oov_words else None

        # Collect updates for batch processing
        update_data.append((oov_words_str, national_catid))  # Update using national_catid

        # Store unique OOV words
        oov_word_set.update(oov_words)  # Collect only unique OOV words

log("Processing completed.")

# Batch update to avoid multiple queries
log("Updating database in batch mode using national_catid ...")
update_query = """
    UPDATE temp_category_synonym_data_20250212
    SET main_catname_oovs_sbert = %s
    WHERE national_catid = %s
"""
cursor.executemany(update_query, update_data)
conn.commit()
log("Database successfully updated.")

# Save **only unique OOV words** to CSV file
csv_filename = "oov_words.csv"
log(f"Saving unique OOV words to {csv_filename} ...")

with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["unique_oovs"])  # Column Name
    for word in sorted(oov_word_set):  # Sort for readability
        writer.writerow([word])  # Write each unique OOV word

log(f"Total unique OOV words identified: {len(oov_word_set)}")
log(f"OOV words saved to: {csv_filename}")

# Close Connection
cursor.close()
conn.close()
# log("Database connection closed.")
