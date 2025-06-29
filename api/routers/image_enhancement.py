from PIL import Image
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import requests
from io import BytesIO
import cv2
import numpy as np

router = APIRouter()

@router.post("/image_enhancement")
async def image_enhancement(request: Request):
    """
    Enhance the image based on type (face, text, general).
    """
    # Access model handler from app state
    model_handler = request.app.state.model_handler

    # Parse JSON body
    body = await request.json()

    # Set default image type if not provided
    img_type = body.get("img_type", "general").lower()

    # Image acquisition
    image = None

    if "product_url" in body:
        # If product_url is provided, do not return the image
        return JSONResponse({"status": "success", "message": "Product URL received, image not returned"})

    elif "url" in body:
        # If URL is provided, download the image using stream=True
        try:
            response = requests.get(body["url"], stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download image from URL")

            # Read the content and convert to a NumPy array
            image_data = np.asarray(bytearray(response.content), dtype=np.uint8)

            # Decode the image using OpenCV
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            if image is None:
                raise HTTPException(status_code=400, detail="Failed to decode the image from URL")

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error while downloading image: {str(e)}")

    if image is None:
        raise HTTPException(status_code=400, detail="No valid image input provided")

    # Predict using the model handler
    enhanced_image = model_handler.process2(model_handler, img_type, image)
    if enhanced_image is None:
        raise HTTPException(status_code=500, detail="Image enhancement failed")

    # Convert the NumPy array to a PIL Image (ensure proper color conversion)
    if isinstance(enhanced_image, np.ndarray):
        # Check if the image is already in RGB format
        if len(enhanced_image.shape) == 3 and enhanced_image.shape[2] == 3:
            # Convert BGR to RGB before creating a PIL image
            enhanced_image = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB)
        enhanced_image = Image.fromarray(enhanced_image)

    # Prepare the image for response
    img_byte_arr = BytesIO()
    enhanced_image.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    return StreamingResponse(img_byte_arr, media_type="image/jpeg")
