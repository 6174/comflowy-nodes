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

class FlowyIdeogram:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "negative_prompt": ("STRING", {"multiline": True}),
                "version": (["ideogram-v2-turbo", "ideogram-v2"],),
                "resolution": (["None", "512x1536", "576x1408", "576x1472", "576x1536", "640x1024", "640x1344", "640x1408", "640x1472", "640x1536", "704x1152", "704x1216", "704x1280", "704x1344", "704x1408", "704x1472", "720x1280", "736x1312", "768x1024", "768x1088", "768x1152", "768x1216", "768x1232", "768x1280", "768x1344", "832x960", "832x1024", "832x1088", "832x1152", "832x1216", "832x1248", "864x1152", "896x960", "896x1024", "896x1088", "896x1120", "896x1152", "960x832", "960x896", "960x1024", "960x1088", "1024x640", "1024x768", "1024x832", "1024x896", "1024x960", "1024x1024", "1088x768", "1088x832", "1088x896", "1088x960", "1120x896", "1152x704", "1152x768", "1152x832", "1152x864", "1152x896", "1216x704", "1216x768", "1216x832", "1232x768", "1248x832", "1280x704", "1280x720", "1280x768", "1280x800", "1312x736", "1344x640", "1344x704", "1344x768", "1408x576", "1408x640", "1408x704", "1472x576", "1472x640", "1472x704", "1536x512", "1536x576", "1536x640"],),
                "style_type": (["None", "Auto", "Realistic", "Design", "Anime", "Render 3D"],),
                "aspect_ratio": (["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "16:10", "10:16", "3:1", "1:3"],),
                "magic_prompt_option": (["On", "Off"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image_with_ideogram"
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate images using Ideogram AI.
- How to use: 
    - Provide a prompt to generate an image.
    - Choose resolution, style type, aspect ratio, and magic prompt option.
    - Resolution overrides aspect ratio. 
    - Magic Prompt will interpret your prompt and optimize it to maximize variety and quality of the images generated. You can also use it to write prompts in different languages.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated image.
"""

    def generate_image_with_ideogram(self, prompt, negative_prompt, version, resolution, style_type, aspect_ratio, magic_prompt_option, seed):
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting Ideogram image generation request. prompt: {prompt}, negative_prompt: {negative_prompt}, resolution: {resolution}, style_type: {style_type}, aspect_ratio: {aspect_ratio}, magic_prompt_option: {magic_prompt_option}, seed: {seed}")

        try:
            response = requests.post(
                f"{API_HOST}/api/open/v0/ideogram",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "version": version, 
                    "resolution": resolution if resolution != "None" else None,
                    "style_type": style_type if style_type != "None" else None,
                    "aspect_ratio": aspect_ratio,
                    "magic_prompt_option": magic_prompt_option,
                    "seed": seed,
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

            # Convert to numpy array
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

            return (img_tensor,)

        except Exception as e:
            error_msg = f"Error during image generation: {str(e)}"
            logger.error(error_msg)
            logger.exception("Detailed error information:")
            # Return an error marked image, ensuring shape is [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
