# import json
# import os
# import sys
from fastapi import APIRouter, BackgroundTasks # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi import Request # type: ignore
from rabbitmq import RabbitMQ
from helper import getConfigInfo
from pydantic import BaseModel

router = APIRouter()

class MessageFormat(BaseModel):
    key: str
    message: dict
    queue_name: str
    credentials: dict

class QueueData(BaseModel):
    data: MessageFormat

@router.post("/push_to_queue")
async def push_to_queue(request: Request, background_tasks: BackgroundTasks):
    """
    Push data to RabbitMQ queue.
    """
    try:
        post_data = await request.json()
        queueData = dict()
        if "data" in post_data:
            if "key" in post_data["data"] and post_data["data"]["key"] != "":
                queueData["key"] = post_data["data"]["key"]
            if "message" in post_data["data"]:
                queueData["message"] = post_data["data"]["message"]
            else:
                return JSONResponse(status_code=500, content={"error_code": 1, "status": "ERROR", "message": "No message passed"})
            if "queue_name" in post_data["data"] and post_data["data"]["queue_name"] != "":
                queueData["queue_name"] = post_data["data"]["queue_name"]
            else:
                return JSONResponse(status_code=500, content={"error_code": 1, "status": "ERROR", "message": "No queue_name passed"})
            print(queueData)
        else:
            return JSONResponse(status_code=500, content={"error_code": 1, "status": "ERROR", "message": "Not valid format passed"})
        print("#### CALLING push_to_queue ####")
        rabbitmq = RabbitMQ()
        connectServer = getConfigInfo('rabbitmq_server1')
        queueData["credentials"] = connectServer
        response, push_msg = rabbitmq.postQueue(queueData)
        if response:
            return JSONResponse(status_code=200, content={"error_code": 0, "status": "SUCCESS", "message": push_msg})
        else:
            return JSONResponse(status_code=500, content={"error_code": 1, "status": "ERROR", "message": push_msg})
    except Exception as e:
        print(f"Error in push_to_queue: {e}")
        return JSONResponse(status_code=500, content={"error_code": 1, "status": "ERROR", "message": str(e)})
    
@router.post("/push_to_kafka")
async def push_to_kafka(request: QueueData):
    return request