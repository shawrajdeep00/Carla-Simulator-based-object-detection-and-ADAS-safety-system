# Carla-Simulator-based-object-detection-and-ADAS-safety-system


This repository contains the final implementation of an Advanced Driver Assistance System (ADAS) for the Hochschule Hamm-Lippstadt CARLA student lab. The system runs in parallel with a human driver in the CARLA simulator and provides traffic-light detection, pedestrian detection, vehicle detection, warning messages, and limited safety interventions.

The final solution uses a custom-trained YOLOv8 object detection model trained on both a public CARLA dataset and lab-collected CARLA data. The trained model is deployed inside `solution/my_adas.py` and loaded from `solution/best.pt`.

---

## Project Objective

The goal of this project was to build an ADAS module that can assist a human driver inside the CARLA simulator.

The ADAS system must:

- Process live camera frames from the CARLA simulation.
- Detect traffic lights.
- Detect pedestrians.
- Detect vehicles.
- Notify the driver about important road situations.
- Intervene only when necessary by returning throttle, brake, and steering commands.
- Follow the structure required by the HSHL ADAS framework.

The final implementation focuses on safe and conservative intervention. The system avoids unnecessary takeover and only applies braking when a high-confidence hazard is detected.

---

## Final Submitted Files

The important final submitted files are:

```text
solution/
├── my_adas.py
└── best.pt

requirements.txt
```

### File Descriptions

| File | Purpose |
|---|---|
| `solution/my_adas.py` | Main ADAS implementation required by the lab framework |
| `solution/best.pt` | Final trained YOLOv8 model weights |
| `requirements.txt` | Python dependency file containing `ultralytics` |
| `CARLA_PROJECT_MECHATRONICS_BLOCK_WEEK.ipynb` | Notebook used for dataset preparation, merging, training, evaluation, and comparison |

---

## Repository Structure

```text
HSHL-ADAS-Team-8-ADAS_start/
│
├── adas/
│   ├── __init__.py
│   ├── interface.py
│   ├── topics.py
│   └── viewer.py
│
├── dev_tools/
│   ├── control_logger/
│   ├── README.md
│   ├── play_bag.sh
│   └── start_ros_node.sh
│
├── solution/
│   ├── __init__.py
│   ├── best.pt
│   └── my_adas.py
│
├── tests/
│   ├── __init__.py
│   ├── test_interface.py
│   ├── test_my_adas.py
│   └── validate_bag.py
│
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── session_bag.md
└── README.md
```

---

## System Overview

The ADAS system runs as a ROS-based CARLA module.

A human driver controls the vehicle manually, while `MyADAS` runs in the background and receives:

- Camera frames
- Speed updates

The ADAS module performs the following loop:

```text
Camera frame
    |
    |--> detect_traffic_light(image)
    |
    |--> detect_objects(image)
    |
    |--> annotated frame shown in browser viewer

Speed update
    |
    |--> compute_control(speed_kmh)
            |
            |--> return None if no intervention is needed
            |
            |--> return (throttle, brake, steer) if intervention is needed
```

The live viewer is available at:

```text
http://localhost:8080
```

---

## Dataset Used

Two datasets were used.

### 1. Public CARLA Kaggle Dataset

The public CARLA object detection dataset was downloaded from Kaggle:

```text
ibrahimalobaid/object-detection-carla-self-driving-car
```

The notebook prepared this dataset into a clean YOLO structure.

The prepared Kaggle dataset contained:

| Split | Images | Label Files | Object Lines |
|---|---:|---:|---:|
| Train | 1120 | 1120 | 2028 |
| Validation | 320 | 320 | 557 |
| Test | 160 | 160 | 292 |

### 2. Lab-Collected Dataset

A second dataset was collected in the lab using CARLA data. This lab dataset was exported in YOLO format and normalized to match the same class order as the Kaggle dataset.

The lab dataset contained:

| Split | Images |
|---|---:|
| Train | 167 |
| Validation | 33 |
| Test | 22 |

### 3. Final Merged Dataset

The final model was trained using both datasets.

Merged dataset counts:

| Source | Split | Images |
|---|---|---:|
| Kaggle | Train | 1120 |
| Kaggle | Validation | 320 |
| Kaggle | Test | 160 |
| Lab | Train | 167 |
| Lab | Validation | 33 |
| Lab | Test | 22 |

Total merged split sizes:

