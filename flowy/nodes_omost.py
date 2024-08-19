from enum import Enum
import json
from typing import Tuple, TypedDict
from typing_extensions import NotRequired
from comfy.sd import CLIP
import torch
from nodes import CLIPTextEncode, ConditioningSetMask

from .lib_omost.utils import numpy2pytorch
from .lib_omost.canvas import OmostCanvasCondition, Canvas as OmostCanvas
from .lib_omost.greedy_encode import (
    encode_bag_of_subprompts_greedy,
    CLIPTokens,
    EncoderOutput,
    SPECIAL_TOKENS,
)

CATEGORY = "Comflowy/omost"
from .utils import llm_request, logger
from .types import LLM_MODELS, STRING
CANVAS_SIZE = 90

system_prompt = r"""You are a helpful AI assistant to compose images using the a json-based canvas system:

The JSON Schema is defined in typescript as follows:
```ts
type Location = "in the center" | "on the left" | "on the right" | "on the top" | "on the bottom" | "on the top-left" | "on the top-right" | "on the bottom-left" | "on the bottom-right"
type Offset = "no offset" | "slightly to the left" | "slightly to the right" | "slightly to the upper" | "slightly to the lower" | "slightly to the upper-left" | "slightly to the upper-right" | "slightly to the lower-left" | "slightly to the lower-right"
type Area = "a small square area" | "a small vertical area" | "a small horizontal area" | "a medium-sized square area" | "a medium-sized vertical area" | "a medium-sized horizontal area" | "a large square area" | "a large vertical area" | "a large horizontal area"
type GlobalDescription = {
    description: string,
    detailed_descriptions: string[],
    tags: string,
    HTML_web_color_name: string,
}
type LocalDescription = {
    location: Location, 
    offset: Offset, 
    area: str, 
    distance_to_viewer: float, 
    description: str, 
    detailed_descriptions: list[str], 
    tags: str, 
    atmosphere: str, 
    style: str, 
    quality_meta: str, 
    HTML_web_color_name: str
}
type Canvas = {
    global_description: GlobalDescription,
    local_descriptions: LocalDescription[]
}
```

Rules:
- If the request language is not english, translate to english before sending it to the model.
- Response should be pure json code, which can be directly used in the next node.
- Response json object schema should be the same as the `Canvas` type defined above.
- HTML_web_color_name should be a valid web css color name, see https://www.w3schools.com/colors/colors_names.asp, not a rgb value
- Value in JSON field should not be empty
```

Example:
- Input: "Describe a painting with a large square area in the center."
- Output:

{
  "global_description": {
    "description": "A fierce battle between warriors and a dragon.",
    "detailed_descriptions": [
      "In this intense scene, a group of fierce warriors is engaged in an epic battle with a mighty dragon.",
      "The warriors, clad in armor and wielding swords and shields, are positioned on the left side of the image.",
      "Their expressions are determined and focused, reflecting their resolve to defeat the dragon.",
      "The dragon, with its massive wings spread wide and its fiery breath illuminating the scene, dominates the center of the image.",
    ],
    "tags": "battle, warriors, dragon, fierce, armor, swords, shields, determined, focused, epic, intense, metallic, glistening, fiery breath, stormy sky, lightning, debris, conflict",
    "HTML_web_color_name": "darkslategray"
  },
  "local_descriptions": [
    {
      "location": "on the left",
      "offset": "no offset",
      "area": "a large horizontal area",
      "distance_to_viewer": 5.0,
      "description": "A group of fierce warriors.",
      "detailed_descriptions": [
        "The warriors, clad in gleaming armor, are positioned on the left side of the image.",
        "They are armed with swords, shields, and spears, ready for battle.",
        "Their faces are set with determination and focus, reflecting their resolve to defeat the dragon.",
      ],
      "tags": "warriors, armor, swords, shields, spears, determined, focused, mid-action",
      "atmosphere": "Determined and focused, ready for the fierce battle.",
      "style": "Highly detailed and dynamic, capturing the intensity of the warriors.",
      "quality_meta": "High resolution with intricate details and dynamic poses.",
      "HTML_web_color_name": "darkgoldenrod"
    },
    {
      "location": "in the center",
      "offset": "no offset",
      "area": "a large square area",
      "distance_to_viewer": 7.0,
      "description": "A mighty dragon.",
      "detailed_descriptions": [
        "The dragon is a massive creature, dominating the center of the image with its wide-spread wings and fiery breath.",
        "Its scales glisten with a metallic sheen, reflecting the light from its fiery breath.",
        "The dragon's eyes burn with a fierce intensity, and its teeth are sharp and menacing.",
      ],
      "tags": "dragon, massive, wings, fiery breath, glistening scales, metallic sheen, fierce eyes, sharp teeth, powerful wings, shadows, battlefield",
      "atmosphere": "Intense and menacing, with a powerful presence.",
      "style": "Epic and dramatic, emphasizing the grandeur and danger of the dragon.",
      "quality_meta": "High resolution with dramatic lighting and detailed textures.",
      "HTML_web_color_name": "firebrick"
    }
  ]
}
"""


