import logging

# We import this inside the class or method to avoid initialization race conditions
def get_mm():
    try:
        import comfy.model_management as mm
        return mm
    except ImportError:
        # Fallback for different directory structures
        from comfy import model_management as mm
        return mm

class VRAMOverrideNode:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "vram_gb": ("INT", {"default": 8, "min": 1, "max": 128, "step": 1}),
                "ram_gb": ("INT", {"default": 32, "min": 1, "max": 512, "step": 1}),
                "mode": (["Enabled", "Disabled"],),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "apply_override"
    CATEGORY = "custom_fixes"
    OUTPUT_NODE = True

    def apply_override(self, vram_gb, ram_gb, mode):
        if mode == "Disabled":
            return ()

        mm = get_mm()
        
        # Convert GB to Bytes
        vram_bytes = vram_gb * 1024 * 1024 * 1024

        # Patching the functions
        # We use 'unused_arg' because Comfy calls these with a device argument
        def get_free_memory_override(device=None):
            return vram_bytes

        def get_total_memory_override(device=None):
            return vram_bytes

        # Apply the monkey patch
        mm.get_free_memory = get_free_memory_override
        mm.get_total_memory = get_total_memory_override
        
        print(f"\n[VRAM Fix] Manual Override: {vram_gb}GB VRAM ({vram_bytes} bytes)\n")
        return ()

# Important: These must be outside the class
NODE_CLASS_MAPPINGS = {
    "VRAMOverrideNode": VRAMOverrideNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VRAMOverrideNode": "VRAM/RAM Manual Override"
}