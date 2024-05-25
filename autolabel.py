import os
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

class AutoLabel:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "a photography of"}),
                "repo_id": ("STRING", {"default": "Salesforce/blip-image-captioning-base"}),
                "inference_mode": (["gpu_float16", "gpu", "cpu"],),
                "get_model_online": ("BOOLEAN", {"default": True},)
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("main_object_description",)
    FUNCTION = "generate_caption"
    CATEGORY = "AutoLabel"

    def tensor_to_image(self, tensor):
        tensor = tensor.cpu()
        image_np = tensor.squeeze().mul(255).clamp(0, 255).byte().numpy()
        image = Image.fromarray(image_np, mode='RGB')
        return image

    def generate_caption(self, image, prompt, repo_id, inference_mode, get_model_online):
        if image is None:
            raise ValueError("Need an image")
        if not repo_id:
            raise ValueError("Need a repo_id or local_model_path")

        if not get_model_online:
            os.environ['TRANSFORMERS_OFFLINE'] = "1"

        processor = BlipProcessor.from_pretrained(repo_id)

        pil_image = self.tensor_to_image(image)

        try:
            if inference_mode == "gpu_float16":
                model = BlipForConditionalGeneration.from_pretrained(repo_id, torch_dtype=torch.float16).to("cuda")
                inputs = processor(pil_image, prompt, return_tensors="pt").to("cuda", torch.float16)
            elif inference_mode == "gpu":
                model = BlipForConditionalGeneration.from_pretrained(repo_id).to("cuda")
                inputs = processor(pil_image, prompt, return_tensors="pt").to("cuda")
            else:
                model = BlipForConditionalGeneration.from_pretrained(repo_id)
                inputs = processor(pil_image, prompt, return_tensors="pt")

            out = model.generate(**inputs)
            description = processor.decode(out[0], skip_special_tokens=True)
            return (description,)

        except Exception as e:
            print(e)
            return ("Error occurred during caption generation",)

NODE_CLASS_MAPPINGS = {
    "AutoLabel": AutoLabel
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AutoLabel": "Auto Label"
}