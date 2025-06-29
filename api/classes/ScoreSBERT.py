from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import os, json, sys
import numpy as np
from pymongo import MongoClient
from bson.decimal128 import Decimal128
from collections import defaultdict
import time

from pymongo import MongoClient
from collections import defaultdict
import mysql.connector
import urllib.parse
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
import os
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

# MySQL Database connection details
db_config_prod_slave = {
    'host':"192.168.17.132",
    'database': "db_product",
    'port': 3306,
    "user": "db_user_name",
    "password": "db_password",
}
vectorDB_path = "/var/log/images/ml_models/vector_db/milvus_lite.db"
if not os.path.exists(vectorDB_path):
    raise FileNotFoundError(f"Milvus DB file not found at {vectorDB_path}. Please ensure that the dataset is available.")
    
vectorDB_client = MilvusClient(vectorDB_path)
collection_name_cat = "sbert_embeddings_cat"
collection_name_text = "sbert_embeddings_text"
# Check if collection exists
if not vectorDB_client.has_collection(collection_name_cat):
    field_cid = FieldSchema(name="cid", dtype=DataType.INT64, description="Category ID", is_primary=True)
    field_cname = FieldSchema(name="cname", dtype=DataType.VARCHAR, description="Category name", max_length=512)
    field_model = FieldSchema(name="model", dtype=DataType.VARCHAR, description="Model name", max_length=128)
    field_vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, description="Vector", dim=768)
    fields = [field_cid, field_cname, field_model, field_vector]
    collection_schema = CollectionSchema(fields=fields)

    index_params = vectorDB_client.prepare_index_params()
    index_params.add_index(field_name = "vector", metric_type="COSINE")
    vectorDB_client.create_collection(collection_name_cat, schema=collection_schema, index_params=index_params, consistency_level="Strong")

if not vectorDB_client.has_collection(collection_name_text):
    field_text = FieldSchema(name="text", dtype=DataType.VARCHAR, description="Text content", max_length=512, is_primary=True)
    field_model = FieldSchema(name="model", dtype=DataType.VARCHAR, description="Model name", max_length=128)
    field_vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, description="Vector", dim=768)  # Ensure vector field is defined
    fields = [field_text, field_model, field_vector]
    collection_schema = CollectionSchema(fields=fields)  # Include vector field in schema
    
    index_params = vectorDB_client.prepare_index_params()
    index_params.add_index(field_name = "vector", metric_type="COSINE")
    vectorDB_client.create_collection(collection_name_text, schema=collection_schema, index_params=index_params, consistency_level="Strong")
    
connection_prod = mysql.connector.connect(**db_config_prod_slave)
# MongoDB setup
client = MongoClient("mongodb://content_process:C0nTent_pR0$3S@192.168.24.91:27017,192.168.24.92:27017,192.168.24.93:27017,192.168.24.94:27017,192.168.13.201:27017/admin?w=majority&readPreference=primary&replicaSet=jdcontent&authMechanism=SCRAM-SHA-1")

db = client['db_product']
imgrel_collection = db['tbl_catalogue_details_imgrel']

