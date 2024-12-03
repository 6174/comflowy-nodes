from .base import FlowyApiNode
from ..types import STRING, INT, SAFETY_TOLERANCE, BOOLEAN_FALSE


class FlowyFluxProUltra(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "image_size": (
                    ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "9:21"],
                ),
                "raw": BOOLEAN_FALSE,
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "safety_tolerance": (SAFETY_TOLERANCE,),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 4}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate images using Flux AI.
- How to use: 
    - Provide a prompt to generate an image.
    - Raw: Generate less processed, more natural-looking images
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated image.
"""

    def get_model_type(self) -> str:
        return "fluxproultra"

    def prepare_payload(self, **kwargs) -> dict:
        return {
            "prompt": kwargs["prompt"],
            "image_size": kwargs["image_size"],
            "raw": kwargs["raw"],
            "seed": kwargs["seed"],
            "safety_tolerance": kwargs["safety_tolerance"],
            "num_images": kwargs["num_images"],
        }
