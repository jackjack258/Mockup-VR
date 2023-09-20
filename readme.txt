Mockup VR v0.1 Notes:

To use this app (Nvidia GPU), install Vizard and automatic1111 webui,
- put the appropriate LORA file (currently called v145.safetensors) in the webui/models/LORA folder
- Download sd_xl_base_1.0.safetensors (base model file) from https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/main
- Run automatic1111 webui  with the --api command line flag, I also use no-half and no-half-vae or it crashes
