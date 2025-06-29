
from datetime import datetime
import sys
import os
import json, pytz
import traceback

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from rabbitmq import RabbitMQ
from helper import getConfigInfo
from classes.Image_enhace import ImageEnhacement

def main():
    try:
        
        subscribe_queue = 'image_enhance_update'
        
        rabbit_mq       = RabbitMQ()
        
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
                img_enhacement = ImageEnhacement()
                if "message" in queue_data:
                    print("Message Found")
                    msg = queue_data["message"]
                    if "product_url" in msg and "docid" in msg:
                        print(f"Valid Data Format {msg}")
                        # Start processing Data
                        if int(msg["purge"]) == 1:
                            print(f"Purging product_url {msg['product_url']}")
                            img_enhacement.PurgeImageUrl(msg['product_url'])
                            # purge image url
                        
                        if "action" in msg and msg["action"] == "update":
                            print(f"Passing product_id to queue to update mysql later")
                            post_data = input_data = dict()
                            post_data["message"] = msg
                            post_data["queue_name"] = "image_enhanced_products"
                            input_data["data"] = post_data
                            status, msg = img_enhacement.PushToQueue(input_data)
                            print(status)
                            # pass product_id to update in mysql table
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
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            except Exception as e:
                print("Error processing message: ", str(e))
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