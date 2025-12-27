import logging
import torch

def get_mm():
    try:
        import comfy.model_management as mm
        return mm
    except ImportError:
        from comfy import model_management as mm
        return mm

def apply_memory_patch(vram_gb, ram_gb):
    mm = get_mm()
    vram_bytes = vram_gb * 1024 * 1024 * 1024
    
    # Add overrides
    def get_free_memory_override(*args, **kwargs):
        return vram_bytes

    def get_total_memory_override(*args, **kwargs):
        return vram_bytes
            
    def get_vram_max_free_lib_override(*args, **kwargs):
        return vram_bytes

    # Apply to the core module
    mm.get_free_memory = get_free_memory_override
    mm.get_total_memory = get_total_memory_override
    
    if hasattr(mm, 'get_vram_max_free_lib'):
        mm.get_vram_max_free_lib = get_vram_max_free_lib_override
    
    # Force ComfyUI's internal constants to refresh if they exist
    if hasattr(mm, 'VRAM_TOTAL'):
        mm.VRAM_TOTAL = vram_bytes
        
    print(f"\n[VRAM Fix] Patch applied: Memory set to {vram_gb}GB\n")

# --- INITIALIZE ON STARTUP ---
# Defaults will be 8GB VRAM 32 GB RAM - Feel free to change this locally or on a fork
try:
    apply_memory_patch(8, 32)
except Exception as e:
    print(f"[VRAM Fix] Startup patch failed: {e}")
# Code above will result in an error incase the patch fails

class VRAMOverrideNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "vram_gb": ("INT", {"default": 8, "min": 1, "max": 128}),
                "ram_gb": ("INT", {"default": 32, "min": 1, "max": 512}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "manual_patch"
    CATEGORY = "custom_fixes"
    OUTPUT_NODE = True

    def manual_patch(self, vram_gb, ram_gb):
        apply_memory_patch(vram_gb, ram_gb)
        return ()

NODE_CLASS_MAPPINGS = {"VRAMOverrideNode": VRAMOverrideNode}
NODE_DISPLAY_NAME_MAPPINGS = {"VRAMOverrideNode": "VRAM/RAM Manual Override"}