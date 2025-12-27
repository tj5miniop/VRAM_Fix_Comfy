import comfy.model_management as mm
import logging

class VRAMOverrideNode:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "vram_gb": ("INT", {"default": 8, "min": 1, "max": 128, "step": 1}),
                "ram_gb": ("INT", {"default": 32, "min": 1, "max": 512, "step": 1}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "apply_override"
    CATEGORY = "custom_fixes"
    OUTPUT_NODE = True

    def apply_override(self, vram_gb, ram_gb):
        # Convert GB to Bytes
        vram_bytes = vram_gb * 1024 * 1024 * 1024
        ram_bytes = ram_gb * 1024 * 1024 * 1024

        # Monkey Patching the ComfyUI memory management functions
        # This replaces the built-in functions with ones that return your specific values
        def get_free_memory_override(device=None):
            return vram_bytes

        def get_total_memory_override(device=None):
            return vram_bytes

        # Overwrite the functions in the model_management module
        mm.get_free_memory = get_free_memory_override
        mm.get_total_memory = get_total_memory_override
        
        logging.info(f"VRAM Override Applied: Setting VRAM to {vram_gb}GB")
        return ()

# Register the node so it appears in the UI
NODE_CLASS_MAPPINGS = {
    "VRAMOverrideNode": VRAMOverrideNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VRAMOverrideNode": "VRAM/RAM Manual Override"
}