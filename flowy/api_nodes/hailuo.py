from .base import FlowyApiNode
from ..types import STRING, INT, BOOLEAN, get_modal_cloud_web_url

class FlowyHailuo(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "prompt_optimizer": BOOLEAN,
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            }
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    OUTPUT_IS_PREVIEW = True
    FUNCTION = "generate"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate videos from images by Hailuo AI.
- How to use: 
    - Provide an image and a prompt.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated video.
"""

    def get_model_type(self) -> str:
        return "hailuo"

    def get_api_host(self) -> str:
        API_HOST = get_modal_cloud_web_url()
        return f"{API_HOST}/api/open/v0/flowy"

    def prepare_payload(self, **kwargs) -> dict:
        image_base64 = self.image_to_base64(kwargs["image"])
        return {
            "image": image_base64,
            "prompt": kwargs["prompt"],
            "prompt_optimizer": kwargs["prompt_optimizer"],
            "seed": kwargs["seed"],
        }
