from .base import FlowyApiNode
from ..types import STRING, INT, get_api_host


class FlowyIdeogram(FlowyApiNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "negative_prompt": ("STRING", {"multiline": True}),
                "version": (["ideogram-v2-turbo", "ideogram-v2"],),
                "resolution": ( [ "None", "512x1536", "576x1408", "576x1472", "576x1536", "640x1024", "640x1344", "640x1408", "640x1472", "640x1536", "704x1152", "704x1216", "704x1280", "704x1344", "704x1408", "704x1472", "720x1280", "736x1312", "768x1024", "768x1088", "768x1152", "768x1216", "768x1232", "768x1280", "768x1344", "832x960", "832x1024", "832x1088", "832x1152", "832x1216", "832x1248", "864x1152", "896x960", "896x1024", "896x1088", "896x1120", "896x1152", "960x832", "960x896", "960x1024", "960x1088", "1024x640", "1024x768", "1024x832", "1024x896", "1024x960", "1024x1024", "1088x768", "1088x832", "1088x896", "1088x960", "1120x896", "1152x704", "1152x768", "1152x832", "1152x864", "1152x896", "1216x704", "1216x768", "1216x832", "1232x768", "1248x832", "1280x704", "1280x720", "1280x768", "1280x800", "1312x736", "1344x640", "1344x704", "1344x768", "1408x576", "1408x640", "1408x704", "1472x576", "1472x640", "1472x704", "1536x512", "1536x576", "1536x640", ], ),
                "style_type": (
                    ["None", "Auto", "Realistic", "Design", "Anime", "Render 3D"],
                ),
                "aspect_ratio": ( [ "1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "16:10", "10:16", "3:1", "1:3", ], ),
                "magic_prompt_option": (["On", "Off"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
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

    def get_model_type(self) -> str:
        return "ideogram"

    def get_api_host(self) -> str:
        API_HOST = get_api_host()
        return f"{API_HOST}/api/open/v0/ideogram"

    def prepare_payload(self, **kwargs) -> dict:
        return {
            "prompt": kwargs["prompt"],
            "negative_prompt": kwargs["negative_prompt"],
            "version": kwargs["version"],
            "resolution": (
                kwargs["resolution"] if kwargs["resolution"] != "None" else None
            ),
            "style_type": (
                kwargs["style_type"] if kwargs["style_type"] != "None" else None
            ),
            "aspect_ratio": kwargs["aspect_ratio"],
            "magic_prompt_option": kwargs["magic_prompt_option"],
            "seed": kwargs["seed"],
        }
