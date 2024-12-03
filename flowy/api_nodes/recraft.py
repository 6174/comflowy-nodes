from .base import FlowyApiNode
from ..types import STRING, INT

class FlowyRecraft(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "image_size": (
                    [
                        "square_hd",
                        "square",
                        "portrait_4_3",
                        "portrait_16_9",
                        "landscape_4_3",
                        "landscape_16_9",
                        "custom",
                    ],
                ),
                "style": (
                    [
                        "realistic_image",
                        "digital_illustration",
                        "vector_illustration",
                        "realistic_image/b_and_w",
                        "realistic_image/hard_flash",
                        "realistic_image/hdr",
                        "realistic_image/natural_light",
                        "realistic_image/studio_portrait",
                        "realistic_image/enterprise",
                        "realistic_image/motion_blur",
                        "digital_illustration/pixel_art",
                        "digital_illustration/hand_drawn",
                        "digital_illustration/grain",
                        "digital_illustration/infantile_sketch",
                        "digital_illustration/2d_art_poster",
                        "digital_illustration/handmade_3d",
                        "digital_illustration/hand_drawn_outline",
                        "digital_illustration/engraving_color",
                        "digital_illustration/2d_art_poster_2",
                        "vector_illustration/engraving",
                        "vector_illustration/line_art",
                        "vector_illustration/line_circuit",
                        "vector_illustration/linocut",
                    ],
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            },
            "optional": {
                "height": (
                    "INT",
                    {
                        "default": 512,
                        "min": 256,
                        "max": 2048,
                        "hidden": "image_size != 'custom'",
                    },
                ),
                "width": (
                    "INT",
                    {
                        "default": 512,
                        "min": 256,
                        "max": 2048,
                        "hidden": "image_size != 'custom'",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate images using Recraft AI.
- How to use: 
    - Provide a prompt to generate an image.
    - Style: The style of the generated images. Vector images cost 2X as much. 
- Output: Returns the generated image.
"""

    def get_model_type(self) -> str:
        return "recraft"

    def prepare_payload(self, **kwargs) -> dict:
        return {
            "prompt": kwargs["prompt"],
            "image_size": kwargs["image_size"],
            "height": kwargs.get("height"),
            "width": kwargs.get("width"),
            "style": kwargs["style"],
            "seed": kwargs["seed"],
        }