# 运行 LLM 生成区域描述
class OmostLLMNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "llm_model": (LLM_MODELS,),
                "api_key": STRING,
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
        }
    RETURN_TYPES = (
        "OMOST_CANVAS_CONDITIONING",
        "STRING",
    )
    RETURN_NAMES = (
        "canvas_conds",
        "generated_text",
    )
    FUNCTION = "run_llm"
    CATEGORY = CATEGORY

    def run_llm(self, prompt: str, llm_model: str, seed: int, api_key: str) -> Tuple[list[OmostCanvasCondition]]:
        """Run LLM to generate area conditioning."""
        if seed > 0xFFFFFFFF:
            seed = seed & 0xFFFFFFFF
            logger.warning("Seed is too large. Truncating to 32-bit: %d", seed)

        try:
            generated_text = llm_request(prompt=prompt, llm_model=llm_model, system_prompt=system_prompt, api_key=api_key, max_tokens=4000, timeout=10)
            # 如果生成的字符中包含了多余的字符，比如 "```json" 或者  "```"，则需要去掉改行
            generated_text = generated_text.replace("```json", "").replace("```", "")

            try:
                generated_json = json.loads(generated_text)
            except Exception as e:
                raise Exception(
                    f"Failed to parse response from LLM model: {str(e)}, Full response: {generated_text}"
                )
        except Exception as e:
            return ([], f"Error happend: {str(e)}")

        try:
            logger.info("Generated text: %s", generated_text)
            canvas = OmostCanvas()
            global_description = generated_json["global_description"]
            canvas.set_global_description(
                description=global_description["description"],
                detailed_descriptions=global_description["detailed_descriptions"],
                tags=global_description["tags"],
                HTML_web_color_name=global_description["HTML_web_color_name"],
            )
            local_descriptions = generated_json["local_descriptions"]
            for local_description in local_descriptions:
                canvas.add_local_description(
                    location=local_description["location"],
                    offset=local_description["offset"],
                    area=local_description["area"],
                    distance_to_viewer=local_description["distance_to_viewer"],
                    description=local_description["description"],
                    detailed_descriptions=local_description["detailed_descriptions"],
                    tags=local_description["tags"],
                    atmosphere=local_description["atmosphere"],
                    style=local_description["style"],
                    quality_meta=local_description["quality_meta"],
                    HTML_web_color_name=local_description["HTML_web_color_name"],
                )
            ret = canvas.process()
            
            print("ret", ret)
            
            # ret = (OmostCanvas.from_bot_response(generated_text).process(),)
            return (ret, generated_text)
        except Exception as e:
            return ([], f"Error happend:\n ============= \n {str(e)} \n==========\n\n\n Full response: {generated_text}")

