import boto3
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import os
import torch

import pickle
import argparse
import cv2
import glob
import os
import torchvision
import requests
import pandas as pd
import time
import math
from urllib.parse import urlparse
from tqdm import tqdm
import numpy as np
from utils.upload import UploadFile
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url
# from services.realesrgan import RealESRGANer
from services.realesrgan.utils import RealESRGANer
from services.realesrgan.archs.srvgg_arch import SRVGGNetCompact
from gfpgan import GFPGANer

class ModelHandler:
    def __init__(self, model_list: list):
        self.models = self.load_model(model_list)

    def set_memory_limit(self, gpu_memory_limit):
        gpu_id = 0  # Use the first GPU
        total_memory = torch.cuda.get_device_properties(gpu_id).total_memory

        # Limit the memory to gpu_memory_limit GB
        max_memory = gpu_memory_limit * 1024 * 1024 * 1024  # Convert GB to bytes
        torch.cuda.set_per_process_memory_fraction(max_memory / total_memory, device=gpu_id)
        print(f"[INFO] Restricted the process to use at most {gpu_memory_limit} GB of GPU memory.")

    def load_model(self, model_list: list):
        self.models = dict()
        for model_name in model_list:
            if model_name == 'RealESRGAN_x4plus':  # x4 RRDBNet model
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
            elif model_name == 'RealESRNet_x4plus':  # x4 RRDBNet model
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
            elif model_name == 'RealESRGAN_x4plus_anime_6B':  # x4 RRDBNet model with 6 blocks
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
            elif model_name == 'RealESRGAN_x2plus':  # x2 RRDBNet model
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
                netscale = 2
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
            elif model_name == 'realesr-animevideov3':  # x4 VGG-style model (XS size)
                model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
                netscale = 4
                file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
            elif model_name == 'realesr-general-x4v3':  # x4 VGG-style model (S size)
                model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
                netscale = 4
                file_url = [
                    'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
                    'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth'
                ]
            elif model_name == "GFPGANer":
                pass
            self.models[model_name] = {
                "model": model, 
                "netscale": netscale, 
                "file_url": file_url
            }

        model_path = os.path.join('weights', model_name + '.pth')
        # Check if model is downloaded or not
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            # ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for url in file_url:
                model_path = load_file_from_url(url=url, model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True)

        return self.models

    def download_image(self, url):
        """
        Download an image from the given URL and return it as a numpy array.
        """
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                image = np.array(image)
                return image
            else:
                raise Exception(f"Failed to download {url} — Status code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading image: {e}")
            raise Exception(f"Error downloading image: {e}")

    def get_image_info(self, image):
        try:
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            orientation = "Portrait" if height > width else "Landscape"

            image_info = {
                'width': width,
                'height': height,
                'channels': channels,
                'resolution': f"{width}x{height}",
                'orientation': orientation,
                'is_grayscale': channels == 1
            }
            return image_info, None
        except Exception as err:
            print(f"Error getting image info: {err}")
            return None, err
    
    def get_outscale(self, image):
        # Get image information
        image_info, err = self.get_image_info(image)
        if(image_info is None):
            message = "Image information could not be retrieved"
            return None, None, message, err, 500
        
        # Define bounding box dimensions
        if image_info['orientation'] == 'Landscape':
            max_width, max_height = 1280, 720
        else:
            max_width, max_height = 720, 1280

        original_width = image_info['width']
        original_height = image_info['height']

        # Calculate scale to fit inside bounding box while preserving aspect ratio
        scale = min(max_width / original_width, max_height / original_height)

        # Compute the new size maintaining aspect ratio
        resized_width = int(original_width * scale)
        resized_height = int(original_height * scale)
        target_res = (resized_width, resized_height)

        h_scale = target_res[1] / image_info['height']
        w_scale = target_res[0] / image_info['width']
        outscale = math.ceil(max(h_scale, w_scale) * 10) / 10

        if image_info['width'] >= target_res[0] and image_info['height'] >= target_res[1]:
            # flag = "Already HD"
            message = "Image already meets/exceeds 720p resolution"
            return None, None, message, None, 200
        message = f"Image is {image_info['orientation']} with resolution {image_info['resolution']}."
        return outscale, target_res, message, None, None

    def face_enhancer(self, image, upsampler, outscale, target_res):
        try:
            with torch.no_grad():
                face_enhancer = GFPGANer(
                    model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
                    upscale=outscale,
                    arch='clean',
                    channel_multiplier=2,
                    bg_upsampler=upsampler
                )
                _, _, output = face_enhancer.enhance(image, has_aligned=False, only_center_face=False, paste_back=True)

                interp = cv2.INTER_AREA if output.shape[0] > target_res[1] or output.shape[1] > target_res[0] else cv2.INTER_LANCZOS4
                output = cv2.resize(output, target_res, interpolation=interp)
                return output, None, None, 200
        except Exception as e:
            print(f"Error in face_enhancer: {e}")
            remark = f"Face enhancement failed: {str(e)}"
            print(f"[ERROR] {remark}")
            message = f"[ERROR] {remark}"
            return None, message, e, 500


    def text_enhancer(self, image, upsampler, outscale, target_res):
        try:
            with torch.no_grad():    
                output, _ = upsampler.enhance(image, outscale=outscale)

                interp = cv2.INTER_AREA if output.shape[0] > target_res[1] or output.shape[1] > target_res[0] else cv2.INTER_LANCZOS4
                output = cv2.resize(output, target_res, interpolation=interp)
                return output, None, None, 200
        except Exception as e:
            print(f"Error in text_enhancer: {e}")
            remark = f"Text enhancement failed: {str(e)}"
            print(f"[ERROR] {remark}")
            message = f"[ERROR] {remark}"
            return None, message, e, 500

    def image_enhancer(self, image, upsampler, outscale, target_res):
        try:
            with torch.no_grad():
                output, _ = upsampler.enhance(image, outscale=outscale)

                interp = cv2.INTER_AREA if output.shape[0] > target_res[1] or output.shape[1] > target_res[0] else cv2.INTER_LANCZOS4
                output = cv2.resize(output, target_res, interpolation=interp)
                print("Enhanced image output.shape: ", output.shape)
                return output, None, None, 200
        except Exception as e:
            print(f"Error in image_enhancer: {e}")
            remark = f"Image enhancement failed: {str(e)}"
            print(f"[ERROR] {remark}")
            message = f"[ERROR] {remark}"
            return None, message, e, 500

    def process(self, data):
        product_url = data.get("product_url")
        product_id = data.get("product_id")
        org_product_url = data.get("org_product_url")
        image_type = data.get("image_type")
        docid = data.get("docid")
        force = data.get("force", 0)

        # Download the image using url_ori first, falling back to url if needed
        if(force):
            try:
                image = self.download_image(org_product_url)
                print("Image downloaded successfully from org_product_url")
            except Exception as err:
                try:
                    print("Falling back to product_url for image download, err: ", err)
                    image = self.download_image(product_url)
                    print("Image downloaded successfully from product_url")
                        
                    # Object instantiation for uploading file to S3
                    upload_file = UploadFile()

                    upload_data = {
                        "docid": docid,
                        "product_id": product_id,
                        "product_url": product_url,
                        "image_type": "enhanced",
                        "SOURCE": image,
                        "DESTINATION": org_product_url,
                    }
                    _, message, err, status_code = upload_file.UploadImageFileToS3(upload_data, db_update=False, path = False)
                    if status_code != 200:
                        return None, message, err, status_code
                except Exception as e:
                    remark = f"Download Failed: {str(e)}"
                    print(f"[ERROR] {remark}")
                    message = f"[ERROR] {remark}"
                    return None, message, e, 404
        else:
            try:
                image = self.download_image(org_product_url)
                print("Image downloaded successfully from org_product_url")
            except Exception as err:
                remark = f"Download Failed from org_product_url: {str(err)}"
                print(f"[ERROR] {remark}")
                message = f"[ERROR] {remark}"
                return None, message, err, 404
            
        # Check if the image is grayscale
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            # Convert grayscale to RGB if necessary
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            print("Image is grayscale, converted to RGB")

        # Map image type to model name
        model_map = {
            "face": "GFPGANer",
            "text": "RealESRNet_x4plus",
            "general": "RealESRGAN_x4plus"
        }

        model_name = model_map.get(image_type, "RealESRGAN_x4plus")
        model_info = self.models.get(model_name)
        if not model_info:
            message = f"Model {model_name} not found in the model list"
            return None, message, None, 404
        
        model_path = os.path.join('weights', model_name + '.pth')
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            for url in model_info.get("file_url"):
                model_path = load_file_from_url(url=url, model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True)

        dni_weight = None
        denoise_strength = 0.5
        if model_name == 'realesr-general-x4v3':
            wdn_model_path = model_path.replace('realesr-general-x4v3', 'realesr-general-wdn-x4v3')
            model_path = [model_path, wdn_model_path]
            dni_weight = [denoise_strength, 1 - denoise_strength]
        
        outscale, target_res, message, err, status_code = self.get_outscale(image)
        print("outscale: ", outscale)
        print("target_res: ", target_res)
        if(outscale is None or target_res is None):
            return None, message, err, status_code

        tile = 0
        tile_pad = 10
        pre_pad = 0
        fp32 = False
        gpu_id = None
        upsampler = RealESRGANer(
            scale=model_info["netscale"],
            model_path=model_path,
            dni_weight=dni_weight,
            model=model_info.get("model"),
            tile=tile,
            tile_pad=tile_pad,
            pre_pad=pre_pad,
            half=not fp32,
            gpu_id=gpu_id
        )

        match model_name:
            case "GFPGANer":
                return self.face_enhancer(image, upsampler, outscale, target_res)
            case "RealESRNet_x4plus":
                return self.text_enhancer(image, upsampler, outscale, target_res)
            case "RealESRGAN_x4plus":
                return self.image_enhancer(image, upsampler, outscale, target_res)
            case _:
                return self.image_enhancer(image, upsampler, outscale, target_res)
        message = f"Model {model_name} not found in the model list"
        return None, message, None, 404

    def process2(self, model_handler, img_type, image):
        # img_mode = 'RGBA' if len(image.shape) == 3 and image.shape[2] == 4 else None

        # Map image type to model name
        model_map = {
            "face": "GFPGANer",
            "text": "RealESRNet_x4plus",
            "general": "RealESRGAN_x4plus"
        }

        model_name = model_map.get(img_type, "RealESRGAN_x4plus")
        model_info = self.models.get(model_name)
        if not model_info:
            return None
        
        model_path = os.path.join('weights', model_name + '.pth')
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            for url in model_info.get("file_url"):
                model_path = load_file_from_url(url=url, model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True)

        dni_weight = None
        denoise_strength = 0.5
        if model_name == 'realesr-general-x4v3':
            wdn_model_path = model_path.replace('realesr-general-x4v3', 'realesr-general-wdn-x4v3')
            model_path = [model_path, wdn_model_path]
            dni_weight = [denoise_strength, 1 - denoise_strength]
        
        outscale, target_res = self.get_outscale(image)
        
        tile = 0
        tile_pad = 10
        pre_pad = 0
        fp32 = False
        gpu_id = None
        upsampler = RealESRGANer(
            scale=model_info["netscale"],
            model_path=model_path,
            dni_weight=dni_weight,
            model=model_info.get("model"),
            tile=tile,
            tile_pad=tile_pad,
            pre_pad=pre_pad,
            half=not fp32,
            gpu_id=gpu_id
        )


        match model_name:
            case "GFPGANer":
                return self.face_enhancer(image, upsampler, outscale, target_res)
            case "RealESRNet_x4plus":
                return self.text_enhancer(image, upsampler, outscale, target_res)
            case "RealESRGAN_x4plus":
                return self.image_enhancer(image, upsampler, outscale, target_res)
            case _:
                return self.image_enhancer(image, upsampler, outscale, target_res)
        return None

