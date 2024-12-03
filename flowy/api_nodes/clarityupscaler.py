from .base import FlowyApiNode
from ..types import STRING, INT, get_api_host

class FlowyClarityUpscale(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": (
                    "FLOAT",
                    {"default": 2.0, "min": 1.0, "max": 4.0, "step": 0.1},
                ),
                "dynamic": (
                    "FLOAT",
                    {"default": 6.0, "min": 1.0, "max": 50.0, "step": 0.1},
                ),
                "creativity": (
                    "FLOAT",
                    {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "resemblance": (
                    "FLOAT",
                    {"default": 0.6, "min": 0.0, "max": 3.0, "step": 0.01},
                ),
                "tiling_width": ( [ 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256, ], {"default": 112}, ),
                "tiling_height": ( [ 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256, ], {"default": 144}, ),
                "num_inference_steps": ("INT", {"default": 18, "min": 1, "max": 100}),
                "seed": ("INT", {"default": 1337, "min": 0, "max": 2147483647}),
                "handfix": (
                    ["disabled", "hands_only", "image_and_hands"],
                    {"default": "disabled"},
                ),
                "pattern": ("BOOLEAN", {"default": False}),
                "sharpen": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1},
                ),
                "downscaling": ("BOOLEAN", {"default": False}),
                "downscaling_resolution": (
                    "INT",
                    {"default": 768, "min": 256, "max": 2048},
                ),
                "sd_model": (
                    [
                        "epicrealism_naturalSinRC1VAE.safetensors [84d76a0328]",
                        "juggernaut_reborn.safetensors [338b85bc4f]",
                        "flat2DAnimerge_v45Sharp.safetensors",
                    ],
                    {"default": "juggernaut_reborn.safetensors [338b85bc4f]"},
                ),
                "scheduler": ( [ "DPM++ 2M Karras", "DPM++ SDE Karras", "DPM++ 2M SDE Exponential", "DPM++ 2M SDE Karras", "Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM++ 2S a", "DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "DPM++ 2M SDE Heun", "DPM++ 2M SDE Heun Karras", "DPM++ 2M SDE Heun Exponential", "DPM++ 3M SDE", "DPM++ 3M SDE Karras", "DPM++ 3M SDE Exponential", "DPM fast", "DPM adaptive", "LMS Karras", "DPM2 Karras", "DPM2 a Karras", "DPM++ 2S a Karras", "Restart", "DDIM", "PLMS", "UniPC", ], {"default": "DPM++ 3M SDE Karras"}, ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"  # Changed from upscale to match parent class
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to upscale images using AI models.
- How to use: 
    - Provide an image to upscale.
    - Dynamic: HDR, try from 3 - 9.
    - Pattern: Upscale a pattern with seamless tiling.
    - Creativity: Try from 0.3 - 0.9.
    - Downscaling: Downscale the image before upscaling. Can improve quality and speed for images with high resolution but lower quality.
    - Resemblance: Try from 0.3 - 1.6.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the upscaled image.
"""

    def get_model_type(self) -> str:
        return "clarityupscaler"

    def get_api_host(self) -> str:
        API_HOST = get_api_host()
        return f"{API_HOST}/api/open/v0/clarityupscaler"

    def prepare_payload(self, **kwargs) -> dict:
        image_base64 = self.image_to_base64(kwargs["image"])
        return {
            "image": image_base64,
            "scale_factor": kwargs["scale_factor"],
            "dynamic": kwargs["dynamic"],
            "creativity": kwargs["creativity"],
            "resemblance": kwargs["resemblance"],
            "tiling_width": kwargs["tiling_width"],
            "tiling_height": kwargs["tiling_height"],
            "num_inference_steps": kwargs["num_inference_steps"],
            "seed": kwargs["seed"],
            "handfix": kwargs["handfix"],
            "pattern": kwargs["pattern"],
            "sharpen": kwargs["sharpen"],
            "downscaling": kwargs["downscaling"],
            "downscaling_resolution": kwargs["downscaling_resolution"],
            "sd_model": kwargs["sd_model"],
            "scheduler": kwargs["scheduler"],
        }
