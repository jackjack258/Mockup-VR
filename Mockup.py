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
import os


isCAVE = False
isInpaintMode = False
lora_name = "v26"
#basemodel_name = "juggernautXL_v9Rdphoto2Lightning"
basemodel_name = "XL45"
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


tex=viz.addTexture('output.png')  
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

def save_image(image, prompt):

    output_dir = 'outputs'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_num = 1
    while os.path.exists(os.path.join(output_dir, f'{file_num}.png')):
        file_num += 1

    image_path = os.path.join(output_dir, f'{file_num}.png')
    image.save(image_path)

    prompt_path = os.path.join(output_dir, f'{file_num}.txt')
    with open(prompt_path, 'w') as f:
        f.write(prompt)

def get_prompt_for_image(image_path):
    base_filename, _ = os.path.splitext(image_path)
    prompt_path = f'{base_filename}.txt'
    try:
        with open(prompt_path, 'r') as f:
            prompt = f.read()
    except FileNotFoundError:
        prompt = "Prompt not found."  
    prompt = prompt.replace(" <lora:v26:1> ", "")  
    return prompt
    
def update_prompt_display():
    image_paths = get_image_paths()
    if image_paths:
        current_image_path = image_paths[current_image_index]
        prompt = get_prompt_for_image(current_image_path)
        promptDisplay.message(prompt) 
    
def update_progress():
    global progressBar, sphere
    while True:
        if isLAN:
            response = requests.get(url='http://127.0.0.1:7860/sdapi/v1/progress')
        else:
            
            response = requests.get(url='http://192.168.99.14:7860/forward_progress', json=payload)
        if response.status_code == 200:
            data = response.json()
            progress = data['progress']
            if (data['current_image'] is not None):
                current_image_data = data['current_image']
                image = Image.open(io.BytesIO(base64.b64decode(current_image_data.split(",",1)[0])))
                image.save('temp.png')
                image1 = 'temp.png'
                tex.load(image1)
                sphere.texture(tex)
            progressBar.set(progress)
            if progress == 1:
                break
        else:
            print('Error: ', response.status_code, response.reason)
        yield viztask.waitTime(1)


def onInpaintSubmit():
    global startPos, endPos, imgTexture, current_image_index
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

        # Update the inpaint mode texture with the new image
        image_paths = get_image_paths()
        if image_paths:
            current_image_index = (current_image_index + 1) % len(image_paths)  # Assume new image is at the end
            new_image_path = image_paths[current_image_index]
            imgTexture.load(new_image_path)  # Update the texture
            quad.texture(imgTexture)        # Apply the updated texture to the quad

        # Do NOT exit inpaint mode
        # exitInpaintMode()
