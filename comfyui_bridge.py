import sys
import json
import requests
import time
import uuid
import argparse
import os
import struct
import zlib
from pathlib import Path

API_BASE = "http://127.0.0.1:8188"
OUTPUT_DIR = Path(r"E:\sd-comfyui\ComfyUI\output")
INPUT_DIR = Path(r"E:\sd-comfyui\ComfyUI\input")


def create_png_with_alpha(width, height, mask_func, filepath):
    """Create a grayscale PNG with alpha channel. mask_func(x,y) returns 0-1."""
    raw_data = b""
    for y in range(height):
        row = bytearray()
        for x in range(width):
            val = int(mask_func(x, y) * 255)
            row.extend([val, val, val, val])  # RGBA
        raw_data += bytes([0]) + row  # filter byte + row
    # IHDR
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF
    # IDAT
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    with open(filepath, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", ihdr_crc))
        f.write(struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc))
        f.write(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF))


def build_workflow(prompt, negative_prompt="", model="anything-v5-PrtRE.safetensors",
                   steps=35, cfg=7, seed=-1, batch_size=1, mode="normal", model_type="sd15", portrait=False,
                   lora_name=None, lora_strength=1.0):
    if seed == -1:
        seed = int(time.time() * 1000) % (2**32)

    if model_type == "sdxl":
        controlnet = "xinsir-controlnet-tile-sdxl-1.0.safetensors"
    else:
        controlnet = "control_v11f1e_sd15_tile.pth"

    w, h = (544, 960) if portrait else (960, 544)

    from_scratch = True

    workflow = {"17": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x_NMKD-Superscale-SP_178000_G.pth"}}}

    if from_scratch:
        workflow["4"] = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}}
        workflow["12"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": controlnet}}

    if lora_name:
        workflow["50"] = {
            "class_type": "LoraLoader",
            "inputs": {"lora_name": lora_name, "strength_model": lora_strength, "strength_clip": lora_strength,
                       "model": ["4", 0], "clip": ["4", 1]}
        }
        model_node = "50"
        clip_node = "50"
    else:
        model_node = "4"
        clip_node = "4"

    if from_scratch:
        if model_type == "sdxl":
            workflow["6"] = {
                "class_type": "CLIPTextEncodeSDXL",
                "inputs": {"width": w, "height": h, "crop_w": 0, "crop_h": 0,
                           "target_width": w, "target_height": h,
                           "text_g": prompt, "text_l": prompt, "clip": [clip_node, 1]}
            }
            workflow["7"] = {
                "class_type": "CLIPTextEncodeSDXL",
                "inputs": {"width": w, "height": h, "crop_w": 0, "crop_h": 0,
                           "target_width": w, "target_height": h,
                           "text_g": negative_prompt, "text_l": negative_prompt, "clip": [clip_node, 1]}
            }
        else:
            workflow["6"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": [clip_node, 1]}}
            workflow["7"] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": [clip_node, 1]}}

    if mode == "inpaint_face":
        # Load source image and mask for face inpainting
        workflow["40"] = {"class_type": "LoadImage", "inputs": {"image": "inpaint_src.png"}}
        workflow["41"] = {"class_type": "LoadImage", "inputs": {"image": "inpaint_mask.png"}}
        workflow["42"] = {
            "class_type": "VAEEncodeForInpaint",
            "inputs": {"pixels": ["40", 0], "vae": ["4", 2], "mask": ["41", 1], "grow_mask_by": 6}
        }
        workflow["43"] = {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 0.45,
                "model": [model_node, 0], "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["42", 0]
            }
        }
        workflow["44"] = {"class_type": "VAEDecode", "inputs": {"samples": ["43", 0], "vae": ["4", 2]}}
        workflow["45"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "ComfyUI_facefix", "images": ["44", 0]}}
    elif mode in ("4k", "4k_upscale"):
        tile = 512 if model_type == "sdxl" else 896

        if mode == "4k_upscale":
            workflow["40"] = {"class_type": "LoadImage", "inputs": {"image": "upscale_src.png"}}
            src_node = "40"
        else:
            workflow["5"] = {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": batch_size}}
            workflow["3"] = {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed, "steps": steps, "cfg": cfg,
                    "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1,
                    "model": [model_node, 0], "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            }
            workflow["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}}
            src_node = "8"

        # Pass 1: 4x AI upscale + ControlNet
        workflow["13"] = {"class_type": "ControlNetApply", "inputs": {
            "conditioning": ["6", 0], "control_net": ["12", 0], "image": [src_node, 0], "strength": 0.35
        }}
        workflow["14"] = {"class_type": "ControlNetApply", "inputs": {
            "conditioning": ["7", 0], "control_net": ["12", 0], "image": [src_node, 0], "strength": 0.35
        }}
        workflow["9"] = {
            "class_type": "UltimateSDUpscaleCustomSample",
            "inputs": {
                "image": [src_node, 0], "model": [model_node, 0],
                "positive": ["13", 0], "negative": ["14", 0],
                "vae": ["4", 2],
                "upscale_by": 4, "seed": seed + 1, "steps": 10, "cfg": 7,
                "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 0.28,
                "upscale_model": ["17", 0],
                "mode_type": "Chess", "tile_width": tile, "tile_height": tile,
                "mask_blur": 8, "tile_padding": 32,
                "seam_fix_mode": "None", "seam_fix_denoise": 1.0,
                "seam_fix_width": 64, "seam_fix_mask_blur": 8, "seam_fix_padding": 16,
                "force_uniform_tiles": True, "tiled_decode": True
            }
        }

        # Pass 2: detail refinement at 4K
        workflow["18"] = {"class_type": "ControlNetApply", "inputs": {
            "conditioning": ["6", 0], "control_net": ["12", 0], "image": ["9", 0], "strength": 0.2
        }}
        workflow["19"] = {"class_type": "ControlNetApply", "inputs": {
            "conditioning": ["7", 0], "control_net": ["12", 0], "image": ["9", 0], "strength": 0.2
        }}
        workflow["20"] = {
            "class_type": "UltimateSDUpscaleNoUpscale",
            "inputs": {
                "upscaled_image": ["9", 0], "model": [model_node, 0],
                "positive": ["18", 0], "negative": ["19", 0],
                "vae": ["4", 2],
                "seed": seed + 2, "steps": 8, "cfg": 7,
                "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 0.12,
                "mode_type": "Chess", "tile_width": tile, "tile_height": tile,
                "mask_blur": 8, "tile_padding": 32,
                "seam_fix_mode": "None", "seam_fix_denoise": 1.0,
                "seam_fix_width": 64, "seam_fix_mask_blur": 8, "seam_fix_padding": 16,
                "force_uniform_tiles": True, "tiled_decode": False
            }
        }
        workflow["11"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "ComfyUI_4K", "images": ["20", 0]}}
    else:
        workflow["5"] = {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": batch_size}}
        workflow["3"] = {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1,
                "model": [model_node, 0], "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        }
        workflow["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}}
        workflow["9"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}}

    return workflow


def free_memory(api_base=API_BASE):
    try:
        requests.post(f"{api_base}/free", timeout=10)
    except Exception:
        pass


def queue_prompt(workflow, api_base=API_BASE, client_id="opencode-bridge"):
    free_memory(api_base)
    data = {"prompt": workflow, "client_id": client_id}
    resp = requests.post(f"{api_base}/prompt", json=data)
    if resp.status_code != 200:
        raise RuntimeError(f"API error ({resp.status_code}): {resp.text}")
    return resp.json()["prompt_id"]


def wait_for_completion(prompt_id, api_base=API_BASE, timeout=600):
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Timed out")
        resp = requests.get(f"{api_base}/history/{prompt_id}")
        if resp.status_code != 200:
            time.sleep(1)
            continue
        history = resp.json()
        if prompt_id in history:
            return history[prompt_id].get("outputs", {})
        time.sleep(1)


def get_output_images(outputs):
    images = []
    for node_id, node_output in outputs.items():
        for output_key, output_list in node_output.items():
            for img_data in output_list:
                if isinstance(img_data, dict) and "filename" in img_data:
                    images.append(img_data)
    return images


def download_image(img_data, api_base=API_BASE, save_dir=None):
    params = {
        "filename": img_data["filename"],
        "subfolder": img_data.get("subfolder", ""),
        "type": img_data.get("type", "output")
    }
    resp = requests.get(f"{api_base}/view", params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed: {resp.status_code}")
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, img_data["filename"])
        with open(path, "wb") as f:
            f.write(resp.content)
        return path
    return resp.content


def rename_output_file(path, mode):
    import re, os
    dir_name = os.path.dirname(path)
    basename = os.path.basename(path)
    prefix = "_4K" if mode in ("4k", "4k_upscale") else ""
    m = re.match(r'^.+_4K_(\d{5})_\.png$' if prefix else r'^.+_(\d{5})_\.png$', basename)
    if not m:
        return path
    existing = [int(re.match(r'^(\d+)', f).group(1)) for f in os.listdir(dir_name)
                if re.match(r'^\d{4}(_4K)?\.png$', f)]
    next_num = (max(existing) + 1) if existing else 1
    c = str(next_num).zfill(4)
    new_name = f"{c}{prefix}.png"
    new_path = os.path.join(dir_name, new_name)
    os.rename(path, new_path)
    return new_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", "-p", required=True)
    parser.add_argument("--negative", "-n", default="")
    parser.add_argument("--model", "-m", default="anything-v5-PrtRE.safetensors")
    parser.add_argument("--steps", "-s", type=int, default=40)
    parser.add_argument("--cfg", "-c", type=float, default=7)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--api", default=API_BASE)
    parser.add_argument("--4k", action="store_true", dest="k4")
    parser.add_argument("--upscale", type=str, default=None, help="4K upscale an existing image")
    parser.add_argument("--inpaint-face", action="store_true", dest="inpaint_face")
    parser.add_argument("--source", type=str, default=None, help="Source image for inpainting")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of images to generate")
    parser.add_argument("--portrait", action="store_true", help="544x960 portrait orientation")
    parser.add_argument("--jxl", action="store_true", help="Use Juggernaut XL workflow")
    parser.add_argument("--lora", type=str, default=None, help="LORA model name (filename in models/loras/)")
    parser.add_argument("--lora-strength", type=float, default=0.85, help="LORA strength (default: 0.85)")

    args = parser.parse_args()
    if args.upscale:
        mode = "4k_upscale"
    elif args.inpaint_face:
        mode = "inpaint_face"
    elif args.k4:
        mode = "4k"
    else:
        mode = "normal"

    model_type = "sdxl" if args.jxl else "sd15"
    if args.jxl and args.model == "anything-v5-PrtRE.safetensors":
        args.model = "Juggernaut-X-RunDiffusion-NSFW.safetensors"

    actual_seed = args.seed
    if actual_seed == -1:
        actual_seed = int(time.time() * 1000) % (2**32)

    workflow = build_workflow(
        prompt=args.prompt, negative_prompt=args.negative,
        model=args.model, steps=args.steps, cfg=args.cfg,
        seed=actual_seed, batch_size=args.batch_size, mode=mode, model_type=model_type, portrait=args.portrait,
        lora_name=args.lora, lora_strength=args.lora_strength
    )

    if mode == "inpaint_face":
        src = args.source
        if not src:
            src = str(OUTPUT_DIR / "ComfyUI_4K_00003_.png")
        import shutil
        from PIL import Image
        shutil.copy2(src, str(INPUT_DIR / "inpaint_src.png"))
        # Detect source image dimensions
        with Image.open(src) as img:
            iw, ih = img.size
        # Create face mask centered in upper portion
        def face_mask(x, y, w=iw, h=ih):
            cx, cy = w // 2, int(h * 0.22)
            rx, ry = w * 0.15, h * 0.12
            dx, dy = (x - cx) / rx, (y - cy) / ry
            return 1.0 if dx * dx + dy * dy <= 1 else 0.0
        create_png_with_alpha(iw, ih, face_mask, str(INPUT_DIR / "inpaint_mask.png"))
        print(f"[Bridge] Face inpainting on: {src} ({iw}x{ih})")
    elif mode == "4k_upscale":
        import shutil
        shutil.copy2(args.upscale, str(INPUT_DIR / "upscale_src.png"))
        from PIL import Image
        with Image.open(args.upscale) as img:
            iw, ih = img.size
        print(f"[Bridge] Upscaling: {args.upscale} ({iw}x{ih}) -> 4x")
    elif mode == "4k":
        print("[Bridge] 960x544 -> 4x(AI+CN) -> 4K -> detail refine")
    print(f"[Bridge] Seed: {actual_seed}")
    print(f"[Bridge] Prompt: {args.prompt[:50]}...")

    prompt_id = queue_prompt(workflow, api_base=args.api)
    outputs = wait_for_completion(prompt_id, api_base=args.api)
    images = get_output_images(outputs)

    if not images:
        print("[Bridge] No output")
        return

    save_dir = args.output or str(OUTPUT_DIR)
    for img_data in images:
        path = download_image(img_data, api_base=args.api, save_dir=save_dir)
        path = rename_output_file(path, mode)
        print(f"[Bridge] {path}")

    print("[Bridge] Done")


if __name__ == "__main__":
    main()
