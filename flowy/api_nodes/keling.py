from .base  import FlowyApiNode
from ..types import STRING, INT

class FlowyKling(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "version": (["standard", "pro"],),
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
                "duration": ([5, 10],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            }
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    OUTPUT_IS_PREVIEW = True
    FUNCTION = "generate"  # Changed from image_to_video to match parent class
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate videos from images by Kling AI.
- How to use: 
    - Provide an image and a prompt.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
    - Pro costs 1250 per second of video. Standard will cost 300 per second of video.
- Output: Returns the generated video.
"""

    def get_model_type(self) -> str:
        return "kling"

    def prepare_payload(self, **kwargs) -> dict:
        image_base64 = self.image_to_base64(kwargs["image"])
        return {
            "image": image_base64,
            "prompt": kwargs["prompt"],
            "version": kwargs["version"],
            "aspect_ratio": kwargs["aspect_ratio"],
            "duration": kwargs["duration"],
            "seed": kwargs["seed"],
        }
