from datetime import datetime
import json
import pytz
import pika
import sys
import os
import time

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
print("parent:", parent)

from classes.ScoreSBERT import ModelHandlerSBERT

# RabbitMQ Config
RABBITMQ_HOST = '192.168.131.114'
RABBITMQ_VHOST = 'liv'
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'
RABBITMQ_QUEUE = 'image_relevance_score'
ERROR_QUEUE = 'image_relevance_score_error'

def is_valid_message(msg):
    return (
        isinstance(msg, dict) and
        isinstance(msg.get("docid"), str) and
        isinstance(msg.get("product_id"), int) and
        isinstance(msg.get("product_url"), str) and
        isinstance(msg.get("description"), str) and
        isinstance(msg.get("categories"), dict)
    )

def handle_rabbitmq_reconnection(channel, connection):
    """
    Handles reconnection to RabbitMQ in case of connection loss.
    """
    while True:
        try:
            connection.process_data_events()
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[!] RabbitMQ connection lost: {e}. Retrying...")
            time.sleep(5)

def main():
    try:
        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            virtual_host=RABBITMQ_VHOST,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare both queues (in case they don’t exist)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.queue_declare(queue=ERROR_QUEUE, durable=True)

        model = ModelHandlerSBERT(model_name = "all-mpnet-base-v2_allowed_words_15", finetuned=True)
        
        def callback(ch, method, properties, body):
            try:
                queue_message = json.loads(body)
                data = queue_message.get("message")
                print("[✔] Received Message:")
                print(json.dumps(data, indent=2), "\n This message will be processed now.")
                print("\n\nDOCID: ", data.get("docid", "No docid provided"))
                print("PRODUCT ID: ", data.get("product_id", "No product_id provided"))

                # Handle missing or empty categories
                if not data.get("categories"):
                    print("[✖] Missing or empty 'categories' field.")
                    queue_message["queue_name"] = ERROR_QUEUE
                    queue_message["err"] = "Missing or empty 'categories' field"
                    error_msg = json.dumps(queue_message)
                    channel.basic_publish(
                        exchange='',
                        routing_key=ERROR_QUEUE,
                        body=error_msg,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                data["product_id"] = int(data.get("product_id", 0))
                data["categories"] = {int(key): value for key, value in data["categories"].items()}

                if is_valid_message(data):
                    print("[✔] Valid message format.")
                    tfidf = True    
                    did = data.get("docid")
                    purl = data.get("product_url")
                    pid = data.get("product_id")
                    categories = data.get("categories", {})
                    start = time.time()
                    similarities, category_list = model.get_category_score_embeddings(model, data, tfidf)
                    similarities_1d_np = similarities.flatten().cpu().numpy() if similarities is not None else None
                    end = time.time()
                    print(f"🕒 Extracting embeddings: {end-start} seconds")
                    
                    if similarities is None or category_list is None:
                        queue_message["queue_name"] = ERROR_QUEUE
                        queue_message["err"] = "Failed to create embeddings"
                        error_msg = json.dumps(queue_message)
                        channel.basic_publish(
                            exchange='',
                            routing_key=ERROR_QUEUE,
                            body=error_msg,
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    mongodb_data = []
                    for ind, scr in enumerate(similarities_1d_np):
                        extracted_info = dict()
                        extracted_info["catid"] = category_list[ind]
                        extracted_info["cname"] = categories.get(category_list[ind])
                        extracted_info["scr"] = scr
                        mongodb_data.append(extracted_info)

                    # model.update_mongodb(mongodb_data, did, pid, purl)
                    # model.update_mongodb_pipeline(mongodb_data, did, pid, purl)
                    
                    start = time.time()
                    print("🕒 Updating MongoDB...")
                    update_status, error = model.update_mongodb_bulk(mongodb_data, did, pid, purl)
                    end = time.time()
                    print(f"🕒 MongoDB update completed in {end-start} seconds")
                    if(update_status):
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        print("[✖] MongoDB update failed:", error)
                        queue_message["queue_name"] = ERROR_QUEUE
                        queue_message["err"] = error
                        error_msg = json.dumps(queue_message)
                        channel.basic_publish(
                            exchange='',
                            routing_key=ERROR_QUEUE,
                            body=error_msg,
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    print("[✖] Invalid message format. Requeuing to error queue.")
                    queue_message["queue_name"] = ERROR_QUEUE
                    queue_message["err"] = "Invalid message format"
                    error_msg = json.dumps(queue_message)
                    channel.basic_publish(
                        exchange='',
                        routing_key=ERROR_QUEUE,
                        body=error_msg,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                print("🕒", datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S'))

            except Exception as e:
                print(f"[!] Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                handle_rabbitmq_reconnection(channel, connection)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
        print(f"[→] Waiting for messages on '{RABBITMQ_QUEUE}'... Press CTRL+C to exit.")
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\n[⛔] Interrupted. Closing connection.")
        try:
            channel.stop_consuming()
        except:
            pass
    except Exception as e:
        print(f"[✖] Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
