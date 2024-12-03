import json
import os
import time

import torch
from ..base import FlowyApiNode
from .schema_to_node import (
    schema_to_comfyui_input_types,
    get_return_type,
    name_and_version,
    inputs_that_need_arrays,
)
from ...api_key_manager import load_api_key

def create_comfyui_node(schema):
    replicate_model, node_name = name_and_version(schema)
    return_type = get_return_type(schema)

    class ReplicateNode(FlowyApiNode):
        @classmethod
        def IS_CHANGED(cls, **kwargs):
            return time.time() if kwargs["force_rerun"] else ""

        @classmethod
        def INPUT_TYPES(cls):
            return schema_to_comfyui_input_types(schema)

        RETURN_TYPES = (
            tuple(return_type.values())
            if isinstance(return_type, dict)
            else (return_type,)
        )
        CATEGORY = "Comflowy Replicate"

        def get_model_type(self) -> str:
            return "replicate"

        def get_api_key(self) -> str:
            """获取 Comflowy API token"""
            api_key = load_api_key()
            if not api_key:
                raise ValueError("Comflowy API key not found. Please set your API key first.")
            return api_key

        def prepare_payload(self, **kwargs):
            # Remove force_rerun from kwargs
            kwargs = {k: v for k, v in kwargs.items() if k != "force_rerun"}

            # Handle array inputs
            array_inputs = inputs_that_need_arrays(schema)
            for input_name in array_inputs:
                if input_name in kwargs:
                    if isinstance(kwargs[input_name], str):
                        kwargs[input_name] = (
                            []
                            if kwargs[input_name] == ""
                            else kwargs[input_name].split("\n")
                        )
                    else:
                        kwargs[input_name] = [kwargs[input_name]]

            # Process image and audio inputs
            for key, value in kwargs.items():
                if value is not None:
                    input_type = (
                        self.INPUT_TYPES()["required"].get(key, (None,))[0]
                        or self.INPUT_TYPES().get("optional", {}).get(key, (None,))[0]
                    )
                    if input_type == "IMAGE":
                        kwargs[key] = self.image_to_base64(value)
                    elif input_type == "AUDIO":
                        kwargs[key] = self.audio_to_base64(value)

            # Remove empty optional inputs
            optional_inputs = self.INPUT_TYPES().get("optional", {})
            for key in list(kwargs.keys()):
                if key in optional_inputs:
                    if isinstance(kwargs[key], torch.Tensor):
                        continue
                    elif not kwargs[key]:
                        del kwargs[key]

            # 添加 API token 到 payload
            return {
                "replicate_model": replicate_model, 
                "input": kwargs,
                "api_key": self.get_api_key()  # 添加 API token
            }

    return node_name, ReplicateNode


def create_comfyui_nodes_from_schemas(schemas_dir):
    nodes = {}
    current_path = os.path.dirname(os.path.abspath(__file__))
    schemas_dir_path = os.path.join(current_path, schemas_dir)
    for schema_file in os.listdir(schemas_dir_path):
        if schema_file.endswith(".json"):
            with open(
                os.path.join(schemas_dir_path, schema_file), "r", encoding="utf-8"
            ) as f:
                schema = json.load(f)
                node_name, node_class = create_comfyui_node(schema)
                nodes[node_name] = node_class
    return nodes


_cached_node_class_mappings = None

def get_node_class_mappings():
    global _cached_node_class_mappings
    if _cached_node_class_mappings is None:
        _cached_node_class_mappings = create_comfyui_nodes_from_schemas("schemas")
    return _cached_node_class_mappings


REPLICATE_NODE_CLASS_MAPPINGS = get_node_class_mappings()