class ModelHandlerSBERT():    
    def __init__(self, model_name="all-mpnet-base-v2_allowed_words_15", finetuned=False):
        # Define local paths for the models
        if finetuned:
            self.model_path = "/var/log/images/ml_models/SBERT_models/models_finetuned/" + model_name
        else:
            self.model_path = "/var/log/images/ml_models/SBERT_models/models_pretrained"
        print("self.model_path: ", self.model_path)
        if not os.path.exists(self.model_path):
            print(f"[Error] Model file not found at {self.model_path}. Exiting.")
            sys.exit(1)
        print("Model Loading ...")
        start = time.time()
        self.embedding_model = SentenceTransformer(self.model_path)
        end = time.time()
        print("Model Loaded Successfully")
        print(f"Time taken: {end-start} seconds.")
        self.milvus_client = vectorDB_client  # Use the global MilvusClient instance
        
    def get_or_cache_vector(self, text, vector_type="text", model="allowed_words_15", catid=None):
        text_lc = text.lower()

        if vector_type == "text":
            collection_name = "sbert_embeddings_text"

            # Step 1: Check if vector already exists
            search_result = self.milvus_client.query(
                collection_name=collection_name,
                filter=f'model == "{model}" and text == "{text_lc}"',
                output_fields=["vector"]
            )
            if search_result and len(search_result) > 0:
                return np.array(search_result[0]["vector"], dtype=float)

            # Step 2: Not found – generate and insert
            vector = self.embedding_model.encode(text_lc)
            self.milvus_client.insert(
                collection_name=collection_name,
                data={"text": text_lc, "vector": vector, "model": model}
            )
            return vector

        elif vector_type == "cat":
            if catid is None:
                raise ValueError("catid must be provided for vector_type='cat'")

            collection_name = "sbert_embeddings_cat"

            search_result = self.milvus_client.query(
                collection_name=collection_name,
                filter=f'model == "{model}" and cname == "{text_lc}"',
                output_fields=["vector"]
            )
            if search_result and len(search_result) > 0:
                return np.array(search_result[0]["vector"], dtype=float)

            vector = self.embedding_model.encode(text_lc)
            self.milvus_client.insert(
                collection_name=collection_name,
                data={"cid": catid, "cname": text_lc, "vector": vector, "model": model}
            )
            return vector

        else:
            raise ValueError("Unsupported vector_type. Use 'text' or 'cat'.")

    def get_tfidf_weighted_embeddings(self, category_list, embedding_model):
        tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = tfidf_vectorizer.fit_transform(category_list)
        tfidf_weights = tfidf_matrix.toarray()
        feature_names = tfidf_vectorizer.get_feature_names_out()
        feature_name_to_index = {word: idx for idx, word in enumerate(feature_names)}

        # Precompute embeddings for all unique words
        unique_words = set(word.lower() for cat in category_list for word in cat.split())
        word_embeddings_dict = {
            word: self.get_or_cache_vector(word, vector_type="text") for word in unique_words if word in feature_name_to_index
        }

        embedding_dim = next(iter(word_embeddings_dict.values())).shape[0]
        category_embeddings = np.zeros((len(category_list), embedding_dim))

        for i, category in enumerate(category_list):
            words = category.split()
            word_embeddings = []
            weights = []

            for word in words:
                word = word.lower()
                if word in feature_name_to_index and word in word_embeddings_dict:
                    idx = feature_name_to_index[word]
                    weight = tfidf_weights[i, idx]
                    word_embeddings.append(word_embeddings_dict[word] * weight)
                    weights.append(weight)

            if word_embeddings:
                category_embeddings[i] = np.average(word_embeddings, axis=0, weights=weights)
            else:
                category_embeddings[i] = np.zeros(embedding_dim)

        return category_embeddings
    
    def get_category_score_embeddings(self, model, data, tfidf=False):
        docid = data.get("docid")
        product_id = data.get("product_id")
        product_url = data.get("product_url")
        description = data.get("description", "")
        categories = data.get("categories", {})

        if not categories or not description.strip():
            return None, None

        # Extract category names and their keys
        category_list = list(categories.values())
        catid_list = list(categories.keys())

        # Get image embedding
        image_embedding = self.embedding_model.encode(description)
        image_embedding = image_embedding.reshape(1, -1).astype(float)

        # Get category embeddings
        a = time.time()
        if tfidf:
            search_embeddings = self.get_tfidf_weighted_embeddings(category_list, self.embedding_model).astype(float)
        else:
            # For category names
            search_embeddings = np.array([
                self.get_or_cache_vector(cat, vector_type="cat", catid = catid) for catid, cat in categories
            ]).astype(float)
            
        b = time.time()
        print(f"Time taken for category embeddings fn: {b-a} seconds")

        # Compute similarity
        similarities = self.embedding_model.similarity(image_embedding, search_embeddings)

        return similarities, catid_list

    def get_quality_score(self, pid):
        select_query = "SELECT contractid FROM tbl_catalogue_details WHERE product_id = %s;"
        # Execute the query with parameterized inputs
        cursor = connection_prod.cursor(dictionary=True)
        cursor.execute(select_query, (pid,))
        row = cursor.fetchone()
        print("### row:", row)
        quality_score = float(row["contractid"]) if row and row["contractid"] is not None else -1.0
        return quality_score
    
    def remove_domain(self, url):
        """Removes the domain name from a URL."""
        parsed_url = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse(('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))

    def update_mongodb(self, mongodb_data, did, pid, purl):
        if not mongodb_data:
            return
        
        pid_str = str(pid)
        
        # Fetch existing doc if exists
        existing_doc = imgrel_collection.find_one({"did": did}) or {}
        existing_cat = {cat["catid"]: cat for cat in existing_doc.get("cat", [])}
        existing_dimg = existing_doc.get("dimg", {})

        # Prepare updated structures
        new_cat = defaultdict(lambda: {"catid": None, "cname": None, "imgs": []})
        new_dimg = {}

        for item in mongodb_data:
            catid = item["catid"]
            cname = item["cname"]
            scr = item["scr"]

            # Handle category-wise image insertion
            new_cat[catid]["catid"] = catid
            new_cat[catid]["cname"] = cname
            new_cat[catid]["imgs"].append({"pid": pid, "scr": scr})

        # Merge new_cat into existing_cat
        for catid, new_cat_data in new_cat.items():
            if catid not in existing_cat:
                existing_cat[catid] = new_cat_data
            else:
                existing_pids = {img["pid"] for img in existing_cat[catid].get("imgs", [])}
                for img in new_cat_data["imgs"]:
                    if img["pid"] not in existing_pids:
                        existing_cat[catid]["imgs"].append(img)

        qual = self.get_quality_score(pid)
        print(f"Quality score for pid {pid}: {qual}")
        pid_entry = {
            "purl": self.remove_domain(purl),
            "qual": qual
        }
        
        # Add even if already present
        existing_dimg[pid_str] = pid_entry
        
        # Final merged doc
        update_doc = {
            "did": did,
            "cat": list(existing_cat.values()),
            "dimg": existing_dimg
        }
        # Upsert updated data
        imgrel_collection.update_one(
            {"did": did},
            {"$set": update_doc},
            upsert=True
        )

        print(f"[✓] MongoDB safely updated for docid: {did}")

    def update_mongodb_pipeline(self, mongodb_data, did, pid, purl):
        if not mongodb_data:
            return

        pid_str = str(pid)
        qual = self.get_quality_score(pid)
        pid_entry = {"purl": self.remove_domain(purl), "qual": qual}

        # Start building the pipeline
        pipeline = []

        # Stage 1: upsert dimg.<pid>
        pipeline.append({
            "$set": {f"dimg.{pid_str}": pid_entry}
        })

        # For each category in mongodb_data, add one pipeline stage
        for item in mongodb_data:
            catid = item["catid"]
            cname = item["cname"]
            scr   = item["scr"]
            new_img = {"pid": pid, "scr": scr}
            new_cat = {"catid": catid, "cname": cname, "imgs": [new_img]}

            pipeline.append({
                "$set": {
                    "cat": {
                        # Rebuild the cat array:
                        "$let": {
                            "vars": {
                                # find any existing category with this catid
                                "match": {
                                    "$filter": {
                                        "input": "$cat",
                                        "as": "c",
                                        "cond": { "$eq": ["$$c.catid", catid] }
                                    }
                                }
                            },
                            "in": {
                                "$cond": [
                                    # If we found at least one match
                                    { "$gt": [{ "$size": "$$match" }, 0] },
                                    # → update that category’s imgs
                                    {
                                        "$map": {
                                            "input": "$cat",
                                            "as": "c",
                                            "in": {
                                                "$cond": [
                                                    { "$eq": ["$$c.catid", catid] },
                                                    {
                                                        # merge existing category with updated imgs
                                                        "$mergeObjects": [
                                                            "$$c",
                                                            {
                                                                "imgs": {
                                                                    "$let": {
                                                                        "vars": {
                                                                            # check if this pid already exists
                                                                            "imgMatch": {
                                                                                "$filter": {
                                                                                    "input": "$$c.imgs",
                                                                                    "as": "img",
                                                                                    "cond": { "$eq": ["$$img.pid", pid] }
                                                                                }
                                                                            }
                                                                        },
                                                                        "in": {
                                                                            "$cond": [
                                                                                { "$gt": [{ "$size": "$$imgMatch" }, 0] },
                                                                                # replace existing entry
                                                                                {
                                                                                    "$map": {
                                                                                        "input": "$$c.imgs",
                                                                                        "as": "img",
                                                                                        "in": {
                                                                                            "$cond": [
                                                                                                { "$eq": ["$$img.pid", pid] },
                                                                                                new_img,
                                                                                                "$$img"
                                                                                            ]
                                                                                        }
                                                                                    }
                                                                                },
                                                                                # append new entry
                                                                                { "$concatArrays": ["$$c.imgs", [new_img]] }
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        ]
                                                    },
                                                    # if not the target catid, leave untouched
                                                    "$$c"
                                                ]
                                            }
                                        }
                                    },
                                    # No existing cat → append a brand-new category object
                                    { "$concatArrays": ["$cat", [new_cat]] }
                                ]
                            }
                        }
                    }
                }
            })

        # Finally execute the update in one call
        imgrel_collection.update_one(
            {"did": did},
            pipeline,
            upsert=True
        )

    def update_mongodb_bulk(self, mongodb_data, did, pid, purl):
        if not mongodb_data:
            return

        operations = []
        operations.append(
            UpdateOne(
                {"did": did},
                {"$setOnInsert": {"did": did, "cat": []}},
                upsert=True
            )
        )
        
        # For each category in mongodb_data:
        for item in mongodb_data:
            catid = item["catid"]
            cname = item["cname"]
            scr   = item["scr"]
            new_img = {"pid": pid, "scr": scr}
            new_cat = {"catid": catid, "cname": cname, "imgs": [new_img]}

            # 2) If category doesn't exist at all, push it
            operations.append(
                UpdateOne(
                    {"did": did, "cat.catid": {"$ne": catid}},
                    {"$push": {"cat": new_cat}}
                )
            )
            
            # 3) If this pid already exists under that cat, just update its scr
            operations.append(
                UpdateOne(
                    {"did": did},
                    {
                    "$set": {
                        f"cat.$[c].imgs.$[i].scr": scr
                    }
                    },
                    array_filters=[
                    {"c.catid": catid},
                    {"i.pid": pid}
                    ]
                )
            )
            
            # 4) If pid is not in imgs yet, push it into the existing cat
            operations.append(
                UpdateOne(
                    {"did": did},                               # just match the document
                    {"$push": {"cat.$[c].imgs": new_img}},      # push into the c-th cat element
                    array_filters=[
                    {
                        "c.catid": catid,                      # match only the cat you want
                        "c.imgs.pid": {"$ne": pid}             # and only if that cat’s imgs doesn't have pid
                    }
                    ]
                )
            )
            
        print(did, pid, purl)
        print("Count of operations to be executed:", len(operations))
        
        try:
            imgrel_collection.bulk_write(operations, ordered=True)
            print(f"[✓] Bulk update successful for did={did}. Operations executed: {len(operations)}")
            return True, None
        except BulkWriteError:
            print(f"[✖] Bulk update failed for did={did}. Some operations may have failed.")
            return False, "BulkWriteError occurred"
        except Exception as e:
            print(f"[✖] Error during bulk update for did={did}: {e}")
            return False, str(e)
        return False, "Unknown error occurred"