def sendInpaintAPIrequest(prompt, steps):
    global width, height, isLAN, sphere, current_image_index

    # Get the current image path from the outputs folder
    image_paths = get_image_paths()
    if not image_paths:
        print("Error: No images found in the 'outputs' folder.")
        return 

    current_image_path = image_paths[current_image_index]

    with open(current_image_path, 'rb') as img_file:
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
        response = requests.post(url='http://192.168.99.14:7860/forward_img2img', json=payload)
    
    if response.status_code == 200:
        data = response.json()
        image_data = data['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
        image.save('output.png')
        save_image(image, prompt)
        image2 = 'output.png'
        tex.load(image2)
        sphere.texture(tex)
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
        #'negative_prompt': "wrong",
        "sampler_index": sampler_name,
        'hr_scale': 1.5,
        "hr_second_pass_steps": 10,
        "hr_upscaler": "SwinIR_4x",
        "denoising_strength": 0.45,
    }
    if isLAN:
        response = requests.post(url='http://127.0.0.1:7860/sdapi/v1/txt2img', json=payload)
    else:
        response = requests.post(url='http://192.168.99.14:7860/forward_txt2img', json=payload)
    if response.status_code == 200:
        data = response.json()
        image_data = data['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",",1)[0])))
        image.save('output.png')
        image2 = 'output.png'
        tex.load(image2)
        sphere.texture(tex)
        save_image(image, prompt)
    else:
        print('Error: ', response.status_code, response.reason)


def onSubmit():
    # Create a new thread for the sendAPIrequest function
    thread = threading.Thread(target=sendAPIrequest, args=(create_prompt(promptBox.get(), lora_name), numStepsBox.get(), hires.get()))
    # Start the new thread
    thread.start()
    # Schedule the update_progress function
    viztask.schedule(update_progress())


def onInpaintButton():
    txt2imgGUI.visible(viz.OFF)
    isInpaintMode = True
    enterInpaintMode()

def createInpaintGUI():
    global inpaintPanel, inpaintPromptBox, numInpaintStepsBox
    inpaintPanel = vizinfo.InfoPanel("Inpaint Tool", icon=True)
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
    with viz.cluster.MaskedContext(viz.MASTER):
        createInpaintGUI()
    viz.mouse.setOverride(viz.ON)


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
    viz.MainWindow.visible(viz.ON)
    viz.mouse.setOverride(viz.OFF)

# Function to setup the environment for inpaint mode
def setupInpaintEnvironment():
    global quad, imgTexture, aspect_ratio, txt2imgGUI, current_image_index

    # Get the current image path from the outputs folder
    image_paths = get_image_paths()
    if not image_paths:
        print("Error: No images found in the 'outputs' folder.")
        return  

    current_image_path = image_paths[current_image_index]

    # Set the view to orthographic for 2D view
    viz.MainWindow.ortho(-aspect_ratio, aspect_ratio, -1, 1, -1, 1)
    viz.MainView.setPosition(0, 0, 0)
    viz.MainView.setEuler([.1, .1, .1])
    viz.MainWindow.visible(viz.OFF)
    with viz.cluster.MaskedContext(viz.MASTER):
        viz.MainWindow.visible(viz.ON)

    # Add a quad to display the CURRENT image
    imgTexture = viz.addTexture(current_image_path)  # Load the current image
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
        sphere = vizshape.addSphere(radius=1280, slices=20, stacks=20, axis=vizshape.AXIS_Y, lighting=False, texture=tex, flipFaces=True)
    except IOError:
        print("Error: Could not load 'output.png'.")

# Function to get a list of image paths from the 'outputs' folder
def get_image_paths():
    output_dir = 'outputs'
    image_paths = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.png'):
            image_paths.append(os.path.join(output_dir, filename))
    return sorted(image_paths)  # Sort for consistent order

# Function to load and display an image on the sphere
def load_image_on_sphere(image_path):
    global tex, sphere
    tex.load(image_path)
    sphere.texture(tex)

# Global variable to track the current image index
current_image_index = 0

# Function to handle the previous image button click
def on_previous_image():
    global current_image_index
    image_paths = get_image_paths()
    if image_paths:
        current_image_index = (current_image_index - 1) % len(image_paths)
        load_image_on_sphere(image_paths[current_image_index])
        update_prompt_display()

# Function to handle the next image button click
def on_next_image():
    global current_image_index
    image_paths = get_image_paths()
    if image_paths:
        current_image_index = (current_image_index + 1) % len(image_paths)
        load_image_on_sphere(image_paths[current_image_index])
        update_prompt_display()


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



with viz.cluster.MaskedContext(viz.MASTER):
    txt2imgGUI = vizinfo.InfoPanel('', title='Mockup VR', icon=True, fontSize=15)
    promptBox = txt2imgGUI.addLabelItem('Enter Prompt:', viz.addTextbox())
    promptBox.overflow(viz.OVERFLOW_GROW)
    promptBox.length(4)
    numStepsBox = txt2imgGUI.addLabelItem('Number of Steps', viz.addTextbox())
    seedButton = txt2imgGUI.addItem(viz.addButtonLabel('Random Seed'), align=viz.ALIGN_RIGHT_CENTER)
    progressBar = viz.addProgressBar('Progress')
    txt2imgGUI.addItem(progressBar)
    hires = txt2imgGUI.addLabelItem('double resolution (will take a long time)', viz.addCheckbox())
    submitButton = txt2imgGUI.addItem(viz.addButtonLabel('Submit'), align=viz.ALIGN_RIGHT_CENTER)
    inpaintButton = txt2imgGUI.addItem(viz.addButtonLabel('Inpaint Mode'), align=viz.ALIGN_RIGHT_CENTER)
    previous_button = txt2imgGUI.addItem(viz.addButtonLabel('< Previous'), align=viz.ALIGN_LEFT_CENTER)
    next_button = txt2imgGUI.addItem(viz.addButtonLabel('Next >'), align=viz.ALIGN_LEFT_CENTER)

    # Link buttons to their functions
    vizact.onbuttondown(previous_button, on_previous_image)
    vizact.onbuttondown(next_button, on_next_image)    
    promptDisplay = txt2imgGUI.addLabelItem('Prompt:', viz.addTextbox())  
    promptDisplay.overflow(viz.OVERFLOW_GROW)
    
    vizact.onbuttondown(submitButton, onSubmit)
    vizact.onbuttondown(inpaintButton, onInpaintButton)

    
viz.callback(viz.MOUSEDOWN_EVENT, onMouseDown)
viz.callback(viz.MOUSEUP_EVENT, onMouseUp)