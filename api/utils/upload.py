import boto3
# import magic
import os
from os.path import join
# from classes.dbconnection import DbConnection
from botocore.exceptions import ClientError
from helper import RemoveFile
# import threading
from PIL import Image
from helper import getConfigInfo
import numpy as np
import cv2
from io import BytesIO
from urllib.parse import urlparse

AWS_ACCESS_KEY = getConfigInfo('aws-s3-mum.access_key_id')
AWS_SECRET_KEY = getConfigInfo('aws-s3-mum.secret_access_key')
S3_BUCKET_NAME = getConfigInfo('aws-s3-mum.bucket')
S3_REGION      = getConfigInfo('aws-s3-mum.region')
S3_DOMAIN      = getConfigInfo('aws-s3-mum.domain')

class UploadFile():
    def __init__(self):
        pass

    def UploadImageFileToS3(self, post_data, db_update=False, path=True):
        """
        Upload a single file to S3
        """
        try:
            # print(post_data)
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=S3_REGION
            )
            dest_image = post_data["DESTINATION"]

            if(path):
                source_image = post_data['SOURCE']
                if not os.path.isfile(source_image):
                    print(f"Error: IMAGE File {source_image} does not exist")
                    message = f"Error: IMAGE File {source_image} does not exist"
                    return False, message, None, 404
                
                
                print("################")
                print(source_image)
                print(dest_image)
                print("################")
                
                # mime = magic.Magic(mime=True)
                # mime_type_val = mime.from_file(source_image)
                # print(mime_type_val)
                # if mime_type_val!="image/jpeg":
                #     img = Image.open(source_image)
                #     rgb_im = img.convert('RGB')
                #     rgb_im.save(dest_image)
                
                post_data['dest_img_key'] = dest_image
                print(f"\n####Uploading {source_image} to s3://{S3_DOMAIN}/{post_data['dest_img_key']}")
                
                s3_client.upload_file(
                    source_image,
                    S3_BUCKET_NAME,
                    post_data['dest_img_key'],
                    ExtraArgs={
                        'ContentType': 'image/jpeg',  # Explicitly set for JPEG
                        'ACL': 'public-read'          # Make it publicly accessible
                    }
                )
                dest_image_url = os.path.join("https://images.jdmagicbox.com/",dest_image)
            else:
                # If path is False, we expect SOURCE to be a numpy array and DESTINATION to be a URL             
                source_image = post_data['SOURCE']  # numpy array
                if not isinstance(source_image, np.ndarray):
                    print("Error: SOURCE must be a numpy array when path is False")
                    message = "Error: SOURCE must be a numpy array when path is False"
                    return False, message, None, 500
                
                # Ensure the image is in BGR format for JPEG
                if source_image.shape[2] == 3:
                    source_image = cv2.cvtColor(source_image, cv2.COLOR_RGB2BGR)

                parsed_url = urlparse(dest_image)
                print("Converting numpy array to JPEG bytes")
                a, buffer = cv2.imencode('.jpg', source_image)
                image_bytes = BytesIO(buffer.tobytes())
                image_bytes.seek(0)  # Move to the start of the BytesIO stream
                
                content_type = 'image/jpeg'

                upload_path = parsed_url.path[1:]
                upload_path = upload_path.replace("v2/comp/","comp/")
                post_data['dest_img_key'] = upload_path
                
                # Upload the image to S3
                # with image_bytes:
                s3_client.upload_fileobj(
                    image_bytes,
                    S3_BUCKET_NAME,
                    post_data['dest_img_key'],
                    ExtraArgs={
                        'ContentType': content_type,  # Explicitly set for JPEG
                        'ACL': 'public-read'          # Make it publicly accessible
                    }
                )
                dest_image_url = dest_image
            
            # if db_update:
                # db_connection = DbConnection()
                # dbconn = db_connection.db_connect_live()
                
                # sql = """
                # UPDATE tbl_video_process_log SET 
                #     thumb_url = %s
                # WHERE ref_id = %s
                # """
                # values = (
                #     dest_image_url,
                #     post_data["random_key"]
                # )
                # upd_dbcursor = dbconn.cursor()
                # upd_dbcursor.execute(sql, values)
                # dbconn.commit()
                # upd_dbcursor.close()
            print("IMAGE uploaded successfully", post_data['dest_img_key'])
            message = "IMAGE uploaded successfully"
            # Remove image file from local
            # RemoveFile(source_image)
            return True, message, None, 201
        except ClientError as err:
            print(f"Error client uploading {post_data['SOURCE']}: {str(err)}")
            message = "Error client"
            return False, message, err, 500
        except Exception as err:
            print(f"Error uploading {post_data['SOURCE']}: {str(err)}")
            message = "Error uploading image to S3"
            return False, message, err, 500
        # finally:
        #     # Close the S3 client
        #     s3_client.close()
        #     print("S3 client closed")
