import time
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
from ..types import STRING, INT, SAFETY_TOLERANCE, BOOLEAN, NUM_IMAGES
from ..utils import logger, get_nested_value
from ..api_key_manager import load_api_key

logger = logging.getLogger(__name__)
from .base import FlowyApiNode

class FlowyFlux(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "version": (["flux-1.1-pro", "flux-pro", "flux-dev"],),
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
                "safety_tolerance": (SAFETY_TOLERANCE,),
                "num_images": (NUM_IMAGES,),
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
        - Choose version, image_size, height, width, and seed.
        - Height and width are only used when image_size=custom.
        - Make sure to set your API Key using the 'Comflowy Set API Key' node first.
    - Output: Returns the generated image."""

    def get_model_type(self) -> str:
        return "flux"

    def prepare_payload(self, **kwargs) -> dict:
        return {
            "prompt": kwargs["prompt"],
            "version": kwargs["version"],
            "image_size": kwargs["image_size"],
            "height": kwargs["height"],
            "width": kwargs["width"],
            "seed": kwargs["seed"],
            "safety_tolerance": kwargs["safety_tolerance"],
            "num_images": kwargs["num_images"],
        }