| Split | Images |
|---|---:|
| Train | 1287 |
| Validation | 353 |
| Test | 182 |

---

## Class Labels

The final dataset used 10 classes.

```text
0: bike
1: motobike
2: person
3: traffic_light_green
4: traffic_light_orange
5: traffic_light_red
6: traffic_sign_30
7: traffic_sign_60
8: traffic_sign_90
9: vehicle
```

The most important classes for the ADAS behavior are:

- `person`
- `vehicle`
- `traffic_light_green`
- `traffic_light_orange`
- `traffic_light_red`

The traffic sign classes are included in the trained detector because they are present in the dataset, but the final ADAS control logic mainly uses traffic lights, pedestrians, and vehicles.

---

## Dataset Preparation

The notebook performs the following dataset preparation steps:

1. Downloads the Kaggle CARLA dataset.
2. Inspects the dataset folder structure.
3. Finds image and label folders automatically.
4. Converts the dataset into a clean YOLO format.
5. Uploads the lab-collected YOLO dataset ZIP.
6. Extracts the lab dataset safely.
7. Fixes Windows-style ZIP paths.
8. Merges the Kaggle and lab datasets into one YOLO dataset.
9. Writes a new merged `data.yaml`.

The Windows path fix is important because the lab dataset ZIP contained backslashes in file paths. Colab expects Linux-style paths, so the paths were normalized using:

```python
fixed_name = member.filename.replace("\\", "/")
```

Without this fix, Colab extracted files incorrectly and could not locate `data.yaml`.

---

## YOLO Dataset Structure

The final merged dataset follows the YOLO format:

```text
hshl_carla_plus_lab_yolo/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml
```

The merged `data.yaml` points YOLO to the correct image folders and class names:

```yaml
train: /content/hshl_carla_plus_lab_yolo/train/images
val: /content/hshl_carla_plus_lab_yolo/valid/images
test: /content/hshl_carla_plus_lab_yolo/test/images
nc: 10
names:
- bike
- motobike
- person
- traffic_light_green
- traffic_light_orange
- traffic_light_red
- traffic_sign_30
- traffic_sign_60
- traffic_sign_90
- vehicle
```

---

## Why YOLOv8 Was Used

YOLOv8 was selected because this project requires real-time object detection for ADAS.

The reasons for using YOLOv8 were:

- It is suitable for real-time inference.
- It provides a strong speed-accuracy tradeoff.
- It supports custom training with YOLO-format datasets.
- It produces `.pt` weights that can be loaded directly in Python.
- It integrates easily into `my_adas.py` through the Ultralytics API.
- It supports transfer learning, which is important because the lab dataset was relatively small.
- It provides multiple model sizes, allowing comparison between `YOLOv8n`, `YOLOv8s`, and `YOLOv8m`.

Other models such as Faster R-CNN, SSD, and DETR were possible, but they were less practical for this lab setup. Faster R-CNN and DETR are heavier and slower, while SSD is older and generally less competitive than modern YOLO models.

---

## Ultralytics

The project uses the `ultralytics` Python package.

Ultralytics provides the implementation and training/inference interface for YOLOv8.

Example usage:

```python
from ultralytics import YOLO

model = YOLO("solution/best.pt")
results = model(image)
```

In this project:

- YOLOv8 is the object detection model.
- Ultralytics is the Python library used to train and run YOLOv8.
- `best.pt` is the final trained model file.

---

## Final YOLO Training Configuration

The final model was trained using YOLOv8 nano:

```python
BASE_MODEL = "yolov8n.pt"
EPOCHS = 60
IMG_SIZE = 640
BATCH_SIZE = 16
```

The training used the merged Kaggle + lab dataset.

The model was trained in Google Colab using a Tesla T4 GPU.

Training environment from the notebook:

```text
Ultralytics 8.4.52
Python 3.12.13
PyTorch 2.10.0+cu128
GPU: Tesla T4
```

---

## Augmentation Strategy

The final training used mosaic and scale augmentation.

```python
mosaic=1.0
close_mosaic=10
scale=0.50
```

### Mosaic Augmentation

Mosaic augmentation combines multiple training images into one synthetic training image. This helps the model learn from objects at different positions, sizes, and contexts.

This is useful for CARLA ADAS because objects like traffic lights and vehicles may appear small, distant, or partially visible.

### Scale Augmentation

Scale augmentation randomly resizes images during training. This helps the model generalize to objects appearing at different distances.

