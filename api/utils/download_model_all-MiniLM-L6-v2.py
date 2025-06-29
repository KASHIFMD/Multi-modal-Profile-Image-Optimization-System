from sentence_transformers import SentenceTransformer

# Download the model and save it to the specified path
model_path = "/main_dir/app/models_pretrained/all-mpnet-base-v2"
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", cache_folder=model_path, local_files_only=False)

# Save the model to disk
embedding_model.save(model_path)
