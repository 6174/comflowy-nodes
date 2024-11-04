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

class FlowyClarityUpscale:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": ([2, 4, 6, 8], {"default": 2}),
                "dynamic": ("FLOAT", {"default": 6.0, "min": 1.0, "max": 50.0, "step": 0.1}),
                "creativity": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.01}),
                "resemblance": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 3.0, "step": 0.01}),
                "tiling_width": ([16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256], {"default": 112}),
                "tiling_height": ([16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256], {"default": 144}),
                "num_inference_steps": ("INT", {"default": 18, "min": 1, "max": 100}),
                "seed": ("INT", {"default": 1337, "min": 0, "max": 2147483647}),
                "handfix": (["disabled", "hands_only", "image_and_hands"], {"default": "disabled"}),
                "pattern": ("BOOLEAN", {"default": False}),
                "sharpen": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "downscaling": ("BOOLEAN", {"default": False}),
                "downscaling_resolution": ("INT", {"default": 768, "min": 256, "max": 2048}),
                "sd_model": (["epicrealism_naturalSinRC1VAE.safetensors [84d76a0328]", 
                            "juggernaut_reborn.safetensors [338b85bc4f]",
                            "flat2DAnimerge_v45Sharp.safetensors"], {"default": "juggernaut_reborn.safetensors [338b85bc4f]"}),
                "scheduler": (["DPM++ 2M Karras", "DPM++ SDE Karras", "DPM++ 2M SDE Exponential", 
                             "DPM++ 2M SDE Karras", "Euler a", "Euler", "LMS", "Heun", "DPM2", 
                             "DPM2 a", "DPM++ 2S a", "DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", 
                             "DPM++ 2M SDE Heun", "DPM++ 2M SDE Heun Karras", 
                             "DPM++ 2M SDE Heun Exponential", "DPM++ 3M SDE", 
                             "DPM++ 3M SDE Karras", "DPM++ 3M SDE Exponential", 
                             "DPM fast", "DPM adaptive", "LMS Karras", "DPM2 Karras", 
                             "DPM2 a Karras", "DPM++ 2S a Karras", "Restart", "DDIM", 
                             "PLMS", "UniPC"], {"default": "DPM++ 3M SDE Karras"}),
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

    def upscale(self, image, scale_factor, dynamic, creativity, resemblance, tiling_width, tiling_height, num_inference_steps, seed,handfix=None, pattern=False, sharpen=0, downscaling=False,downscaling_resolution=768, sd_model=None, scheduler=None):
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting image upscale request. scale_factor: {scale_factor}")

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
            # Build URL for API request using API_HOST
            response = requests.post(
                f"{API_HOST}/api/open/v0/flowy",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "image": f"data:image/jpeg;base64,{img_str}",
                    "scale_factor": scale_factor,
                    "dynamic": dynamic,
                    "creativity": creativity,
                    "resemblance": resemblance,
                    "tiling_width": tiling_width,
                    "tiling_height": tiling_height,
                    "num_inference_steps": num_inference_steps,
                    "seed": seed,
                    "handfix": handfix,
                    "pattern": pattern,
                    "sharpen": sharpen,
                    "downscaling": downscaling,
                    "downscaling_resolution": downscaling_resolution,
                    "sd_model": sd_model,
                    "scheduler": scheduler,
                    "model_type": "clarityupscaler",
                }
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"API request completed. Status code: {response.status_code}")
            logger.debug(f"API response content: {json.dumps(result, indent=2)}")

            if not result.get('success'):
                logger.error(f"API request failed. Response content: {json.dumps(result, indent=2)}")
                raise Exception(f"API request failed. Response content: {json.dumps(result, indent=2)}")

            output_url = result.get('data', {}).get('output')
            if not output_url or not isinstance(output_url, str):
                logger.error(f"Complete API response: {json.dumps(result, indent=2)}")
                raise Exception(f"Unable to get valid output image URL. API response doesn't have expected data structure. Complete response: {json.dumps(result, indent=2)}")

            logger.info(f"Received output URL: {output_url}")

            # Verify if URL is accessible
            try:
                url_check = requests.head(output_url)
                url_check.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Cannot access output URL: {str(e)}")
                raise Exception(f"Cannot access output URL: {str(e)}")

            # Add delay to wait for Replicate processing
            time.sleep(10)

            img_response = requests.get(output_url, stream=True)
            img_response.raise_for_status()

            # Convert image data to PIL Image
            img = Image.open(img_response.raw)

            # Convert to numpy array
            img_np = np.array(img)

            # Ensure image has 3 RGB channels
            if len(img_np.shape) == 2:  # Grayscale image
                img_np = np.stack([img_np] * 3, axis=-1)
            elif img_np.shape[-1] == 4:  # RGBA image
                img_np = img_np[:, :, :3]

            # Convert to float32 and normalize to 0-1 range
            img_np = img_np.astype(np.float32) / 255.0

            # Convert to torch tensor, ensure shape is [B,H,W,C]
            img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # Add batch dimension

            logger.info(f"Image processing completed. Output tensor shape: {img_tensor.shape}")
            logger.info(f"API request completed. Status code: {response.status_code}")
            logger.debug(f"API response content: {response.text}")

            return (img_tensor,)

        except Exception as e:
            error_msg = f"Error during upscaling: {str(e)}"
            logger.error(error_msg)
            logger.exception("Detailed error information:")
            # Return an error marker image, ensure shape is [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
