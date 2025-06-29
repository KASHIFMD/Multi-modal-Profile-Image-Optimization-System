
from datetime import datetime
import sys
import os
import json, pytz, requests
import traceback

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from rabbitmq import RabbitMQ
from helper import getConfigInfo
from classes.Image_relevance import ImageRelevance
from bson import Int64

def main():
    try:
        # gpu_ip = sys.argv[1]
        # port = sys.argv[2]
        # if gpu_ip == "" or port == "":
        #     print("No GPU IP or port passed")
        #     # exit(1)
        
        # gpu_url = f"http://{gpu_ip}:{port}"
        
        # gpu_health_url = f"{gpu_url}/health"
        # print(f"Requesting on URL {gpu_health_url}")
        # response = requests.get(gpu_health_url)
        
        # if response.status_code == 200:
        #     print("GPU working\n")
        # else:
        #     print("Wrong GPU IP entered or GPU is down")
        #     exit(1)
        
        subscribe_queue = 'image_relevance_process'
        
        # print(f"Vhost Passed {vhost}")
        
        rabbit_mq = RabbitMQ()
        img_relev = ImageRelevance()
        
        connectServer = getConfigInfo('rabbitmq_server1')
        # connectServer["host"] = vhost
        
        connection = rabbit_mq.createConnection(connectServer)
        channel = connection.channel()
        queue = channel.queue_declare(
            queue=subscribe_queue,
            passive=False,
            durable=True,
            exclusive=False,
            auto_delete=False
        )

        message_count   = queue.method.message_count
        print(message_count)
        
        def callback(ch, method, properties, body):
            try:
                queue_data = json.loads(body)
                
                rabbitmq_con = RabbitMQ()
                if "message" in queue_data:
                    print("Message Found")
                    msg = queue_data["message"]
                    if "product_url" in msg and "docid" in msg:
                        print(f"Valid Data Format {msg}")
                        # Start processing Data
                        docid = msg["docid"]
                        product_id = msg["product_id"]
                        product_url = msg["product_url"]
                        is_json = int(msg["is_json"]) if "is_json" in msg else 1 
                        prompt_name = msg["prompt_name"]
                        error_msg = msg["error_msg"]
                        
                        jdmart_id_found = False
                        company_details = img_relev.CompanyDetails(docid)
                        hot_cat_name = ""
                        hot_cat_id = 0
                        # print(company_details)
                        if str.upper(docid) in company_details:
                            comp_details = company_details[str.upper(docid)]
                            b2b_flag = int(comp_details["b2b_flag"])
                            
                            hot_cat_info = comp_details["hot_cat_info"]
                            # print(type(hot_cat_info))
                            # print(len(hot_cat_info))
                            # # exit(1)
                            if hot_cat_info != False and hot_cat_info != None and len(hot_cat_info) > 0:
                                hot_cat_name = hot_cat_info["name"]
                                hot_cat_id = hot_cat_info["nid"]
                                
                            
                            new_catidlineage = comp_details["new_catidlineage"]
                            # print(new_catidlineage["key"])
                            if new_catidlineage != False:
                                for v in new_catidlineage["val"]:
                                    if v[4] == hot_cat_id:
                                        jdmart_id_found = True
                                        jdmart_id = v[9]
                                        print(f"Hot cat matched and jdmart_id {jdmart_id}")
                                        break
                            
                            if b2b_flag == 1 and jdmart_id_found:
                                print(f"B2B Flag identified in company_details {b2b_flag}")
                                category_api_res = img_relev.FetchJdMartCatName(str(jdmart_id))
                                if "errorcode" in category_api_res and category_api_res["errorcode"] == 0:
                                    jdmart_res = category_api_res["results"]
                                    jdmart_catname = jdmart_res[0].get("jdmart_catname")
                                    print(f"JD Mart Cat name : {jdmart_catname}")
                                else:
                                    jdmart_id_found = False
                            else:
                                jdmart_id_found = False
                                print(f"Check hot category in company details {hot_cat_info}")
                                print(f"Hot Catname : '{hot_cat_name}' && Hot CatId : '{hot_cat_id}'")
                        else:
                            print(f"No Data Found from company API {company_details}")
                        
                        print(f"JD MART Identifed status {jdmart_id_found}")    
                        
                        if jdmart_id_found:
                            print(f"Hit Relevance API with jdmart_catname {jdmart_catname}")
                            post_cat_name = jdmart_catname
                        else:
                            print(f"Hit Relevance API with hot catname {hot_cat_name}")
                            post_cat_name = hot_cat_name
                            
                        print("############################################")
                        if post_cat_name == "" and prompt_name == "vision_json_cat":
                            prompt_name = "vision_json"
                        
                        request_data = {
                            "docid" : docid,
                            "product_id": product_id,
                            "product_url": product_url,
                            "is_json": is_json,
                            "prompt_name": prompt_name,
                            "cat_name": post_cat_name
                        }
                        hit_gpu = True
                        if prompt_name == "cat" and post_cat_name == "":
                            hit_gpu = False
                        
                        # output = image_relevance(RelevanceDataFormat, background_tasks=None)
                        print(f"Request DATA to GPU {request_data}")
                        print("############################################")
                        if hit_gpu:
                            gpu_res = img_relev.HitInternalRoute(request_data)
                            # print(type(gpu_res))
                            print(gpu_res)
                            # exit(1)
                            if "error_code" in gpu_res and gpu_res["error_code"] == 0:
                                print("##Success##")
                                print(gpu_res["output"])
                                gpu_output = gpu_res["output"]
                                img_rel_data = {}
                                
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
                                    "pid" : Int64(msg["product_id"]),
                                    "did" : str.lower(msg["docid"])
                                }
                                meta_collection_name = "tbl_catalogue_metadata"
                                # img_rel_val = {
                                #     "description" : "zrdxtgfchjbkn",
                                #     "alttag" : "tag value",
                                #     "tags" : ["1", "2", "3", "4", "5"]
                                # }
                                update_data = {
                                    "pid" : Int64(msg["product_id"]),
                                    "did" : str.lower(msg["docid"]),
                                    "purl" : msg["product_url"],
                                    "img_rel" : img_rel_data
                                }
                                push_data = {
                                    "img_rel.cat_match" : int(img_rel_data["cat_match"])
                                }
                                if error_msg == "success":
                                    mong_res = img_relev.UpdateMongoCollection(filter_qry, push_data, meta_collection_name)
                                else:
                                    mong_res = img_relev.UpdateMongoCollection(filter_qry, update_data, meta_collection_name)
                                
                                print(f"DOCID INSERTED as {str.lower(msg['docid'])} and Mongo Res : {mong_res}")
                                # Push to different queue
                                # desc = ""
                                print(f"############# {error_msg} ##########")
                                # if error_msg == "success":
                                # filter_qry_1 = {
                                #     "pid" : Int64(msg["product_id"]),
                                #     "did" : str.lower(msg["docid"])
                                # }
                                mongo_res = img_relev.FetchDataFromMongo(filter_qry, meta_collection_name)
                                print(f"Mongo Res : {mongo_res}")
                                img_description = mongo_res["img_rel"]["description"] if "img_rel" in mongo_res and "description" in mongo_res["img_rel"] else ""
                                img_alttag = mongo_res["img_rel"]["alttag"] if "img_rel" in mongo_res and "alttag" in mongo_res["img_rel"] else ""
                                # Hit gpu for promt_name
                                if img_description == "" and img_alttag == "":
                                    print("Reprocess data to generate full info")
                                    if post_cat_name == "":
                                        prompt_name_1 = "vision_json"
                                    else:
                                        prompt_name_1 = "vision_json_cat"
                                    request_data_1 = {
                                        "docid" : docid,
                                        "product_id": product_id,
                                        "product_url": product_url,
                                        "is_json": is_json,
                                        "prompt_name": prompt_name_1,
                                        "cat_name": post_cat_name
                                    }
                                    status, response = img_relev.ReprocessDataUsingGpu(request_data_1)
                                    if status:
                                        img_description = response
                                # else:
                                #     mongo_res = None
                                #     img_description = img_rel_data["description"] if "description" in img_rel_data else ""
                                    
                                category_data = {}
                                if new_catidlineage != False and len(new_catidlineage["val"]) > 0:
                                    for v in new_catidlineage["val"]:
                                        category_data[v[4]] = v[1]
                                
                                messagedata = {
                                    "docid" : str.lower(msg["docid"]),
                                    "product_id" : msg["product_id"],
                                    "product_url" : msg["product_url"],
                                    "categories" : category_data,
                                    "description" : img_description
                                }
                                
                                post_data = input_data = dict()
                                post_data["message"] = messagedata
                                post_data["queue_name"] = "image_relevance_score"
                                input_data["data"] = post_data
                                status, msg = img_relev.PushToQueue(input_data)
                                print(status)
                                
                                
                                print(f"Queue Data : {queue_data}")
                        else:
                            print(f"No need to call GPU : {hit_gpu}")    
                    else:
                        print(f"Invalid Data Format {msg}")
                        invalidData = {
                            "queue_name" : f"error.{subscribe_queue}",
                            **queue_data
                        }
                        response = rabbitmq_con.postQueue(invalidData)
                    
                else:
                    print("### NOT VALID FORMAT DATA ###")
                    errorData = {
                        "queue_name" : f"error.{subscribe_queue}",
                        **queue_data
                    }
                    response = rabbitmq_con.postQueue(errorData)

                current_date    = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
                print(current_date)
                
                ch.basic_ack(delivery_tag = method.delivery_tag)
                
            except json.JSONDecodeError:
                print("Failed to decode JSON message")
                traceback.print_exc()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            except Exception as e:
                print("Error processing message: ", str(e))
                traceback.print_exc()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            finally:
                print("Message processing complete")
                # channel.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        
        channel.basic_consume(
            queue=subscribe_queue, 
            on_message_callback=callback, 
            consumer_tag='Image_optimization'
        )
        
        print('[SUBSCRIBERS] [*] Waiting for messages. To exit press CTRL+C')
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()     

    except Exception as e:
        print("[SUBSCRIBERS] failed")
        print(f"ERROR : {str(e)}")
        print("Exiting...")
        exit(1)

if __name__ == "__main__":
    main()