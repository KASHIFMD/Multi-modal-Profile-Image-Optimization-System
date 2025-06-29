from fastapi import APIRouter, BackgroundTasks # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi import Request # type: ignore
from rabbitmq import RabbitMQ
from helper import getConfigInfo
from pydantic import BaseModel
from typing import Optional
import cv2
import numpy as np
from utils.upload import UploadFile
from prompts import prompts
from jinja2 import Template
import os
import json
import requests
import random

# Used to keep track of last used GPU for round-robin (can also be persisted to Redis or file)
ROUND_ROBIN_INDEX_KEY = "ROUND_ROBIN_INDEX"

router = APIRouter(prefix="/v1")

class EnhanceDataFormat(BaseModel):
    docid: str
    product_id: str
    product_url: str
    org_product_url: str
    image_type: str
    force: Optional[int] = 0  # ✅ Default is False, indicating no force enhancement
    
class RelevanceDataFormat(BaseModel):
    docid: str
    product_id: str
    product_url: str
    prompt: Optional[str] = None  # ✅ Default is None
    prompt_name: Optional[str] = None  # ✅ Default is None
    cat_name: Optional[str] = None  # ✅ Default is None
    is_json: Optional[int] = 0  # ✅ Default is False, indicating no JSON response
        
def get_prompt(prompt_name, prompt=None, cat_name=None):
    if (prompt_name is None or prompt_name == "") and (prompt is not None and prompt != ""):
        filled_prompt = prompt
    elif prompt_name in ["vision_json", "description"]:
        filled_prompt = prompts.get(prompt_name)
    elif prompt_name in ["vision_json_cat", "cat"]:
        if not cat_name:
            return JSONResponse(status_code=400, content={"error_code": 1, "message": "Category name is required for vision_json_cat"})
        template = Template(prompts.get(prompt_name))
        filled_prompt = template.render(category_name=cat_name)
    elif cat_name and cat_name != "":
        template = Template(prompts.get("full_details_cat"))
        filled_prompt = template.render(category_name=cat_name)
    else:
        template = Template(prompts.get("full_details"))
        filled_prompt = template.render()
    return filled_prompt

def getConfigInfo():
    process = "image_relevancy"
    gpu_ips = ["103.42.50.120", "103.42.50.106"]
    gpu_candidates = []
    for gpu_ip in gpu_ips:
        try:
            workers = int(os.environ[f"{gpu_ip}_{process}_workers"])
            if workers > 0:
                port = os.environ[f"{gpu_ip}_{process}_port"]
                gpu_candidates.append((gpu_ip, port, workers))
        except (KeyError, ValueError) as e:
            print(f"Skipping {gpu_ip} due to error: {e}")
            continue

    if not gpu_candidates:
        print("No GPUs with available workers.")
        return

    # Extract workers
    worker_counts = [w for (_, _, w) in gpu_candidates]
    if len(set(worker_counts)) == 1:
        # All weights are same — use round robin
        index = int(os.environ.get(ROUND_ROBIN_INDEX_KEY, 0)) % len(gpu_candidates)
        os.environ[ROUND_ROBIN_INDEX_KEY] = str((index + 1) % len(gpu_candidates))  # update index
        selected_ip, selected_port, _ = gpu_candidates[index]
        print(f"Round-robin selected GPU: {selected_ip}")
    else:
        # Weighted random selection
        total = sum(worker_counts)
        probabilities = [w / total for w in worker_counts]
        selected_ip, selected_port, _ = random.choices(gpu_candidates, weights=probabilities, k=1)[0]
        print(f"Weighted random selected GPU: {selected_ip}")
    return selected_ip, selected_port

 
