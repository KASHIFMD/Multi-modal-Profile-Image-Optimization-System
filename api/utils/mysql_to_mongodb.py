# import pymysql
import mysql.connector
import pymongo
import json
import urllib.parse
from app.config import db_config_dev, MONGO_URI
from app.services.embeddings import update_api_flag_docids
import os

# MongoDB details
MONGO_DB_NAME = "db_product"
MONGO_COLLECTION_NAME = "tbl_catalogue_details_imgrel"


def remove_domain(url):
    """Removes the domain name from a URL."""
    parsed_url = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))


def fetch_mysql_data(limit, offset):
    """Fetch data from MySQL imgrel_scores table."""
    try:
        connection = mysql.connector.connect(**db_config_dev)
    except Exception as e:
        print(f"The is mysql connection issue in get_details python code")
    if connection.is_connected():
        cursor = connection.cursor(dictionary=True)
        
    query = f"""
    WITH unique_docids AS (
        SELECT docid
        FROM imgrel_scores
        WHERE cat_score_01_tfidf_finetune_15 IS NOT NULL
        GROUP BY docid
        ORDER BY docid
        LIMIT {limit} OFFSET {offset}
    )
    SELECT i.product_id, i.docid, i.product_url, i.desc_api, i.cat_score_01_tfidf_finetune_15, i.contractid
    FROM imgrel_scores i
    JOIN unique_docids u ON i.docid = u.docid
    WHERE api_flag_tfidf_finetune_15 = 3;
    """

    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    connection.close()
    return data

def process_data(mysql_data):
    """Transform MySQL data into MongoDB schema format."""
    doc_dict = {}

    for row in mysql_data:
        docid = row["docid"].lower()
        product_id = str(row["product_id"])  # Convert to string for dictionary keys
        product_url = row["product_url"]
        if(product_url is None):
            continue
        product_url = remove_domain(product_url)
        desc_api = row["desc_api"]
        contractid = float(row["contractid"]) if row["contractid"] else 0.0  # Ensure floating-point storage
        cat_score_json = json.loads(row["cat_score_01_tfidf_finetune_15"])

        # Initialize document if not exists
        if docid not in doc_dict:
            doc_dict[docid] = {
                "did": docid,
                "dimg": {},
                "cat": [] #change to array from object
            }

        # Add product details to dimg
        doc_dict[docid]["dimg"][product_id] = {
            "purl": product_url,
            "desc": desc_api,
            "qual": contractid
        }

        # Process category scores
        for category_name, details in cat_score_json.items():
            category_id = details["category_id"]
            score = details["score"]

            # Initialize category if not exists
            if category_id not in [item["catid"] for item in doc_dict[docid]["cat"]]:
                doc_dict[docid]["cat"].append({
                    "catid": category_id,
                    "cname": category_name,
                    "imgs": []
                })

            # Add image reference
            for cat_item in doc_dict[docid]["cat"]:
                if cat_item["catid"] == category_id:
                    cat_item["imgs"].append({
                        "pid": int(product_id),
                        "scr": float(score)
                    })

    # Convert dictionary values into required MongoDB list format
    final_docs = []
    for docid, details in doc_dict.items():
        # details["dimg"] = details["dimg"].values()  # Convert dictionary to list
        # details["cat"] = list(details["cat"].values())  # Convert dictionary to list
        final_docs.append(details)

    return final_docs

def insert_into_mongodb(documents):
    """Insert structured data into MongoDB using connection string with upsert."""
    try:
        # Establish connection using MONGO_URI
        with pymongo.MongoClient(MONGO_URI) as client:
            # Access database
            db = client[MONGO_DB_NAME]
            collection = db[MONGO_COLLECTION_NAME]

            if documents:
                bulk_operations = []
                docids = []
                for doc in documents:
                    # print(doc)
                    # return
                    docids.append(doc["did"])
                    bulk_operations.append(
                        pymongo.UpdateOne(
                            {"did": doc["did"]},  # Match existing document by 'did' (docid)
                            {"$set": doc},  # Update the document fields
                            upsert=True  # Insert if it does not exist
                        )
                    )

                # Execute bulk write operation
                result = collection.bulk_write(bulk_operations)
                print(f"✅ Matched: {result.matched_count}, Modified: {result.modified_count}, Inserted: {result.upserted_count} documents.")
                update_api_flag_docids(docids)

    except Exception as e:
        print(f"❌ Error inserting documents into MongoDB: {e}")



if __name__ == "__main__":
    limit = 1000  # Process 1000 docids at a time
    offset = 0  # Start at the beginning
    total_docids = 0  # Track total docids processed
    batch_count = 0  # Count number of batches processed

    print("🚀 Starting data transfer from MySQL to MongoDB...\n")

    while True:
        print(f"\n➡ Fetching batch {batch_count + 1} (offset={offset}, limit={limit})...")

        mysql_data = fetch_mysql_data(limit, offset)
        if not mysql_data:
            print("\n✅ All docids processed! No more data to fetch.")
            break  # Exit loop when no more data is available

        batch_docids = len(set(row["docid"] for row in mysql_data))  # Unique docids in this batch
        total_docids += batch_docids  # Track total processed docids

        print(f"📊 Stats: Batch {batch_count + 1} | Fetched {len(mysql_data)} records | Unique docids: {batch_docids} | Total docids processed: {total_docids}")

        print(f"🔄 Processing {len(mysql_data)} records into MongoDB schema...")
        mongo_docs = process_data(mysql_data)

        print(f"💾 Inserting {len(mongo_docs)} documents into MongoDB...")
        insert_into_mongodb(mongo_docs)

        offset += limit  # Move to next batch
        batch_count += 1  # Increment batch count

    print(f"\n✅ Data transfer completed successfully! 🎉")
    print(f"📌 Final Stats: Total Batches: {batch_count} | Total Unique Docids Processed: {total_docids}")