# 输出最终的 OmostCanvasCondition
class OmostToConditioning:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_conds": ("OMOST_CANVAS_CONDITIONING",),
                "clip": ("CLIP",),
                "global_strength": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01, "default": 0.2},
                ),
                "region_strength": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01, "default": 0.8},
                ),
                "overlap_method": (
                    [e.value for e in OmostToConditioning.AreaOverlapMethod],
                    {"default": OmostToConditioning.AreaOverlapMethod.AVERAGE.value},
                ),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "layout_cond"
    CATEGORY = CATEGORY
    DESCRIPTION = """Apply Omost layout with ComfyUI's area condition system."""

    class AreaOverlapMethod(Enum):
        """Methods to handle overlapping areas."""

        # The top layer overwrites the bottom layer.
        OVERLAY = "overlay"
        # Take the average of the two layers.
        AVERAGE = "average"

    def __init__(self):
        self.cond_set_mask_node = ConditioningSetMask()

    @staticmethod
    def calc_cond_mask(
        canvas_conds: list[OmostCanvasCondition],
        method: AreaOverlapMethod = AreaOverlapMethod.OVERLAY,
    ) -> list[OmostCanvasCondition]:
        """Calculate canvas cond mask."""
        assert len(canvas_conds) > 0
        canvas_conds = canvas_conds.copy()

        global_cond = canvas_conds[0]
        global_cond["mask"] = torch.ones(
            [CANVAS_SIZE, CANVAS_SIZE], dtype=torch.float32
        )
        region_conds = canvas_conds[1:]

        canvas_state = torch.zeros([CANVAS_SIZE, CANVAS_SIZE], dtype=torch.float32)
        if method == OmostToConditioning.AreaOverlapMethod.OVERLAY:
            for canvas_cond in region_conds[::-1]:
                a, b, c, d = canvas_cond["rect"]
                mask = torch.zeros([CANVAS_SIZE, CANVAS_SIZE], dtype=torch.float32)
                mask[a:b, c:d] = 1.0
                mask = mask * (1 - canvas_state)
                canvas_state += mask
                canvas_cond["mask"] = mask
        elif method == OmostToConditioning.AreaOverlapMethod.AVERAGE:
            canvas_state += 1e-6  # Avoid division by zero
            for canvas_cond in region_conds:
                a, b, c, d = canvas_cond["rect"]
                canvas_state[a:b, c:d] += 1.0

            for canvas_cond in region_conds:
                a, b, c, d = canvas_cond["rect"]
                mask = torch.zeros([CANVAS_SIZE, CANVAS_SIZE], dtype=torch.float32)
                mask[a:b, c:d] = 1.0
                mask = mask / canvas_state
                canvas_cond["mask"] = mask

        return canvas_conds

    def layout_cond(
        self,
        canvas_conds: list[OmostCanvasCondition],
        clip: CLIP,
        global_strength: float,
        region_strength: float,
        overlap_method: str,
    ):
        """Layout conditioning"""
        overlap_method = OmostToConditioning.AreaOverlapMethod(overlap_method)
        positive: ComfyUIConditioning = []
        masks: list[torch.Tensor] = []
        canvas_conds = OmostToConditioning.calc_cond_mask(
            canvas_conds, method=overlap_method
        )

        for i, canvas_cond in enumerate(canvas_conds):
            is_global = i == 0

            prefixes = canvas_cond["prefixes"]
            # Skip the global prefix for region prompts.
            if not is_global:
                prefixes = prefixes[1:]

            cond: ComfyUIConditioning = PromptEncoding.encode_bag_of_subprompts_greedy(
                clip, prefixes, canvas_cond["suffixes"]
            )
            # Set area cond
            cond: ComfyUIConditioning = self.cond_set_mask_node.append(
                cond,
                mask=canvas_cond["mask"],
                set_cond_area="default",
                strength=global_strength if is_global else region_strength,
            )[0]
            assert len(cond) == 1
            positive.extend(cond)
            masks.append(canvas_cond["mask"].unsqueeze(0))

        return (
            positive,
            # Output masks in case it's needed for debugging or the user might
            # want to apply extra condition such as ControlNet/IPAdapter to
            # specified region.
            # torch.cat(masks, dim=0),
        )