This is important because a vehicle or traffic light may appear very small when far away and very large when close.

### Close Mosaic

```python
close_mosaic=10
```

This disables mosaic during the last 10 epochs. Mosaic is useful for generalization early in training, but disabling it near the end helps the model stabilize bounding boxes on normal images.

---

## Final Model Performance

The final 60-epoch YOLOv8n model achieved the following validation results on the merged validation set:

| Metric | Value |
|---|---:|
| Precision | 0.947 |
| Recall | 0.874 |
| mAP50 | 0.933 |
| mAP50-95 | 0.697 |

The final model file was saved as:

```text
solution/best.pt
```

The file size is approximately:

```text
6.25 MB
```

This small size is suitable for deployment inside the CARLA ADAS repository.

---

## Class-Wise Final Model Results

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| bike | 29 | 29 | 0.960 | 0.826 | 0.912 | 0.620 |
| motobike | 27 | 27 | 0.843 | 0.963 | 0.956 | 0.737 |
| person | 65 | 72 | 1.000 | 0.972 | 0.993 | 0.731 |
| traffic_light_green | 64 | 69 | 1.000 | 0.874 | 0.972 | 0.603 |
| traffic_light_orange | 26 | 30 | 0.955 | 0.712 | 0.915 | 0.520 |
| traffic_light_red | 68 | 78 | 0.927 | 0.731 | 0.825 | 0.637 |
| traffic_sign_30 | 50 | 50 | 0.970 | 0.980 | 0.992 | 0.829 |
| traffic_sign_60 | 36 | 36 | 0.967 | 0.972 | 0.982 | 0.805 |
| traffic_sign_90 | 9 | 9 | 0.956 | 0.889 | 0.885 | 0.788 |
| vehicle | 149 | 243 | 0.892 | 0.816 | 0.893 | 0.702 |

The strongest results were achieved for:

- `person`
- `traffic_light_green`
- `traffic_sign_30`
- `traffic_sign_60`
- `vehicle`

The lower recall for red/orange traffic lights is expected because traffic lights are small and sometimes visually ambiguous in CARLA scenes.

---

## YOLOv8 Model Comparison

A comparative analysis was performed between three YOLOv8 model sizes:

- YOLOv8n
- YOLOv8s
- YOLOv8m

Each model was trained for 10 epochs on the merged dataset using the same augmentation settings.

### Comparison Results

| Model | Precision | Recall | mAP50 | mAP50-95 | Approx FPS | Size MB | Training Time Min |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLOv8n | 0.8707 | 0.7870 | 0.8512 | 0.6108 | 101.85 | 5.96 | 5.09 |
| YOLOv8s | 0.9070 | 0.8411 | 0.8940 | 0.6240 | 61.00 | 21.48 | 6.21 |
| YOLOv8m | 0.8851 | 0.8680 | 0.8895 | 0.6510 | 30.65 | 49.62 | 12.21 |

### ADAS Decision Score

A weighted score was used to select the most suitable model for ADAS:

```text
ADAS score = 0.45 * normalized_mAP50-95
           + 0.35 * normalized_recall
           + 0.20 * normalized_FPS
```

The resulting scores were:

| Model | ADAS Score |
|---|---:|
| YOLOv8n | 0.9396 |
| YOLOv8s | 0.8903 |
| YOLOv8m | 0.8602 |

Although YOLOv8m achieved the highest mAP50-95 in the short comparison, YOLOv8n was selected because it provides the best balance of accuracy, recall, speed, and model size for real-time ADAS.

The final submitted model therefore uses YOLOv8n.

---

## ADAS Implementation

The main implementation is in:

```text
solution/my_adas.py
```

The class implemented is:

```python
class MyADAS(CarlaADASInterface):
```

The HSHL framework expects three main functions:

```python
detect_traffic_light(image)
detect_objects(image)
compute_control(speed_kmh)
```

---

## Model Loading

The ADAS code loads the trained YOLO model from the solution folder.

The model search order is:

```python
solution/best.pt
solution/weights/best.pt
best.pt
```

In the submitted repository, the final model is placed at:

```text
solution/best.pt
```

The model is loaded using:

```python
from ultralytics import YOLO

self._yolo = YOLO(str(model_path))
```

---

## YOLO Inference Settings

The implementation runs YOLO with:

```python
conf=0.45
iou=0.45
```

