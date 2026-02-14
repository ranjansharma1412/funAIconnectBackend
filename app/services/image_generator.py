
import torch
from diffusers import FluxPipeline
import os

class ImageGenerator:
    _instance = None
    _pipeline = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageGenerator, cls).__new__(cls)
            # cls._instance._load_model() # Disabled automatic loading to save resources
        return cls._instance

    def _load_model(self):
        print("Loading FLUX.1-schnell model...")
        model_id = "black-forest-labs/FLUX.1-schnell"
        
        # Determine device
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {device}")

        try:
            # Attempt to load with 4-bit quantization if possible (mainly for CUDA)
            # For MPS, 4-bit support via bitsandbytes is experimental/limited.
            # We'll try standard loading with optimization if 4-bit fails or isn't appropriate for MPS yet.
            
            # Note: 4-bit quantization usually requires bitsandbytes which has limited MPS support.
            # We will use bfloat16 for MPS as it is generally supported and efficient.
            
            dtype = torch.bfloat16
            
            self._pipeline = FluxPipeline.from_pretrained(
                model_id,
                torch_dtype=dtype
            )
            
            # Use model offloading for MPS as sequential offloading can be unstable
            if device == "mps":
                self._pipeline.enable_model_cpu_offload()
            else:
                self._pipeline.enable_sequential_cpu_offload() # Save VRAM
            
            # self._pipeline.to(device) # enable_model_cpu_offload/sequential handles device placement

            print("FLUX.1-schnell model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e

    def generate_image(self, prompt, num_inference_steps=4, guidance_scale=0.0):
        if not self._pipeline:
            # self._load_model() # Do not auto-load
            raise RuntimeError("Model FLUX.1-schnell is not loaded. Please configure a model to generate images.")
        
        print(f"Generating image for prompt: {prompt}")
        image = self._pipeline(
            prompt,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            max_sequence_length=256
        ).images[0]
        
        return image
