import csv
import os
import sys
import json

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import traceback
from datetime import datetime
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
from utils.upload import UploadFile
from urllib.parse import urlparse
from helper import getConfigInfo, CurlGetRequest

def process_csv(file_path: str):
    """
    Process the CSV file and return the data as a list of dictionaries.
    Each dictionary represents a row in the CSV file.
    """
    data = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        raise
    return data


def main():
    try:
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
        else:
            print("No file path found")
            exit(1)

        # Process the CSV file
        data = process_csv(file_path)
        print(f"Processed {len(data)} rows from {file_path}")

        count = 0
        remarks_list = []
        upload_file = UploadFile()
        # Iterate through the data and perform operations
        for row in data:
            docid = row.get('docid')
            product_id = row.get('product_id')
            product_url = row.get('product_url')
            time_taken = row.get('time_taken')
            remark = row.get('remark')
            flag = row.get('flag')
            remark_substr = remark[0:17]
            remarks_list.append(remark_substr)
            enhanced_img_path = row.get('enhanced_img_path')
            # Extract destination path from product_url
            parsed_url = urlparse(product_url)
            # print(parsed_url)
            # print("\n")
            if remark == "Processed Successfully":
                count += 1
                # print(f"Parsed URL: {parsed_url.path}")
                destination_path = parsed_url.path.replace("/v2/comp/", "/comp/")
                # print(f"URL : {product_url} && Remark : {remark} && New path : {enhanced_img_path}\n")
                generated_img_path = enhanced_img_path.replace("/workspace/output_images/", "/home/ubuntu/kashif/image_enhancement/Real-ESRGAN/output_images/")
                
                # print(f"\nGenerated image path: {generated_img_path}")
            
                upload_data = {
                    "docid": docid,
                    "product_id": product_id,
                    "product_url": product_url,
                    # "org_product_url": product_url,
                    "image_type": "enhanced",
                    "SOURCE": generated_img_path,
                    "DESTINATION": destination_path[1:],
                }
                # print(f"\nUpload data: {upload_data}")
                update_db = False
                upload_res, res_url = upload_file.UploadImageFileToS3(upload_data, update_db)
                
                print(f"Upload response: {upload_res}")
                
                # img_url = f"https://images.jdmagicbox.com{destination_path}"
                # img_url_v2 = f"https://images.jdmagicbox.com/v2{destination_path}"
                
                # akamai_purge_url = getConfigInfo('AKAMAI_PURGE.URL')
                
                # print(akamai_purge_url)
                # img_upd_res = False
                # curl get request
                if upload_res:
                    print(f"{count}. Image URL: {res_url}")
                    # resposne = CurlGetRequest(akamai_purge_url+img_url)
                    # print(f"Response: {resposne}")
                    # resposne_v2 = CurlGetRequest(akamai_purge_url+img_url_v2)
                    # print(f"Response: {resposne_v2}")
                else:
                    print(f"Image upload failed for {docid} with remark: {remark}")
                    # img_upd_res = False
                
                # if count > 10:
                #     break
        unique_remarks = set(remarks_list)
        print(f"\nUnique remarks: {unique_remarks}")
        
        print(f"Total rows processed: {len(data)}")
        print(f"Total rows with 'Processed Successfully': {count}")
            

    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
        exit(1)
    finally:
        # Cleanup code if needed
        print("Cleanup code executed")
        # For example, close any open files or connections
        # if file:
        #     file.close()
        pass

if __name__ == "__main__":
    main()