This means detections below 45 percent confidence are ignored during raw model inference.

Further class-specific thresholds are then applied in the ADAS logic.

---

## Detection Thresholds

The following thresholds are used:

| Detection Type | Threshold |
|---|---:|
| Traffic light | 0.75 |
| Pedestrian | 0.70 |
| Vehicle | 0.50 |

These thresholds were chosen to reduce false detections, especially false red-light or pedestrian braking.

False positive braking is dangerous and disruptive in an ADAS system. Therefore, the implementation is intentionally conservative.

---

## Traffic Light Detection

Traffic light detection is implemented in:

```python
detect_traffic_light(image)
```

The function uses two methods:

1. HSV color processing in the upper part of the image.
2. YOLO detection for traffic-light classes.

The HSV color masks are calculated for:

- red
- yellow
- green

However, the final traffic light decision is only trusted if YOLO detects a valid traffic light with confidence greater than or equal to `0.75`.

This avoids detecting random red, yellow, or green objects as traffic lights.

### Traffic Light Filtering

The implementation rejects invalid traffic-light boxes if:

- The box is too low in the image.
- The box is too large to realistically be a traffic light.

This helps prevent false detections from large colored objects.

The traffic-light return value has the structure:

```python
{
    "state": "red" | "yellow" | "green" | "unknown",
    "annotated": image,
    "counts": counts,
    "confidence": confidence,
    "source": source
}
```

---

## Object Detection

Object detection is implemented in:

```python
detect_objects(image)
```

The function returns:

```python
{
    "pedestrians": [...],
    "vehicles": [...],
    "annotated": image
}
```

### Pedestrian Detection

A detection is treated as a pedestrian if the class name contains:

```text
person
pedestrian
```

Pedestrian detections require confidence at least:

```text
0.70
```

### Vehicle Detection

A detection is treated as a vehicle if the class name contains:

```text
vehicle
car
truck
bus
motorbike
motobike
motorcycle
bike
```

Vehicle detections require confidence at least:

```text
0.50
```

Traffic lights and traffic signs are explicitly excluded from vehicle detection.

---

## Control Logic

Control decisions are implemented in:

```python
compute_control(speed_kmh)
```

This function decides whether to:

- Return `None`, meaning the human driver remains in control.
- Return `(throttle, brake, steer)`, meaning ADAS temporarily intervenes.

The function never returns throttle and brake at the same time.

---

## Intervention Rules

### Pedestrian Ahead

If a pedestrian is detected:

```python
return (0.0, 1.0, 0.0)
```

This applies full braking.

HUD message:

```text
PEDESTRIAN AHEAD - EMERGENCY BRAKE
```

### Red Traffic Light

If a red traffic light is detected by YOLO with confidence at least 0.75:

```python
return (0.0, brake, 0.0)
```

The brake value depends on speed:

| Speed | Brake |
|---|---:|
| Greater than 15 km/h | 0.9 |
| 15 km/h or below | 0.6 |

HUD message:

```text
RED LIGHT - STOPPING
```

### Yellow Traffic Light

If a yellow/orange traffic light is detected with high confidence and the vehicle speed is above 10 km/h:

```python
return (0.0, 0.45, 0.0)
```

HUD message:

```text
Yellow light - slowing
```

### Vehicle Ahead

If a vehicle is detected and considered close, the system applies mild braking only if speed is above 20 km/h.

```python
return (0.0, 0.35, 0.0)
```

A vehicle is considered close if its bounding box area is greater than:

```text
45000 pixels
```

HUD message:

```text
Vehicle ahead - reducing speed
```

### Green Traffic Light

If a green traffic light is detected with high confidence, the system shows a notification but does not intervene.

HUD message:

```text
Green light ahead
```

Return value:

```python
None
```

The driver stays in control.

### No Hazard

If no relevant hazard is detected:

```python
return None
```

The human driver remains in full control.

---

## Notification Cooldown

The implementation includes cooldown logic to avoid repeatedly spamming messages on the HUD.

General notifications and warnings use a cooldown of:

```text
3.0 seconds
```

Alerts use a shorter cooldown:

```text
0.5 seconds
```

This prevents the screen from being filled with repeated messages while still allowing critical warnings to appear quickly.

---

## Live Viewer

The implementation starts a live frame viewer on port 8080:

```python
self._viewer = FrameViewer(port=8080)
self._viewer.start()
self.register_viewer(self._viewer)
```

