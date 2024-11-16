import base64
import numpy as np
import torch
print(torch.cuda.is_available())


from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from ultralytics import YOLO  # Import YOLO from Ultralytics
import cv2

app = Flask(__name__)

# Load the YOLOv8 model
dir_path = os.path.dirname(os.path.realpath(__file__))
model = YOLO(dir_path + '/Models/model1/weights/best.pt').to('cpu')

# Define the upload folder path (use absolute path to avoid issues)
app.config['UPLOAD_FOLDER'] = dir_path + '/static/uploads/'
#print("This is current directoy" + os.getcwd())
#print("This is file directoy" + dir_path)

# Allowed file extensions (for security reasons)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Run OpenCV on a image, then return the annotated/blurred image
def processImage(image):
    results = model(image)  # YOLOv8 inference
    result = results[0]

    # Draw bounding boxes and save the image (as in previous steps)
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        
        conf = box.conf[0]
        cls = int(box.cls[0])
        label = result.names[cls]

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"{label}: {conf:.2f}"
        cv2.putText(image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        roi = image[y1:y2, x1:x2]
        blurred_roi = cv2.GaussianBlur(roi, (51, 51), 0)
        image[y1:y2, x1:x2] = blurred_roi

    return image

# Run to check whether a request sent by the client is valid
def validateRequest(request):
    if 'image' not in request.files:
        print("No image part in the request")
        return False
    
    file = request.files['image']

    if not file:
        print("No file selected")
        return False

    filename = file.filename

    if filename == '':
        print("No file selected")
        return False
    
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        print("Invalid extension")
        return False
    
    return True

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Run when file is uploaded
@app.route('/upload', methods=['POST'])
def upload_image():

    result = validateRequest(request)
    if not result:
        return redirect(request.url)

    file = request.files['image']
    
    # Format image to be used, without locally saving
    img_stream = file.stream.read()
    img_array = np.frombuffer(img_stream, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

#    cv2.imshow("Regular Image", img)
#    cv2.waitKey(0)
#    cv2.destroyAllWindows()

    processedImage = processImage(img)  

#    cv2.imshow("Blurred Detections", processedImage)
#    cv2.waitKey(0)
#    cv2.destroyAllWindows()

    # Convert the image to base64 (useful for returning it in HTTP response)
    _, buffer = cv2.imencode('.jpg', processedImage)
    img_base64 = base64.b64encode(buffer).decode('utf-8') # IMPORT BASE64 FOR THIS TO WORK

    return render_template('index.html', image_base64=img_base64, result = True)

@app.route('/display/<filename>')
def display_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)