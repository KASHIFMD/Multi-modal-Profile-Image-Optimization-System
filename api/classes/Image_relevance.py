import os, json, sys, requests
# from fastapi import JSONResponse
from helper import getConfigInfo, CurlGetRequest
from rabbitmq import RabbitMQ
import random
from bson import Int64
from pymongo import MongoClient # type: ignore
class ImageRelevance():
    def __init__(self):
        self.CompanyDetailsIp = "http://192.168.8.11:9001/web_services/CompanyDetails.php"
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
        
    def UpdateMongoCollection(self, filter_query, update_data, collection_name):
        MongoUser = getConfigInfo('mongo.username')
        MongoPass = getConfigInfo('mongo.password')
        MongoHost = getConfigInfo('mongo.url')
        MongoDTBS = getConfigInfo('mongo.db')
        
        MONGO_CONNECTION_STRING = f"mongodb://{MongoUser}:{MongoPass}@{MongoHost}/{MongoDTBS}"
        
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[MongoDTBS]
        collection = db[collection_name]

        result = collection.update_one(filter_query, {'$set': update_data}, upsert=True)
        # output = f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}"
        output =  {
            "matched" : result.matched_count,
            "modified" : result.modified_count,
            "upserted_id" : result.upserted_id
        }
        return output
    
    def UpdatePushMongoCollection(self, filter_query, update_data, collection_name):
        MongoUser = getConfigInfo('mongo.username')
        MongoPass = getConfigInfo('mongo.password')
        MongoHost = getConfigInfo('mongo.url')
        MongoDTBS = getConfigInfo('mongo.db')
        
        MONGO_CONNECTION_STRING = f"mongodb://{MongoUser}:{MongoPass}@{MongoHost}/{MongoDTBS}"
        
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[MongoDTBS]
        collection = db[collection_name]

        result = collection.update_one(filter_query, {'$push': update_data}, upsert=True)
        # output = f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}"
        output =  {
            "matched" : result.matched_count,
            "modified" : result.modified_count,
            "upserted_id" : result.upserted_id
        }
        return output
    
    def FetchDataFromMongo(self, filter_query, collection_name):
        MongoUser = getConfigInfo('mongo.username')
        MongoPass = getConfigInfo('mongo.password')
        MongoHost = getConfigInfo('mongo.url')
        MongoDTBS = getConfigInfo('mongo.db')
        MONGO_CONNECTION_STRING = f"mongodb://{MongoUser}:{MongoPass}@{MongoHost}/{MongoDTBS}"
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[MongoDTBS]
        collection = db[collection_name]
        result = collection.find_one(filter_query)
        return result if result else None
    
    def ReprocessDataUsingGpu(self, data):
        # print("#### ReprocessDataUsingGpu ####")
        # print(data)
        gpu_res = self.HitInternalRoute(data)
        # print(type(gpu_res))
        print(gpu_res)
        if "error_code" in gpu_res and gpu_res["error_code"] == 0:
            print("##Success##")
            print(gpu_res["output"])
            gpu_output = gpu_res["output"]
            img_rel_data = {}
            description_val = ""
            
            for k,v in gpu_output.items():
                if k == "alttag" or k == "description":
                    img_rel_data[k] = v
                elif k == "tags":
                    img_rel_data[k] = [x.strip() for x in v.split(',')]
                elif k == "cat_match":
                    img_rel_data[k] = int(v)
                else:
                    img_rel_data[k] = v
                                                    
                
            filter_qry = {
                "pid" : Int64(data["product_id"]),
                "did" : str.lower(data["docid"])
            }
            meta_collection_name = "tbl_catalogue_metadata"
            
            update_data = {
                "pid" : Int64(data["product_id"]),
                "did" : str.lower(data["docid"]),
                "purl" : data["product_url"],
                "img_rel" : img_rel_data
            }
            mong_res = self.UpdateMongoCollection(filter_qry, update_data, meta_collection_name)
            print(f"Mongo Update Response: {mong_res}")
            return True, img_rel_data["description"]
        else:
            print("##Error##")
            print(gpu_res)
            return False, "Error in GPU processing"
        
    
    def CompanyDetails(self, docid):
        url = f"{self.CompanyDetailsIp}?docid={docid}&case=content_service1"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)
    
    def FetchJdMartCatName(self, jdmart_id):
        url = "http://192.168.8.17:3000/services/category_data_api.php?city=mumbai&module=ME&return=jdmart_id,jdmart_catname&where={%22jdmart_id%22:%22"+jdmart_id+"%22}&scase=10&from=content_enhance"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)
    
    def HitInternalRoute(self, data):
        url = "http://192.168.40.172:5008/v1/img_relevance"
        
        # payload = json.dumps({
        #     "docid": "040pxx40.xx40.220120145025.j7d3",
        #     "product_id": "1234",
        #     "product_url": "https://images.jdmagicbox.com/v2/comp/hyderabad/d3/040pxx40.xx40.220120145025.j7d3/catalogue/pista-house-bakery-and-restaurant-uppal-hyderabad-restaurants-oq0tzidbzu.jpg",
        #     "is_json": 1,
        #     "prompt_name": "vision_json_cat",
        #     "cat_name": "restaurant"
        #     })
        payload = json.dumps(data)
        
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return json.loads(response.text)