The browser viewer can be opened at:

```text
http://localhost:8080
```

This shows the camera feed and annotated detections.

---

## Requirements

The only additional dependency added is:

```text
ultralytics
```

The final `requirements.txt` contains:

```text
ultralytics
```

The Docker image already provides common packages such as NumPy and OpenCV, so they were not duplicated in `requirements.txt`.

---

## How to Run

From the repository root:

```bash
docker compose --profile bag up --build
```

Then open the browser viewer:

```text
http://localhost:8080
```

The ADAS node will load:

```text
solution/my_adas.py
solution/best.pt
```

---

## Local Validation

The repository includes tests.

Run:

```bash
python -m pytest tests/test_my_adas.py -v
```

The tests validate that the required ADAS functions return outputs in the expected format and that control commands are within valid ranges.

---

## Notebook Workflow

The notebook `CARLA_PROJECT_MECHATRONICS_BLOCK_WEEK.ipynb` was used for the full machine learning pipeline.

The notebook performs:

1. Environment setup.
2. Kaggle authentication.
3. Kaggle CARLA dataset download.
4. Dataset structure inspection.
5. Clean YOLO dataset preparation.
6. Lab dataset upload.
7. Lab dataset extraction with Windows-path fix.
8. Kaggle + lab dataset merge.
9. YOLOv8n training with mosaic and scale augmentation.
10. Final model download as `best.pt`.
11. YOLOv8n, YOLOv8s, YOLOv8m comparative analysis.
12. Generation of `my_adas.py`.
13. Copying `best.pt` into the solution folder.
14. Creation of the final submission ZIP.

---

## Final Training Code Summary

The final training cell used:

```python
model = YOLO("yolov8n.pt")

model.train(
    data=str(MERGED_YAML),
    epochs=60,
    imgsz=640,
    batch=16,
    project=str(RUN_DIR),
    name="hshl_carla_plus_lab_yolov8n_augmented",
    exist_ok=True,
    patience=12,
    mosaic=1.0,
    close_mosaic=10,
    scale=0.50,
    verbose=True,
    plots=True,
)
```

---

## Why the Final Model Is YOLOv8n

The comparative analysis showed that YOLOv8n had the best ADAS score because it was much faster and smaller while still achieving strong detection performance.

For ADAS, speed is important because the system must process camera frames continuously and react quickly. A larger model may have slightly better accuracy, but if it is slower, it may not be as suitable for real-time driver assistance.

YOLOv8n was therefore selected as the best practical choice.

---

## Safety Design Choices

The system is designed conservatively.

Important safety choices include:

- High confidence threshold for traffic lights.
- High confidence threshold for pedestrians.
- No braking on low-confidence color-only traffic light detection.
- No takeover for green traffic lights.
- No generic braking for every vehicle detection.
- Mild braking only for close vehicles.
- Full braking for pedestrians.
- No throttle and brake simultaneously.

These decisions reduce false interventions while still responding to safety-critical situations.

---

## Limitations

The project has some limitations:

1. The lab dataset is relatively small.
2. Traffic lights are often small in the image, making detection harder.
3. The system uses only camera and speed information.
4. LiDAR is not used.
5. Distance estimation is approximated using bounding box size.
6. CARLA lighting and object rendering can affect detection quality.
7. The ADAS control logic is rule-based, not learned.

---

## Possible Future Improvements

Future improvements could include:

- More lab data collection.
- More balanced traffic-light examples.
- Better distance estimation using depth or stereo vision.
- Lane detection integration.
- Temporal smoothing across frames.
- Tracking detected objects across time.
- Better pedestrian risk estimation.
- Testing under more CARLA weather and lighting conditions.
- Tuning thresholds based on live driving experiments.

---

## Conclusion

This project implements a complete CARLA ADAS pipeline:

- Dataset preparation
- Public + lab dataset merging
- YOLOv8 training
- Model comparison
- Final model deployment
- Traffic light detection
- Pedestrian and vehicle detection
- Driver warning and control intervention

The final submitted system uses a YOLOv8n model trained for 60 epochs on the merged Kaggle and lab dataset. The trained model is deployed as `solution/best.pt` and loaded inside `solution/my_adas.py`.

The final ADAS behavior is conservative and safety-focused: it warns the driver when appropriate and intervenes only for high-confidence hazards such as pedestrians, red lights, yellow lights, and close vehicles.
