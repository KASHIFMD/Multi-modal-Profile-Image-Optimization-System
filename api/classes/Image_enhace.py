import os, json, sys, requests
# from fastapi import JSONResponse

from helper import getConfigInfo, CurlGetRequest
from rabbitmq import RabbitMQ
class ImageEnhacement():
    def __init__(self):
        pass
    
    def PurgeImageUrl(self, img_url):    
        akamai_purge_url = getConfigInfo('AKAMAI_PURGE.URL')
                
        print(akamai_purge_url)
        resposne = CurlGetRequest(f"{akamai_purge_url}{img_url}")
        print(f"Response: {resposne}")
        
    def PushToQueue(self, post_data):
        queueData = dict()
        if "data" in post_data:
            if "key" in post_data["data"] and post_data["data"]["key"] != "":
                queueData["key"] = post_data["data"]["key"]
            if "message" in post_data["data"]:
                queueData["message"] = post_data["data"]["message"]
            else:
                return False, "message missing"
            if "queue_name" in post_data["data"] and post_data["data"]["queue_name"] != "":
                queueData["queue_name"] = post_data["data"]["queue_name"]
            else:
                return False, "queue_name missing"
            print(queueData)
        else:
            return False, "data missing"
        print("#### CALLING push_to_queue ####")
        rabbitmq = RabbitMQ()
        connectServer = getConfigInfo('rabbitmq_server1')
        queueData["credentials"] = connectServer
        response, push_msg = rabbitmq.postQueue(queueData)
        return response, push_msg

    def RequestEnhance(self, gpu_url, post_data):
        url = f"{gpu_url}/v1/img_enhance"

        # payload = json.dumps({
        #     "docid": "011p1230168198p9a4v7",
        #     "product_id": "123",
        #     "product_url": "https://images.jdmagicbox.com/delhi/v7/011p1230168198p9a4v7/catalogue/insculp-salon-rani-bagh-delhi-7.jpg",
        #     "org_product_url": "https://images.jdmagicbox.com/delhi/v7/011p1230168198p9a4v7/catalogue/insculp-salon-rani-bagh-delhi-7-w.jpg",
        #     "image_type": "general"
        # })
        payload = json.dumps(post_data)
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # print(response.text)
        return response.text
