import time
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
from .types import STRING, INT, SAFETY_TOLERANCE, BOOLEAN, get_api_host
from .api_key_manager import load_api_key

logger = logging.getLogger(__name__)

class FlowyFlux:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "version": (["flux-1.1-pro", "flux-pro"],),
                "aspect_ratio": ([
                    "custom",
                    "1:1",
                    "16:9",
                    "2:3",
                    "3:2",
                    "4:5",
                    "5:4",
                    "9:16",
                    "3:4",
                    "4:3"
                ],),
                "height": ("INT", {"default": 256, "min": 256, "max": 1440}),
                "width": ("INT", {"default": 256, "min": 256, "max": 1440}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}), 
                "prompt_upsampling": BOOLEAN,
                "safety_tolerance": (SAFETY_TOLERANCE,),
                "output_quality": ("INT", {"default": 80, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate images using Flux AI.
- How to use: 
    - Provide a prompt to generate an image.
    - Choose version, aspect ratio, height, width, and seed.
    - Height and width are only used when aspect_ratio=custom. Must be a multiple of 32 (if it's not, it will be rounded to nearest multiple of 32). 
    - Prompt Upsampling: Automatically modify the prompt for more creative generation.
    - Safety tolerance, 1 is most strict and 5 is most permissive.
    - Quality when saving the output images, from 0 to 100. 100 is best quality, 0 is lowest quality. Not relevant for .png outputs.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated image.
"""

    def generate(self, prompt, version, aspect_ratio, height, width, seed, prompt_upsampling, safety_tolerance, output_quality):
        api_key = load_api_key()
        API_HOST = get_api_host()
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting Flux image generation request. prompt: {prompt}, version: {version}, aspect_ratio: {aspect_ratio}, height: {height}, width: {width}, seed: {seed}, prompt_upsampling: {prompt_upsampling}, safety_tolerance: {safety_tolerance}, output_quality: {output_quality}")

        try:
            response = requests.post(
                f"{API_HOST}/api/open/v0/flowy",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "version": version, 
                    "aspect_ratio": aspect_ratio,
                    "height": height,
                    "width": width,
                    "seed": seed,
                    "prompt_upsampling": prompt_upsampling,
                    "safety_tolerance": safety_tolerance,
                    "output_quality": output_quality,
                    "model_type": "flux",
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

            logger.info(f"Obtained output URL: {output_url}")

            # Verify if URL is accessible
            try:
                url_check = requests.head(output_url)
                url_check.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Unable to access output URL: {str(e)}")
                raise Exception(f"Unable to access output URL: {str(e)}")

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

            return (img_tensor,)

        except Exception as e:
            error_msg = f"Error during image generation: {str(e)}"
            logger.error(error_msg)
            logger.exception("Detailed error information:")
            # Return an error marker image, ensure shape is [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
