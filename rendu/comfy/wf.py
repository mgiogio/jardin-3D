# Workflow ComfyUI (format API) : Flux dev + LoRA profondeur. La profondeur de la photo fige la géométrie,
# l'image de départ garde les couleurs, le prompt change la lumière. Usage : python3 wf.py prompt denoise seed > wf.json
import json, sys
prompt, denoise, seed = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1408, 1056)
DEPTH = len(sys.argv) > 6 and sys.argv[6] == "depth"   # profondeur fournie (depth.png) au lieu de l'estimation
wf = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "fp8_e4m3fn"}},
 "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp16.safetensors", "type": "flux"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
 "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "flux1-depth-dev-lora.safetensors", "strength_model": 1.0}},
 "5": {"class_type": "LoadImage", "inputs": {"image": "scene.png"}},
 "6": {"class_type": "ImageScale", "inputs": {"image": ["5", 0], "upscale_method": "lanczos", "width": W, "height": H, "crop": "disabled"}},
 "7": {"class_type": "DepthAnythingV2Preprocessor", "inputs": {"image": ["6", 0], "ckpt_name": "depth_anything_v2_vitl.pth", "resolution": 1024}},
 "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
 "9": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["8", 0], "guidance": 10.0}},
 "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
 "11": {"class_type": "InstructPixToPixConditioning", "inputs": {"positive": ["9", 0], "negative": ["10", 0], "vae": ["3", 0], "pixels": ["7", 0]}},
 "12": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
 "13": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["11", 0], "negative": ["11", 1], "latent_image": ["12", 0],
        "seed": seed, "steps": 28, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
 "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["3", 0]}},
 "15": {"class_type": "SaveImage", "inputs": {"images": ["14", 0], "filename_prefix": "rendu"}},
 "16": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "profondeur"}},
}
if DEPTH:
    wf["20"] = {"class_type": "LoadImage", "inputs": {"image": "depth.png"}}
    wf["7"] = {"class_type": "ImageScale", "inputs": {"image": ["20", 0], "upscale_method": "lanczos", "width": W, "height": H, "crop": "disabled"}}
print(json.dumps(wf))