@router.post("/img_enhance")
def image_enhancement(request: Request, data: EnhanceDataFormat, background_tasks: BackgroundTasks):
    """
    Received request to enhance image using GPU
    """
    loadModel = True if os.environ["LOAD_MODEL"] == "True" else False
    if loadModel:
        try:
            # Extract data from the request
            docid = data.docid
            product_id = data.product_id
            product_url = data.product_url
            org_product_url = data.org_product_url
            image_type = data.image_type
            force = data.force

            # Create a dictionary to hold the data
            data = {
                "docid": docid,
                "product_id": product_id,
                "product_url": product_url,
                "org_product_url": org_product_url,
                "image_type": image_type,
                "force": force
            }
            print(f"Data received: {data}")
            
            if not all([docid, product_id, product_url, org_product_url, image_type]):
                return JSONResponse(status_code=400, content={"error_code": 1, "message": "Invalid request data"})
            # Check if the image type is valid
            
            # New function to handle the image optimization request -- start
            # Access model handler from app state
            model_handler = request.app.state.model_handler

            try:
                # Get the enhanced image using the model handler
                enhanced_image, message, err, status_code = model_handler.process(data)
                if enhanced_image is None:
                    return JSONResponse(status_code=status_code, content = {"error_code": 1, "err": str(err), "message":message})
                
                # Object instantiation for uploading file to S3
                upload_file = UploadFile()

                upload_data = {
                    "docid": docid,
                    "product_id": product_id,
                    "product_url": product_url,
                    "image_type": "enhanced",
                    "SOURCE": enhanced_image,
                    "DESTINATION": product_url,
                }
                _, message, err, status_code = upload_file.UploadImageFileToS3(upload_data, db_update=False, path = False)
            except Exception as err:
                return JSONResponse(status_code=500, content = {"error_code": 1, "err": err, "message": "Error in processing image enhancement"})

            # End of new function to handle the image optimization request
            return JSONResponse(status_code=status_code, content={"error_code": 0, "err": err, "message": "Image optimization request processed successfully"})
        except Exception as err:
            return JSONResponse(status_code=500, content={"error_code": 1, "err": err, "message": "Error in processing image enhancement"})
    else:
        return JSONResponse(status_code=501, content={"error_code": 1, "message": "Not Implemented: API disabled on CPU server, not loading model"})

@router.post("/img_relevance")
def image_relevance(request: RelevanceDataFormat, background_tasks: BackgroundTasks):
    """
    Received request to generate image relevance data using GPU
    """
    try:
        # Extract data from the request
        docid = request.docid
        product_id = request.product_id
        product_url = request.product_url
        prompt = request.prompt
        prompt_name = request.prompt_name
        cat_name = request.cat_name
        is_json = request.is_json
        # Create a dictionary to hold the data
        data = {
            "docid": docid,
            "product_id": product_id,
            "product_url": product_url,
            "prompt": prompt,
            "prompt_name": prompt_name,
            "cat_name": cat_name,
            "is_json": is_json
        }
        print(f"Data received: {data}")
        # Check if the request is valid
        if not all([docid, product_id, product_url]):
            return JSONResponse(status_code=400, content={"error_code": 1, "message": "Invalid request data"})
        
        # New function to handle the image enhancement request -- start  
        filled_prompt = get_prompt(prompt_name, prompt, cat_name)
        selected_ip, selected_port = getConfigInfo()
        
        uri = f"http://{selected_ip}:{selected_port}/v1/infer"
        data = {
            "image_url": product_url,
            "prompt": filled_prompt,
            "is_json": is_json
        }
        payload = json.dumps(data)
        print("payload:", payload)
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(uri, headers=headers, data=payload)
        if(is_json == 1):
            try:
                status_code = response.status_code
                response_json = response.json()
                response_json["output"] = json.loads(response_json["output"])
            except ValueError:
                # If response is not JSON, return raw text
                print("response_json: ", response_json)
                return JSONResponse(status_code=500, content={"error_code": 1, "message": str("Invalid JSON returned from GPU server")})
            response = response_json
        else:
            status_code = response.status_code
            response = json.loads(response.text)
        # End of new function to handle the image enhancement request
        return JSONResponse(status_code=status_code, content=response)
        
    except Exception as e:
        print(f"Error in img_enhance: {e}")
        return JSONResponse(status_code=500, content={"error_code": 1, "message": str(e)})
