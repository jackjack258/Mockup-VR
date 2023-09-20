
import requests
import viz
import vizfx
import vizconnect
import vizshape
from PIL import Image, PngImagePlugin
import io 
import base64

iscave = False

lora_name="v146"
basemodel_name=""
sampler_name='DPM++ 3M SDE Karras'
num_steps=35
hiresFix=False
width=1024
height=512



def create_prompt(str, lora_name):
	prompt = " <lora:" +lora_name+ ":1> " + "<lora:wrong:1> equirectangular " + str
	return prompt



viz.go()

env = vizfx.addChild('mars test background scene.osgb')

prompt = create_prompt(viz.input('Input Prompt: '), lora_name)

payload = {
	'prompt': prompt,
	'steps': num_steps,
	'enable_hr': hiresFix,
	'width': width,
	'height': height,
	'negative_prompt': "wrong",
	"sampler_index": sampler_name,
	
	
}
# send the request to the webui API
response = requests.post(url='http://127.0.0.1:7860/sdapi/v1/txt2img', json=payload)
if response.status_code == 200:
	data = response.json()
	image_data = data['images'][0]
	image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
	image.save('output.png')
	tex = viz.addTexture('output.png')
	
else:
	
	print('Error: ', response.status_code, response.reason)
	
	
sphere = vizshape.addSphere(radius = 200, slices = 20, stacks = 20, axis = vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)


