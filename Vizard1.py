﻿import requests
import viz
import vizfx
import vizconnect
import vizshape
from PIL import Image, PngImagePlugin
import io 
import base64
import vizact
import vizinfo
import viztask

isCAVE = False

lora_name="v18"
basemodel_name=""
sampler_name='DPM++ 3M SDE Karras'
num_steps=35
hiresFix=False
width=1448
height=724

sphere = None

def create_prompt(str, lora_name):
	prompt = " <lora:" +lora_name+ ":1> " + "<lora:wrong:1> equirectangular " + str
	return prompt

def sendAPIrequest(prompt, num_steps, hiresFix):
    global sphere
    payload = {
        'prompt': prompt,
        'steps': num_steps,
        'enable_hr': hiresFix,
        'width': width,
        'height': height,
        'negative_prompt': "wrong",
        "sampler_index": sampler_name,
    }
    response = requests.post(url='http://127.0.0.1:7860/sdapi/v1/txt2img', json=payload)
    if response.status_code == 200:
        data = response.json()
        image_data = data['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
        image.save('output.png')
        tex = viz.addTexture('output.png')
        if sphere is not None:
            sphere.remove()
        sphere = vizshape.addSphere(radius = 128, slices = 20, stacks = 20, axis = vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
    else:
        print('Error: ', response.status_code, response.reason)


def onSubmit(button, state):
    if button == submitButton and state == viz.DOWN:
        num_steps = int(numStepsBox.get())
        hiresFix = bool(hires.get())  # Get the state of the checkbox
        sendAPIrequest(create_prompt(promptBox.get(), lora_name), num_steps, hiresFix)

if isCAVE:
	vizconnect.go()
	viewPoint = vizconnect.addViewpoint(pos=[0,10,0])
	viewPoint.add(vizconnect.getDisplay())
	vizconnect.resetViewpoints()
else:
    viz.go()
    viz.fov(100)

env = vizfx.addChild('mars test background scene.osgb')

txt2imgGUI = vizinfo.InfoPanel('',title='txt2img gui menu',icon=False)

promptBox = txt2imgGUI.addLabelItem('Enter Prompt',viz.addTextbox())
txt2imgGUI.addSeparator(padding=(20,20))
numStepsBox = txt2imgGUI.addLabelItem('Number of Steps', viz.addTextbox())
txt2imgGUI.addSeparator(padding=(20,20))

hires = txt2imgGUI.addLabelItem('hires fix', viz.addCheckbox())


txt2imgGUI.addSeparator(padding=(20,20))

submitButton = txt2imgGUI.addItem(viz.addButtonLabel('Submit'),align=viz.ALIGN_RIGHT_CENTER)

vizact.onbuttondown(submitButton, lambda: onSubmit(submitButton, viz.DOWN))
