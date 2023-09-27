
import requests
import viz
import vizfx
import vizconnect
import vizshape
from PIL import Image, PngImagePlugin
import io 
import base64
import vizact
import vizinfo

isCAVE = False


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


def sendAPIrequest(prompt, num_steps, hiresFix):
	payload = {
		'prompt': prompt,
		'steps': num_steps,
		'enable_hr': hiresFix,
		'width': 1024,
		'height': 512,
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
	
	
	sphere = vizshape.addSphere(radius = 128, slices = 20, stacks = 20, axis = vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)




"""def onSubmit(button, state, textbox):
	if button == submitButton and state == viz.DOWN:
			sendAPIrequest(textbox.get(), 50, False)"""

def onKeyDown(key, textbox):
	if key == viz.KEY_HOME:
		sendAPIrequest(textbox.get(), 50, False)



if isCAVE:
	vizconnect.go()
	viewPoint = vizconnect.addViewpoint(pos=[0,10,0])
	viewPoint.add(vizconnect.getDisplay())
	vizconnect.resetViewpoints()
else:
	viz.go()




env = vizfx.addChild('mars test background scene.osgb')

#prompt = create_prompt(viz.input('Input Prompt: '), lora_name)



#Add an InfoPanel with a title bar
txt2imgGUI = vizinfo.InfoPanel('',title='txt2img gui menu',icon=False)

#Add prompt box
promptBox = txt2imgGUI.addLabelItem('Enter Prompt',viz.addTextbox())
txt2imgGUI.addSeparator(padding=(20,20))

#Add extra options
hires = txt2imgGUI.addLabelItem('hires fix',viz.addCheckbox(0))

txt2imgGUI.addSeparator()

#Add submit button aligned to the right
submitButton = txt2imgGUI.addItem(viz.addButtonLabel('Submit'),align=viz.ALIGN_RIGHT_CENTER)

#vizact.onbuttondown(submitButton, sendAPIrequest(promptBox.get(), 50, False))


viz.callback(viz.KEYDOWN_EVENT, onKeyDown(submitButton, promptBox))







	
	



