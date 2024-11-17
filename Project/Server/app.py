import json
import os
from flask import Flask, request, jsonify
import cv2
import numpy as np
from PIL import Image
import io
import base64
from flask_cors import CORS

from ultralytics import YOLO

app = Flask(__name__)
CORS(app)

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
print(dir_path)
model = YOLO(dir_path + '/Models/model1/weights/best.pt').to('cpu')

def processImage(image_bytes):
    np_img = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # Resize the image (e.g., downscale to 50% of the original size)
    #height, width = image.shape[:2]
    #new_width = width // 2
    #new_height = height // 2
    #image_resized = cv2.resize(image, (new_width, new_height))

    results = model(image)  # YOLOv8 inference
    result = results[0]

    # Draw bounding boxes and save the image (as in previous steps)
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = str(result.names[cls])

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"{label}: {conf:.2f}"
        cv2.putText(image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        roi = image[y1:y2, x1:x2]
        blurred_roi = cv2.GaussianBlur(roi, (51, 51), 0)
        image[y1:y2, x1:x2] = blurred_roi
    
    _, buffer = cv2.imencode('.jpg', image)
    img_bytes = buffer.tobytes()

    return img_bytes

def processImageBoxes(image_bytes):
    np_img = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # Resize the image (e.g., downscale to 50% of the original size)
    #height, width = image.shape[:2]
    #new_width = width // 2
    #new_height = height // 2
    #image_resized = cv2.resize(image, (new_width, new_height))

    results = model(image)  # YOLOv8 inference
    result = results[0]
#    print(result)
    boxesData = []
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = str(result.names[cls])

        boxesData.append({
            'x': x1,
            'y': y1,
            'width': x2 - x1,
            'height': y2 - y1,
            'confidence': conf,
            'label': label
        })
    return boxesData

# Endpoint to process the frame
@app.route('/process-frame', methods=['POST'])
def process_frame_endpoint():
    # Get the base64-encoded image from the request
    img_data = request.json.get('image')
    
    # Decode the base64 image
    img_bytes = base64.b64decode(img_data)
    
    # Process the image
    processed_img_bytes = processImage(img_bytes)
    
    # Return the processed image as a base64-encoded string
    return jsonify({
        'processed_image': base64.b64encode(processed_img_bytes).decode('utf-8')
    })

@app.route('/getboxes', methods=['POST'])
def getboxes():
    # Get the base64-encoded image from the request
    img_data = request.json.get('image')
    
    # Decode the base64 image
    img_bytes = base64.b64decode(img_data)
    
    # Process the image
    processed_img_boxes = processImageBoxes(img_bytes)
    
    # Return the processed image as a base64-encoded string
    return jsonify({
        'processed_boxes': processed_img_boxes
    })

if __name__ == '__main__':
    app.run(debug=True)