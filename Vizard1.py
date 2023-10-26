
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
import viztask
import threading

isCAVE = False
lora_name="v21"
basemodel_name="XL45"
sampler_name='Restart'
num_steps=35
hiresFix=False
width=1408
height=704

ALMOST_ZERO=0.000001
class MyDtrackManager():
	def __init__(self, default_head_pos=[0,1,0]):
		self.default_head_pos = default_head_pos
		self.wrapped_tracker = None
		self.raw_vrpn = None
		self.dtrack_updater = None
					
	def startDefaultHeadPosition(self):
		self.wrapped_tracker = vizconnect.getTracker("dtrack_head")
		self.raw_vrpn = self.wrapped_tracker.getRaw()
		
		fakeTracker = viz.addGroup()
		fakeTracker.setPosition(self.default_head_pos)
		self.wrapped_tracker.setRaw(fakeTracker)
		
		#This calls check_dtrack each frame
		self.dtrack_updater = vizact.onupdate(0, self.check_dtrack)
	
	def check_dtrack(self):
		x, y, z = self.raw_vrpn.getPosition()
		atOrigin = self.isAlmostZero(x) or self.isAlmostZero(y) or self.isAlmostZero(z)
		
		if not atOrigin:
			self.wrapped_tracker.setRaw(self.raw_vrpn)
			self.dtrack_updater.remove()
	
	#Will move to other library
	def isAlmostZero(self, val):
		if abs(val) <= ALMOST_ZERO:
			return True
		else:
			return False

sphere = None

def create_prompt(str, lora_name):
	prompt = " <lora:" +lora_name+ ":1> " + "<lora:wrong:1> equirectangular " + str
	return prompt


def update_progress():
    global progressBar  
    while True:
        response = requests.get(url='http://127.0.0.1:7860/sdapi/v1/progress')
        if response.status_code == 200:
            data = response.json()
            progress = data['progress']  
            progressBar.set(progress)  
            if progress == 1:  
                break  
        else:
            print('Error: ', response.status_code, response.reason)
        yield viztask.waitTime(1)  


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
        'hr_scale': 2,
        "hr_second_pass_steps": 10,
        "hr_upscaler": "SwinIR_4x",
        "denoising_strength": 0.5,
    }
    #response = requests.post(url='http://192.168.99.14:7860/forward', json=payload)
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
        hiresFix = bool(hires.get())  
        threading.Thread(target=sendAPIrequest, args=(create_prompt(promptBox.get(), lora_name), num_steps, hiresFix)).start()
        viztask.schedule(update_progress())  # Schedule the update_progress coroutine


if isCAVE:
    CONFIG_FILE = "E:\\VizardProjects\\_CaveConfigFiles\\vizconnect_config_CaveFloor+ART_headnode.py"
    vizconnect.go(CONFIG_FILE)
    viewPoint = vizconnect.addViewpoint(pos=[0,10,0])
    #viewPoint.add(vizconnect.getDisplay())
    #vizconnect.resetViewpoints()
    dtrack_manager = MyDtrackManager()
    dtrack_manager.startDefaultHeadPosition()
else:
    viz.go()
    viz.fov(100)

env = vizfx.addChild('mars test background scene.osgb')
progressBar = None

txt2imgGUI = vizinfo.InfoPanel('',title='txt2img gui menu',icon=False,)

promptBox = txt2imgGUI.addLabelItem('Enter Prompt',viz.addTextbox())
promptBox.length(6)
txt2imgGUI.addSeparator(padding=(20,20))
numStepsBox = txt2imgGUI.addLabelItem('Number of Steps', viz.addTextbox())
txt2imgGUI.addSeparator(padding=(20,20))
progressBar = viz.addProgressBar('Progress')
txt2imgGUI.addItem(progressBar)

hires = txt2imgGUI.addLabelItem('hires fix', viz.addCheckbox())


txt2imgGUI.addSeparator(padding=(20,20))

submitButton = txt2imgGUI.addItem(viz.addButtonLabel('Submit'),align=viz.ALIGN_RIGHT_CENTER)

vizact.onbuttondown(submitButton, lambda: onSubmit(submitButton, viz.DOWN))