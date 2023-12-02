import viz
import vizshape
import vizinfo
import vizact
import vizconnect
from PIL import Image, ImageDraw
import io
import base64
import requests
import threading
import numpy as np
import vizfx
from MyUtils import *
import viztask


isCAVE = False
isInpaintMode = False
lora_name = "v26"
basemodel_name = "juggernautXL_version6Rundiffusion"
sampler_name = 'DPM++ 3M SDE Karras'
num_steps = 35
hiresFix = False
width = 1408
height = 704
seed = np.random.randint(0, 1000000000)
isLAN = True
ALMOST_ZERO = 0.000001
sphere = None
quad = None
startPos = None
endPos = None
selectionBox = []
imgTexture = None
aspect_ratio = 2



class MyDtrackManager():
    def __init__(self, default_head_pos=[0, 1, 0]):
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

        self.dtrack_updater = vizact.onupdate(0, self.check_dtrack)

    def check_dtrack(self):
        x, y, z = self.raw_vrpn.getPosition()
        atOrigin = self.isAlmostZero(x) or self.isAlmostZero(y) or self.isAlmostZero(z)

        if not atOrigin:
            self.wrapped_tracker.setRaw(self.raw_vrpn)
            self.dtrack_updater.remove()

    def isAlmostZero(self, val):
        return abs(val) <= ALMOST_ZERO


def create_prompt(str, lora_name):
    prompt = " <lora:" + lora_name + ":1> " + "an equirectangular " + str
    return prompt
    
def create_inpaint_prompt(str, lora_name):
    return "an equirectangular " + str


