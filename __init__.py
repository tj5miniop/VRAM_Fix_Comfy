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
    ram_bytes = ram_gb * 1024 * 1024 * 1024
    
    # Hopefully fixes relevant error - cannot unpack non-iterable int object
    # This handles cases where ComfyUI expects a single int OR a tuple (free, total)
    def universal_memory_return(*args, **kwargs):
        class MemoryTuple(int):
            def __iter__(self):
                return iter((vram_bytes, vram_bytes))
            def __getitem__(self, index):
                return vram_bytes
        return MemoryTuple(vram_bytes)

    # Overwrite every possible function ComfyUI uses to check memory
    target_functions = [
        'get_free_memory',
        'get_total_memory',
        'get_vram_max_free_lib',
        'get_torch_memory_stats'
    ]

    for func_name in target_functions:
        if hasattr(mm, func_name):
            setattr(mm, func_name, universal_memory_return)

    # Some logic checks these constants instead of calling functions
    mm.VRAM_TOTAL = vram_bytes
    mm.RAM_TOTAL = ram_bytes
    
    # try patching xformers and CUDA (This may mean that this node will only work for NVIDIA related setups?)
    if hasattr(mm, 'current_protocol'):
        try:
            mm.vram_state = mm.VRAMState.NORMAL
        except:
            pass

    print(f"\n[VRAM Fix] High-Level Patch Applied: {vram_gb}GB VRAM / {ram_gb}GB RAM\n")

# Apply on startup default values; 8GB VRAM 32GB RAM
try:
    apply_memory_patch(8, 32)
except Exception as e:
    print(f"[VRAM Fix] Startup injection failed: {e}")

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
    CATEGORY = "fixes"
    OUTPUT_NODE = True

    def manual_patch(self, vram_gb, ram_gb):
        apply_memory_patch(vram_gb, ram_gb)
        return ()

NODE_CLASS_MAPPINGS = {"VRAMOverrideNode": VRAMOverrideNode}
NODE_DISPLAY_NAME_MAPPINGS = {"VRAMOverrideNode": "VRAM/RAM Manual Override"}