# 对于 LLM 动态生成的区域描述，该节点用于预览canvas的节点
class ComflowyOmostPreviewNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_conds": ("OMOST_CANVAS_CONDITIONING",),
            }
        }

    RETURN_TYPES = ("IMAGE", "JSON",)
    FUNCTION = "render_canvas"
    CATEGORY = CATEGORY

    def render_canvas(
        self, canvas_conds: list[OmostCanvasCondition]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Render canvas conditioning to image"""
        return (
            numpy2pytorch(imgs=[OmostCanvas.render_initial_latent(canvas_conds)]),
            canvas_conds,
            # torch.cat(
            #     [OmostCanvas.render_mask(cond).unsqueeze(0) for cond in canvas_conds],
            #     dim=0,
            # ),
        )


# 对于高级用户，可以直接编辑python代码，然后加载到这个节点中
class ComflowyOmostLoadCanvasPythonCodeNode:
    """Load python code generated by Omost demo app."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "python_str": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("OMOST_CANVAS_CONDITIONING",)
    FUNCTION = "load_canvas"
    CATEGORY = CATEGORY

    def load_canvas(self, python_str: str) -> Tuple[list[OmostCanvasCondition]]:
        """Load canvas from file"""
        canvas = OmostCanvas.from_python_code(python_str)
        return (canvas.process(),)

# 定义这个节点可以在后续直接做一个前端编辑器，用于编辑基于区域的条件
class ComflowyOmostLoadCanvasConditioningNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "omost_canvas_json": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("OMOST_CANVAS_CONDITIONING",)
    FUNCTION = "load_canvas"
    CATEGORY = CATEGORY

    def load_canvas(self, omost_canvas_json: str) -> Tuple[list[OmostCanvasCondition]]:
        """Load canvas from file"""
        return (json.loads(omost_canvas_json),)


ComfyUIConditioning = list  # Dummy type definitions for ComfyUI
ComfyCLIPTokensWithWeight = list[Tuple[int, float]]


class ComfyCLIPTokens(TypedDict):
    l: list[ComfyCLIPTokensWithWeight]
    g: NotRequired[list[ComfyCLIPTokensWithWeight]]


class PromptEncoding:
    """Namespace for different prompt encoding methods"""

    ENCODE_NODE = CLIPTextEncode()

    @staticmethod
    def encode_bag_of_subprompts(
        clip: CLIP, prefixes: list[str], suffixes: list[str]
    ) -> ComfyUIConditioning:
        """@Deprecated
        Simplified way to encode bag of subprompts without omost's greedy approach.
        """
        conds: ComfyUIConditioning = []

        logger.debug("Start encoding bag of subprompts")
        for target in suffixes:
            complete_prompt = "".join(prefixes + [target])
            logger.debug(f"Encoding prompt: {complete_prompt}")
            cond: ComfyUIConditioning = PromptEncoding.ENCODE_NODE.encode(
                clip, complete_prompt
            )[0]
            assert len(cond) == 1
            conds.extend(cond)

        logger.debug("End encoding bag of subprompts. Total conditions: %d", len(conds))

        # Concat all conditions
        return [
            [
                # cond
                torch.cat([cond for cond, _ in conds], dim=1),
                # extra_dict
                {"pooled_output": conds[0][1]["pooled_output"]},
            ]
        ]

    @staticmethod
    def encode_subprompts(
        clip: CLIP, prefixes: list[str], suffixes: list[str]
    ) -> ComfyUIConditioning:
        """@Deprecated
        Simplified way to encode subprompts by joining them together. This is
        more direct without re-organizing the prompts into optimal batches like
        with the greedy approach.
        Note: This function has the issue of semantic truncation.
        """
        complete_prompt = ",".join(
            ["".join(prefixes + [target]) for target in suffixes]
        )
        logger.debug("Encoding prompt: %s", complete_prompt)
        return PromptEncoding.ENCODE_NODE.encode(clip, complete_prompt)[0]

    @staticmethod
    def encode_bag_of_subprompts_greedy(
        clip: CLIP, prefixes: list[str], suffixes: list[str]
    ) -> ComfyUIConditioning:
        """Encode bag of subprompts with greedy approach. This approach is used
        by the original Omost repo."""

        def convert_comfy_tokens(
            comfy_tokens: list[ComfyCLIPTokensWithWeight],
        ) -> list[int]:
            assert len(comfy_tokens) >= 1
            tokens: list[int] = [token for token, _ in comfy_tokens[0]]
            # Strip the first token which is the CLIP prefix.
            # Strip padding tokens.
            return tokens[1 : tokens.index(SPECIAL_TOKENS["end"])]

        def convert_to_comfy_tokens(tokens: CLIPTokens) -> ComfyCLIPTokens:
            return {
                "l": [[(token, 1.0) for token in tokens.clip_l_tokens]],
                "g": (
                    [[(token, 1.0) for token in tokens.clip_g_tokens]]
                    if tokens.clip_g_tokens is not None
                    else None
                ),
            }

        def tokenize(text: str) -> CLIPTokens:
            tokens: ComfyCLIPTokens = clip.tokenize(text)
            return CLIPTokens(
                clip_l_tokens=convert_comfy_tokens(tokens["l"]),
                clip_g_tokens=(
                    convert_comfy_tokens(tokens.get("g")) if "g" in tokens else None
                ),
            )

        def encode(tokens: CLIPTokens) -> EncoderOutput:
            cond, pooled = clip.encode_from_tokens(
                convert_to_comfy_tokens(tokens), return_pooled=True
            )
            return EncoderOutput(cond=cond, pooler=pooled)

        encoder_output = encode_bag_of_subprompts_greedy(
            prefixes,
            suffixes,
            tokenize_func=tokenize,
            encode_func=encode,
            logger=logger,
        )

        return [
            [
                encoder_output.cond,
                {"pooled_output": encoder_output.pooler},
            ]
        ]
