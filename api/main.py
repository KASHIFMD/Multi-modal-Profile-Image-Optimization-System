import requests
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from routers.push_to_queue import router as push_to_queue_router
from routers.image_enhancement import router as image_enhancement_router
from routers.request_gpu import router as request_gpu_router
import argparse
import os

loadModel= True if os.environ["LOAD_MODEL"] == "True" else False
if loadModel:
    SERVER_IP = os.environ.get("SERVER_IP", "localhost")
    PROCESS = os.environ.get("PROCESS", "content_image_optimization")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = os.environ[f"{SERVER_IP}_{PROCESS}_environment_PYTORCH_CUDA_ALLOC_CONF"]
    
    from classes.RealESR import ModelHandler
    model_handler = None

    # Define the lifespan context manager
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup logic (runs before the app starts serving requests)
        print("Starting up: initialize resources here")
        global model_handler
        # These models are used for image enhancement for current development
        model_list = ['RealESRNet_x4plus', 'RealESRGAN_x4plus', 'GFPGANer']
        model_handler = ModelHandler(model_list)

        # Set memory limit for each process (in GB)
        gpu_limit = int(os.getenv(f"{SERVER_IP}_{PROCESS}_gpu_limit", "4"))
        model_handler.set_memory_limit(gpu_limit)

        app.state.model_handler = model_handler
        print("Model handler initialized successfully.")

        yield  # Yield control while the application is running

        # Shutdown logic (runs after the app finishes serving requests)
        print("Shutting down: clean up resources here")
        # Properly release resources held by the model handler
        try:
            if hasattr(model_handler, 'release'):
                model_handler.release()
            elif hasattr(model_handler, 'close'):
                model_handler.close()
            elif hasattr(model_handler, 'cleanup'):
                model_handler.cleanup()
            else:
                del model_handler
            print("Model handler resources released successfully.")
        except Exception as e:
            print(f"Error during resource cleanup: {e}")
    
    app = FastAPI(lifespan=lifespan, title="Image Relevance", description="API to get or set image relevance data", version="1.0.0")
else:
    app = FastAPI(title="Content Image Optimization", description="API to get or set image relevance or enhancement data", version="1.0.0")

@app.get("/")
def hello():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    """
    Health check endpoint
    """
    health_check = {
        "status": "ok",
        "version": "1.0.0",
        "description": "API is running"
    }
    return health_check

@app.get("/get_relevance/{docid}")
def get_relevance(docid: str):
    print(f"Received request for relevance of docid: {docid}")
    return {"docid": docid, "relevance": 0.85}


@app.get("/set_relevance/{docid}/{relevance}")
def set_relevance(docid: str, relevance: float):
    print(f"Setting relevance for docid: {docid} to {relevance}")
    # Simulate setting relevance
    return {"error": 0, "docid": docid, "relevance": relevance}

@app.get("/company_details/{docid}")
def company_details(docid: str):
    """
    Get company details by docid
    """
    COMPANY_DETAILS_API = "http://192.168.8.11:9001/web_services/CompanyDetails.php?case=content_service&docid="
    comp = COMPANY_DETAILS_API + docid
    comp_res = requests.get(comp)
    comp_json = comp_res.json()
    if comp_res.status_code != 200:
        return {"error": "Company not found"}
    # Simulate a successful response
    company_data = {
        docid.upper(): comp_json[docid.upper()]
    }
    return company_data

# Include the router for push_to_queue
app.include_router(push_to_queue_router, prefix="/v1", tags=["push_to_queue"])
app.include_router(image_enhancement_router, prefix="/v1", tags=["image_enhancement"])  # Include the img router
app.include_router(request_gpu_router, tags=["Request GPU server api"])  # Include the request_gpu router

if __name__ == "__main__":
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    SERVER_IP = os.environ.get("SERVER_IP", "localhost")
    PROCESS = os.environ.get("PROCESS", "content_image_optimization")
    print("SERVER_IP: ", SERVER_IP)
    print("PROCESS: ", PROCESS)
    
    # Load the worker configuration
    port = int(os.environ[f"{SERVER_IP}_{PROCESS}_port"])
    workers = int(os.environ.get(f"{SERVER_IP}_{PROCESS}_workers", 1))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)
