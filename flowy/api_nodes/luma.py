from .base import FlowyApiNode
from ..types import STRING, INT, BOOLEAN_FALSE


class FlowyLuma(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            },
            "optional": {
                "end_image_optional": ("IMAGE",),
                "loop": BOOLEAN_FALSE,
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    OUTPUT_IS_PREVIEW = True
    FUNCTION = "generate"  # Changed from image_to_video to match parent class
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate videos from images by Luma AI.
- How to use: 
    - Provide an image and a prompt.
    - Loop: Whether the video should loop (end of video is blended with the beginning).
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated video.
"""

    def get_model_type(self) -> str:
        return "luma"

    def prepare_payload(self, **kwargs) -> dict:
        image_base64 = self.image_to_base64(kwargs["image"])
        return {
            "image": image_base64,
            "prompt": kwargs["prompt"],
            "aspect_ratio": kwargs["aspect_ratio"],
            "end_image": kwargs.get("end_image_optional"),  # Optional parameter
            "loop": kwargs.get("loop", False),  # Optional parameter with default
            "seed": kwargs["seed"],
        }
