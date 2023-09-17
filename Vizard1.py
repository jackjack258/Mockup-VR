# import the modules we need
import requests
import viz
import vizfx
import vizconnect
import vizshape
from PIL import Image, PngImagePlugin
import io # for reading the image data
import base64 # for decoding the image data

lora_name="v146"
basemodel_name=""
sampler_name='DPM++ 3M SDE Karras'
num_steps=50
hiresFix=False
width=1024
height=512



def create_prompt(str, lora_name):
	prompt = " <lora:" +lora_name+ ":1> " + "<lora:wrong:1> equirectangular " + str
	return prompt



# start the visualization
viz.go()

# load the environment model
env = vizfx.addChild('mars test background scene.osgb')

prompt = create_prompt(viz.input('Input Prompt: '), lora_name)

# create a payload with the prompt and other parameters
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
# check if the response is successful
if response.status_code == 200:
	# get the response data as a json object
	data = response.json()
	# get the image data from the response
	image_data = data['images'][0]
	# decode the image data from base64 format
	image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
	image.save('output.png')
	# convert the image object into a string of bytes
	#image_data = image.tobytes()
	# create a texture object from the image data string
	tex = viz.addTexture('output.png')
	# apply the texture to the background node of the environment model
	
else:
	# print an error message if the response is not successful
	print('Error: ', response.status_code, response.reason)
	
	
sphere = vizshape.addSphere(radius = 90, slices = 20, stacks = 20, axis = vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)


