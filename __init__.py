import logging
import torch
import psutil
from collections import namedtuple

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
    
    # 1. FIX VRAM: Handles both int and tuple returns for ComfyUI
    def universal_memory_return(*args, **kwargs):
        class MemoryTuple(int):
            def __iter__(self):
                return iter((vram_bytes, vram_bytes))
            def __getitem__(self, index):
                return vram_bytes
        return MemoryTuple(vram_bytes)

    target_functions = [
        'get_free_memory',
        'get_total_memory',
        'get_vram_max_free_lib',
        'get_torch_memory_stats'
    ]

    for func_name in target_functions:
        if hasattr(mm, func_name):
            setattr(mm, func_name, universal_memory_return)

    mm.VRAM_TOTAL = vram_bytes
    mm.RAM_TOTAL = ram_bytes

    # 2. FIX RAM: Patch psutil globally to trick the logging.info line
    # We create a mock object that mimics what psutil.virtual_memory() returns
    def patched_virtual_memory():
        mem_tuple = namedtuple('vmem', ['total', 'available', 'percent', 'used', 'free'])
        # Setting total to our manual value, others to 0 or manual for consistency
        return mem_tuple(ram_bytes, ram_bytes, 0.0, 0, ram_bytes)

    psutil.virtual_memory = patched_virtual_memory

    # 3. FIX Torch (Optional but recommended for consistency)
    if torch.cuda.is_available():
        # This tricks torch.cuda.get_device_properties().total_memory
        torch.cuda.get_device_properties = lambda device: namedtuple('prop', ['total_memory'])(vram_bytes)

    print(f"\n[VRAM Fix] Memory Overrides Applied: {vram_gb}GB VRAM / {ram_gb}GB RAM\n")

# Apply on startup
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
