from flask import Flask, request, Response, jsonify
import base64
from flask_cors import CORS
import numpy as np
import cv2
from PIL import Image
from io import BytesIO

confthres=0.5
nmsthres=0.1

app = Flask(__name__)
CORS(app)

@app.route('/dnn/yolo', methods=['POST'])
def main():
    labelsPath="./model/coco.names"
    configpath="./model/yolov3.cfg"
    weightspath="./model/yolov3.weights"
    print("[INFO] loading YOLO models...")
    LABELS = open(labelsPath).read().strip().split("\n")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath) 

    file = request.form['image']
    starter = file.find(',')
    image_data = file[starter+1:]
    image_data = bytes(image_data, encoding="ascii")
    img = Image.open(BytesIO(base64.b64decode(image_data))) 
    #img = cv2.imread('./dog.jpg')
    npimg=np.array(img)
    image=npimg.copy()
    image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    (H, W) = image.shape[:2]

    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    boxes = []
    confidences = []
    classes = []
    results = [] 

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > confthres:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classes.append({ 'id': int(classID), 'name': LABELS[classID] })

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)

    if len(idxs) > 0:
        for i in idxs.flatten():
            results.append({ 'class': classes[i], 'confidence': confidences[i], 'bbox': boxes[i] })

    return jsonify(results)

# start flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')