def update_progress():
    global progressBar, sphere
    while True:
        if isLAN:
            response = requests.get(url='http://127.0.0.1:7860/sdapi/v1/progress')
        else:
            
            pass
        if response.status_code == 200:
            data = response.json()
            progress = data['progress']
            if (data['current_image'] is not None):
                current_image_data = data['current_image']
                image = Image.open(io.BytesIO(base64.b64decode(current_image_data.split(",",1)[0])))
                image.save('temp.png')
                tex = viz.addTexture('temp.png')
                if sphere is not None:
                    sphere.remove()
                sphere = vizshape.addSphere(radius=128, slices=20, stacks=20, axis=vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
            progressBar.set(progress)
            if progress == 1:
                break
        else:
            print('Error: ', response.status_code, response.reason)
        yield viztask.waitTime(1)


def onInpaintSubmit():
    global startPos, endPos, imgTexture
    if startPos and endPos and imgTexture:
        # Convert selection box coordinates to image pixels and save mask
        minX, maxX = sorted([int((startPos[0] + aspect_ratio) * width / (2 * aspect_ratio)), 
                             int((endPos[0] + aspect_ratio) * width / (2 * aspect_ratio))])
        minY, maxY = sorted([int((1 - startPos[1]) * height / 2), 
                             int((1 - endPos[1]) * height / 2)])

        # Create and save the mask (inverted)
        # Start with a black image (color=0)
        mask = Image.new('L', (width, height), color=0)
        mask.paste(255, [minX, minY, maxX, maxY])
        mask.save('mask.png')

        # Call InpaintAPI function (to be implemented)
        inpaintPrompt = inpaintPromptBox.get()
        numInpaintSteps = int(numInpaintStepsBox.get())
        sendInpaintAPIrequest(inpaintPrompt, numInpaintSteps)

        # Exit inpaint mode after submitting
        exitInpaintMode()

def sendInpaintAPIrequest(prompt, steps):
    global width, height, isLAN, sphere
    with open('output.png', 'rb') as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    with open('mask.png', 'rb') as mask_file:
        mask_base64 = base64.b64encode(mask_file.read()).decode('utf-8')

    payload = {
        'init_images': [img_base64],
        'prompt': create_inpaint_prompt(prompt, lora_name),
        'steps': steps,
        'width': width,
        'height': height,
        'mask': mask_base64,
        'mask_blur': 32,
        "sampler_index": sampler_name,
        'denoising_strength': .75,
        'inpainting_fill': 0,
     }

    if isLAN:
        response = requests.post(url='http://127.0.0.1:7860/sdapi/v1/img2img', json=payload)
    else:
        response = requests.post(url='http://192.168.99.14:7860/forward', json=payload)
    
    if response.status_code == 200:
        data = response.json()
        image_data = data['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
        image.save('output.png')
        tex = viz.addTexture('output.png')
        if sphere is not None:
            sphere.remove()
        sphere = vizshape.addSphere(radius=128, slices=20, stacks=20, axis=vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
    else:
        print('Error: ', response.status_code, response.reason)


# Function to send API request
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
        'hr_scale': 1.5,
        "hr_second_pass_steps": 10,
        "hr_upscaler": "SwinIR_4x",
        "denoising_strength": 0.45,
    }
    if isLAN:
        response = requests.post(url='http://127.0.0.1:7860/sdapi/v1/txt2img', json=payload)
    else:
        response = requests.post(url='http://192.168.99.14:7860/forward', json=payload)
    if response.status_code == 200:
        data = response.json()
        image_data = data['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
        image.save('output.png')
        tex = viz.addTexture('output.png')
        if sphere is not None:
            sphere.remove()
        sphere = vizshape.addSphere(radius=128, slices=20, stacks=20, axis=vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
    else:
        print('Error: ', response.status_code, response.reason)


def onSubmit(button, state):
    global seed, txt2imgGUI, isInpaintMode
    if button == submitButton and state == viz.DOWN:
        num_steps = int(numStepsBox.get())
        hiresFix = bool(hires.get())
        threading.Thread(target=sendAPIrequest, args=(create_prompt(promptBox.get(), lora_name), num_steps, hiresFix)).start()
        viztask.schedule(update_progress())

    if button == seedButton and state == viz.DOWN:
        seed = np.random.randint(0, 1000000000)
        txt2imgGUI.setTitle('seed: ' + str(seed))

    if button == inpaintButton and state == viz.DOWN:
        isInpaintMode = True
        enterInpaintMode()

def createInpaintGUI():
    global inpaintPanel, inpaintPromptBox, numInpaintStepsBox
    inpaintPanel = vizinfo.InfoPanel("Inpaint Tool", align=viz.ALIGN_CENTER, icon=False)
    inpaintPromptBox = inpaintPanel.addLabelItem('Enter Inpaint Prompt', viz.addTextbox())
    inpaintPromptBox.overflow(viz.OVERFLOW_GROW)
    numInpaintStepsBox = inpaintPanel.addLabelItem('Number of Inpaint Steps', viz.addTextbox())
    submitInpaintButton = inpaintPanel.addItem(viz.addButtonLabel('Submit'), align=viz.ALIGN_CENTER)
    exitInpaintButton = inpaintPanel.addItem(viz.addButtonLabel('Exit Inpaint Mode'), align=viz.ALIGN_CENTER)

    # Link buttons to their functions
    vizact.onbuttondown(submitInpaintButton, onInpaintSubmit)
    vizact.onbuttondown(exitInpaintButton, exitInpaintMode)

def enterInpaintMode():
    global isInpaintMode, sphere, quad, imgTexture, inpaintPanel, txt2imgGUI
    isInpaintMode = True
    if sphere:
        sphere.visible(viz.OFF)
    setupInpaintEnvironment()
    createInpaintGUI()
    viz.mouse.setOverride(viz.ON)
    txt2imgGUI.visible(viz.OFF)  # Hide the main GUI


def exitInpaintMode():
    global isInpaintMode, sphere, quad, inpaintPanel, txt2imgGUI
    isInpaintMode = False
    if sphere:
        sphere.visible(viz.ON)
    if quad:
        quad.remove()
        quad = None
    if inpaintPanel:
        inpaintPanel.remove()  # Remove the inpaint GUI
        inpaintPanel = None
    txt2imgGUI.visible(viz.ON)  # Show the main GUI again
    viz.MainWindow.fov(100)
    viz.mouse.setOverride(viz.OFF)

# Function to setup the environment for inpaint mode
def setupInpaintEnvironment():
    global quad, imgTexture, aspect_ratio
    # Set the view to orthographic for 2D view
    viz.MainWindow.ortho(-aspect_ratio, aspect_ratio, -1, 1, -1, 1)
    viz.MainView.setPosition(0, 0, 0)
    viz.MainView.setEuler([.1, .1, .1])
    # Add a quad to display the image
    imgTexture = viz.addTexture('output.png')
    quad = viz.addTexQuad(size=[aspect_ratio*2, 2])
    quad.setPosition(0, 0, 0)
    quad.texture(imgTexture)
    viz.mouse.setOverride(viz.OFF)


 # Function to handle mouse events for inpaint mode
def updateSelectionBox():
    global selectionBox, startPos, endPos
    for line in selectionBox:
        line.remove()
    selectionBox = []  

    if startPos and endPos:
        # Define min and max coordinates
        minX = min(startPos[0], endPos[0])
        maxX = max(startPos[0], endPos[0])
        minY = min(startPos[1], endPos[1])
        maxY = max(startPos[1], endPos[1])

        # Define the corners of the rectangle
        corners = [(minX, minY, 0), (maxX, minY, 0), (maxX, maxY, 0), (minX, maxY, 0), (minX, minY, 0)]

        # Iterate through the corners to draw lines between them
        for i in range(len(corners) - 1):
            line = drawLine(corners[i], corners[i + 1], lineWidth=10, color=viz.RED)
            selectionBox.append(line)

# Mouse event handlers
def onMouseDown(button):
    global startPos, isInpaintMode
    if isInpaintMode and button == viz.MOUSEBUTTON_LEFT:
        windowPos = viz.mouse.getPosition()
        startPos = ((windowPos[0] * 2 * aspect_ratio) - aspect_ratio,
                    (windowPos[1] * 2 - 1))

def onMouseUp(button):
    global endPos, isInpaintMode
    if isInpaintMode and button == viz.MOUSEBUTTON_LEFT:
        windowPos = viz.mouse.getPosition()
        endPos = ((windowPos[0] * 2 * aspect_ratio) - aspect_ratio,
                  (windowPos[1] * 2 - 1))
        updateSelectionBox()

def loadDefaultSphereTexture():
    global sphere
    try:
        tex = viz.addTexture('output.png')
        if sphere is not None:
            sphere.remove()
        sphere = vizshape.addSphere(radius=128, slices=20, stacks=20, axis=vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
    except IOError:
        print("Error: Could not load 'output.png'.")




viz.callback(viz.MOUSEDOWN_EVENT, onMouseDown)
viz.callback(viz.MOUSEUP_EVENT, onMouseUp)

# Initialize the Vizard environment
if isCAVE:
    CONFIG_FILE = "E:\\VizardProjects\\_CaveConfigFiles\\vizconnect_config_CaveFloor+ART_headnode.py"
    vizconnect.go(CONFIG_FILE)
    viewPoint = vizconnect.addViewpoint(pos=[0, 10, 0])
    dtrack_manager = MyDtrackManager()
    dtrack_manager.startDefaultHeadPosition()
else:
    viz.go()
    viz.fov(100)

loadDefaultSphereTexture()
progressBar = None

# Setup the main GUI
txt2imgGUI = vizinfo.InfoPanel('', title='txt2img gui menu', icon=False)
promptBox = txt2imgGUI.addLabelItem('Enter Prompt', viz.addTextbox())
promptBox.length(6)
promptBox.overflow(viz.OVERFLOW_GROW)
txt2imgGUI.addSeparator(padding=(20, 20))
numStepsBox = txt2imgGUI.addLabelItem('Number of Steps', viz.addTextbox())
txt2imgGUI.addSeparator(padding=(20, 20))
seedBox = txt2imgGUI.addLabelItem('Seed: ' + str(seed), viz.addTextbox())
seedButton = txt2imgGUI.addItem(viz.addButtonLabel('Randomize'), align=viz.ALIGN_RIGHT_CENTER)
txt2imgGUI.addSeparator(padding=(20, 20))
progressBar = viz.addProgressBar('Progress')
txt2imgGUI.addItem(progressBar)
hires = txt2imgGUI.addLabelItem('hires fix', viz.addCheckbox())
txt2imgGUI.addSeparator(padding=(20, 20))
submitButton = txt2imgGUI.addItem(viz.addButtonLabel('Submit'), align=viz.ALIGN_RIGHT_CENTER)
inpaintButton = txt2imgGUI.addItem(viz.addButtonLabel('Inpaint Mode'), align=viz.ALIGN_RIGHT_CENTER)
vizact.onbuttondown(submitButton, lambda: onSubmit(submitButton, viz.DOWN))
vizact.onbuttondown(seedButton, lambda: onSubmit(seedButton, viz.DOWN))
vizact.onbuttondown(inpaintButton, lambda: onSubmit(inpaintButton, viz.DOWN))
