import time
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
from ..types import STRING, INT, SAFETY_TOLERANCE, BOOLEAN, FLOAT, NUM_IMAGES, OUTPUT_FORMAT
from ..utils import logger, get_nested_value
from ..api_key_manager import load_api_key

logger = logging.getLogger(__name__)
from .base import FlowyApiNode

class FlowyFluxDevLora(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "lora_path": ("STRING", {"multiline": True}),
                "lora_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 4.0, "step": 0.1}),
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
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "num_inference_steps": ("INT", {"default": 28, "min": 1, "max": 50}),
                "guidance_scale": ("FLOAT", {"default": 3.5, "min": 1.0, "max": 20.0, "step": 0.1}),
                "num_images": (NUM_IMAGES,),
                "safety_tolerance": (SAFETY_TOLERANCE,),
                "output_format": (OUTPUT_FORMAT,),
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
    FUNCTION = "generate"
    DESCRIPTION = """Nodes from https://comflowy.com: 
    - Description: A service to generate images using Flux AI.
    - How to use: 
        - Provide a prompt to generate an image.
        - Choose version, image_size, height, width, seed, and other parameters.
        - Height and width are only used when image_size=custom.
        - Make sure to set your API Key using the 'Comflowy Set API Key' node first.
    - Output: Returns the generated image."""

    def get_model_type(self) -> str:
        return "fluxdevlora"

    def prepare_payload(self, **kwargs) -> dict:
       return {
            "prompt": kwargs["prompt"],
            "lora_path": kwargs["lora_path"],
            "lora_scale": kwargs["lora_scale"],
            "image_size": kwargs["image_size"],
            "seed": kwargs["seed"],
            "num_inference_steps": kwargs["num_inference_steps"],
            "guidance_scale": kwargs["guidance_scale"],
            "num_images": kwargs["num_images"],
            "safety_tolerance": kwargs["safety_tolerance"],
            "output_format": kwargs["output_format"],
            "height": kwargs["height"],
            "width": kwargs["width"],
        }
