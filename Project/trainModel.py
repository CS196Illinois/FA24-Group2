from ultralytics import YOLO

# WARNING: To train your own model, please download a YAML + txt dataset, replace the code on line 14 accordingly
# Adjust Parameters to experiment, log results with valModel or testModel so we can improve our model
# Save model to Project/Models

# Common Error: to avoid directory errors with the dataset: In the downloaded dataset, in data.yaml - 
# Please set the paths for test, train, val to be absolute instead of relative

model = YOLO(model='yolov8n.pt')
model.info()
results = model.train(data="Project/Data/data.yaml", epochs=1, imgsz=640)