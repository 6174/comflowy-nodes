import time  
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
from .types import STRING, INT, API_HOST
from .utils import logger, get_nested_value
from .api_key_manager import load_api_key

logger = logging.getLogger(__name__)

class FlowyUpscale:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
                "model": (["clarity-upscaler"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to upscale images using AI models.
- How to use: 
    - Provide an image to upscale.
    - Choose the scale factor and the upscaling model.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the upscaled image.
"""

    def upscale(self, image, scale_factor, model):
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting image upscale request. scale_factor: {scale_factor}, model: {model}")

        # Process input image
        if isinstance(image, torch.Tensor):
            if image.dim() == 4:
                image = image.squeeze(0)  # Remove batch dimension
            if image.shape[-1] == 3:
                image = (image.cpu().numpy() * 255).astype(np.uint8)
            elif image.shape[0] == 3:
                image = (image.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            else:
                raise ValueError(f"Unsupported image shape: {image.shape}")
        elif isinstance(image, np.ndarray):
            if image.ndim == 2:
                image = np.stack([image] * 3, axis=-1)
            elif image.shape[-1] == 1:
                image = np.repeat(image, 3, axis=-1)
            elif image.shape[-1] != 3:
                raise ValueError(f"Unsupported number of channels: {image.shape[-1]}")
            image = (image * 255).astype(np.uint8)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Convert input image to JPEG format and compress
        buffered = io.BytesIO()
        Image.fromarray(image).save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        try:
            # Build the URL for the API request
            response = requests.post(
                f"{API_HOST}/api/open/v0/upscale",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "image": f"data:image/jpeg;base64,{img_str}",
                    "scale_factor": scale_factor,
                    "model": model
                }
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"API request completed. Status code: {response.status_code}")
            logger.debug(f"API response content: {json.dumps(result, indent=2)}")

            if not result.get('success'):
                logger.error(f"API request failed. Response content: {json.dumps(result, indent=2)}")
                raise Exception(f"API request failed. Response content: {json.dumps(result, indent=2)}")

            output_url = result.get('data', {}).get('output', [None])[0]
            if not output_url:
                logger.error(f"Complete API response: {json.dumps(result, indent=2)}")
                raise Exception(f"Unable to get valid output image URL. API response does not have expected data structure. Complete response: {json.dumps(result, indent=2)}")

            logger.info(f"Obtained output URL: {output_url}")

            # Verify URL is accessible
            try:
                url_check = requests.head(output_url)
                url_check.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Unable to access output URL: {str(e)}")
                raise Exception(f"Unable to access output URL: {str(e)}")

            # Add delay, wait for Replicate to process
            time.sleep(10)

            img_response = requests.get(output_url, stream=True)
            img_response.raise_for_status()

            # Convert image data to PIL Image
            img = Image.open(img_response.raw)

            # Convert image data to numpy array
            img_np = np.array(img)

            # Ensure image is 3 channel RGB
            if len(img_np.shape) == 2:  # Grayscale image
                img_np = np.stack([img_np] * 3, axis=-1)
            elif img_np.shape[-1] == 4:  # RGBA image
                img_np = img_np[:, :, :3]

            # Convert to float32 and normalize to 0-1 range
            img_np = img_np.astype(np.float32) / 255.0

            # Convert to torch tensor, ensuring shape is [B,H,W,C]
            img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # Add batch dimension

            logger.info(f"Image processing completed. Output tensor shape: {img_tensor.shape}")
            logger.info(f"API request completed. Status code: {response.status_code}")
            logger.debug(f"API response content: {response.text}")

            return (img_tensor,)

        except Exception as e:
            error_msg = f"Error during image upscale: {str(e)}"
            logger.error(error_msg)
            logger.exception("Detailed error information:")
            # Return an error marked image, ensuring shape is [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
