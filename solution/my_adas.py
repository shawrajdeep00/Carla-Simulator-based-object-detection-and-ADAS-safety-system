#!/usr/bin/env python3
"""
HSHL ADAS Student Lab
=====================
A human student drives the car manually (steering wheel / keyboard).
Your ADAS module runs in parallel. Implement the three functions below:

    detect_traffic_light(image)  — called for every camera frame (~15 fps)
    detect_objects(image)        — called for every camera frame (~15 fps)
    compute_control(speed_kmh)   — called for every speed update (~45 Hz)
"""
import cv2          # type: ignore
import numpy as np  # type: ignore
import rclpy        # type: ignore
import time

from pathlib import Path
from adas import CarlaADASInterface, FrameViewer

try:
    from ultralytics import YOLO  # type: ignore
except Exception:
    YOLO = None


class MyADAS(CarlaADASInterface):

    def __init__(self):
        super().__init__("my_adas")

        self._traffic_light_info = None
        self._object_info = None

        self._last_notification_time = 0.0
        self._last_alert_time = 0.0
        self._notification_cooldown = 3.0

        self._traffic_light_confidence_threshold = 0.75
        self._pedestrian_confidence_threshold = 0.70
        self._vehicle_confidence_threshold = 0.50

        self._yolo = None
        self._last_image_id = None
        self._last_yolo_result = None

        if YOLO is not None:
            try:
                model_path = self._find_model_path()
                self._yolo = YOLO(str(model_path))
                self.get_logger().info(f"Loaded YOLO model: {model_path}")
            except Exception as exc:
                self.get_logger().warning(f"Could not load YOLO model: {exc}")

        self._viewer = FrameViewer(port=8080)
        self._viewer.start()
        self.register_viewer(self._viewer)

        self.on_camera_image(self.process_image)
        self.on_speed_update(self.on_speed)

        self.get_logger().info("MyADAS started — waiting for sensor data...")

    def _find_model_path(self) -> Path:
        here = Path(__file__).resolve().parent
        candidates = [
            here / "best.pt",
            here / "weights" / "best.pt",
            Path("solution") / "best.pt",
            Path("best.pt"),
        ]
        for path in candidates:
            if path.exists():
                return path
        return here / "best.pt"

    def _run_yolo(self, image: np.ndarray):
        if self._yolo is None:
            return None

        image_id = id(image)
        if self._last_image_id == image_id and self._last_yolo_result is not None:
            return self._last_yolo_result

        result = self._yolo(image, verbose=False, conf=0.45, iou=0.45)[0]
        self._last_image_id = image_id
        self._last_yolo_result = result
        return result

    def process_image(self, image: np.ndarray):
        annotated = image

        try:
            tl_result = self.detect_traffic_light(image)
            if tl_result is not None:
                self._traffic_light_info = tl_result
                if "annotated" in tl_result:
                    annotated = tl_result["annotated"]
        except NotImplementedError:
            pass
        except Exception as exc:
            self.get_logger().error(f"detect_traffic_light() raised {type(exc).__name__}: {exc}")

        try:
            obj_result = self.detect_objects(image)
            if obj_result is not None:
                self._object_info = obj_result
                if "annotated" in obj_result:
                    annotated = obj_result["annotated"]
        except NotImplementedError:
            pass
        except Exception as exc:
            self.get_logger().error(f"detect_objects() raised {type(exc).__name__}: {exc}")

        self._viewer.push(annotated)

    def on_speed(self, speed_kmh: float):
        try:
            result = self.compute_control(speed_kmh)
            if result is not None:
                throttle, brake, steer = self._check_compute_control(result)
                self.send_control(throttle, brake, steer)
        except NotImplementedError:
            pass
        except (ValueError, TypeError) as exc:
            msg = f"compute_control() bad output: {exc}"
            self.get_logger().error(msg)
            self.show_alert(msg, duration=4.0)
        except Exception as exc:
            self.get_logger().error(f"compute_control() raised {type(exc).__name__}: {exc}")

    def detect_traffic_light(self, image: np.ndarray):
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return {"state": "unknown"}

        annotated = image.copy()
        h, w = image.shape[:2]
        roi_y2 = max(1, h // 3)
        roi_bgr = image[:roi_y2, :]
        hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

        red1 = cv2.inRange(hsv_roi, np.array([0, 100, 100]), np.array([10, 255, 255]))
        red2 = cv2.inRange(hsv_roi, np.array([160, 100, 100]), np.array([180, 255, 255]))
        red = cv2.bitwise_or(red1, red2)
        yellow = cv2.inRange(hsv_roi, np.array([15, 90, 90]), np.array([40, 255, 255]))
        green = cv2.inRange(hsv_roi, np.array([40, 70, 70]), np.array([90, 255, 255]))

        kernel = np.ones((3, 3), np.uint8)
        masks = {
            "red": cv2.morphologyEx(red, cv2.MORPH_OPEN, kernel),
            "yellow": cv2.morphologyEx(yellow, cv2.MORPH_OPEN, kernel),
            "green": cv2.morphologyEx(green, cv2.MORPH_OPEN, kernel),
        }
        counts = {name: int(cv2.countNonZero(mask)) for name, mask in masks.items()}

        state = "unknown"
        confidence = 0.0
        source = "none"

        result = self._run_yolo(image)
        yolo_state = None
        yolo_confidence = 0.0

        if result is not None and result.boxes is not None:
            names = result.names

            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = str(names.get(cls, cls)).lower()

                if "traffic_light" not in name:
                    continue

                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                box_w = max(0, x2 - x1)
                box_h = max(0, y2 - y1)
                box_area = box_w * box_h

                if y2 > int(0.72 * h):
                    continue
                if box_area > int(0.035 * h * w):
                    continue

                candidate = "unknown"
                if "red" in name:
                    candidate = "red"
                elif "green" in name:
                    candidate = "green"
                elif "yellow" in name or "orange" in name:
                    candidate = "yellow"

                if candidate != "unknown" and conf > yolo_confidence:
                    yolo_state = candidate
                    yolo_confidence = conf

                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(
                    annotated,
                    f"{name} {conf:.2f}",
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        if yolo_state is not None and yolo_confidence >= self._traffic_light_confidence_threshold:
            state = yolo_state
            confidence = yolo_confidence
            source = "yolo"

        color_map = {
            "red": (0, 0, 255),
            "yellow": (0, 255, 255),
            "green": (0, 255, 0),
            "unknown": (180, 180, 180),
        }
        color = color_map.get(state, (180, 180, 180))

        cv2.rectangle(annotated, (0, 0), (w - 1, roi_y2), color, 2)
        cv2.putText(
            annotated,
            f"Traffic light: {state} ({source} {confidence:.2f})",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            color,
            2,
            cv2.LINE_AA,
        )

        return {
            "state": state,
            "annotated": annotated,
            "counts": counts,
            "confidence": confidence,
            "source": source,
        }

    def detect_objects(self, image: np.ndarray):
        pedestrians = []
        vehicles = []

        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return {"pedestrians": pedestrians, "vehicles": vehicles}

        annotated = image.copy()
        result = self._run_yolo(image)

        if result is None or result.boxes is None:
            cv2.putText(
                annotated,
                "YOLO model not available",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
            return {"pedestrians": pedestrians, "vehicles": vehicles, "annotated": annotated}

        names = result.names

        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            name = str(names.get(cls, cls)).lower()

            entry = {"bbox": [x1, y1, x2, y2], "confidence": round(conf, 3)}

            is_pedestrian = (
                (cls == 0 and name == "person")
                or "person" in name
                or "pedestrian" in name
            )

            is_vehicle = (
                cls in {2, 3, 5, 7}
                or any(
                    key in name
                    for key in [
                        "vehicle",
                        "car",
                        "truck",
                        "bus",
                        "motorbike",
                        "motobike",
                        "motorcycle",
                        "bike",
                    ]
                )
            )

            if "traffic" in name or "sign" in name or "light" in name:
                is_vehicle = False

            if is_pedestrian and conf < self._pedestrian_confidence_threshold:
                continue
            if is_vehicle and conf < self._vehicle_confidence_threshold:
                continue

            if is_pedestrian:
                pedestrians.append(entry)
                color = (0, 0, 255)
                label = f"pedestrian {conf:.2f}"
            elif is_vehicle:
                vehicles.append(entry)
                color = (255, 120, 0)
                label = f"vehicle {conf:.2f}"
            else:
                continue

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
                cv2.LINE_AA,
            )

        cv2.putText(
            annotated,
            f"Pedestrians: {len(pedestrians)} | Vehicles: {len(vehicles)}",
            (20, image.shape[0] - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        return {
            "pedestrians": pedestrians,
            "vehicles": vehicles,
            "annotated": annotated,
        }

    def compute_control(self, speed_kmh: float):
        tl = self._traffic_light_info
        tl_state = tl["state"] if tl else "unknown"
        tl_confidence = float(tl.get("confidence", 0.0)) if tl else 0.0
        tl_source = tl.get("source", "none") if tl else "none"

        obj = self._object_info
        pedestrians = obj["pedestrians"] if obj else []
        vehicles = obj["vehicles"] if obj else []

        if pedestrians:
            self._safe_alert("PEDESTRIAN AHEAD - EMERGENCY BRAKE", duration=3.0)
            return (0.0, 1.0, 0.0)

        if (
            tl_state == "red"
            and tl_source == "yolo"
            and tl_confidence >= self._traffic_light_confidence_threshold
        ):
            self._safe_alert("RED LIGHT - STOPPING", duration=1.5)
            brake = 0.9 if speed_kmh > 15 else 0.6
            return (0.0, brake, 0.0)

        if (
            tl_state == "yellow"
            and tl_source == "yolo"
            and tl_confidence >= self._traffic_light_confidence_threshold
            and speed_kmh > 10
        ):
            self._safe_warning("Yellow light - slowing", duration=1.0)
            return (0.0, 0.45, 0.0)

        if vehicles:
            close_vehicle = self._has_close_vehicle(vehicles)
            if close_vehicle and speed_kmh > 20:
                self._safe_warning("Vehicle ahead - reducing speed", duration=1.0)
                return (0.0, 0.35, 0.0)
            return None

        if (
            tl_state == "green"
            and tl_source == "yolo"
            and tl_confidence >= self._traffic_light_confidence_threshold
        ):
            self._safe_notification("Green light ahead", duration=1.0)

        return None

    def _has_close_vehicle(self, vehicles) -> bool:
        max_area = 0
        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle["bbox"]
            area = max(0, x2 - x1) * max(0, y2 - y1)
            max_area = max(max_area, area)
        return max_area > 45000

    def _cooldown_ok(self) -> bool:
        now = time.time()
        if now - self._last_notification_time > self._notification_cooldown:
            self._last_notification_time = now
            return True
        return False

    def _safe_notification(self, msg: str, duration: float = 3.0) -> None:
        if self._cooldown_ok():
            self.show_notification(msg, duration=duration)

    def _safe_warning(self, msg: str, duration: float = 5.0) -> None:
        if self._cooldown_ok():
            self.show_warning(msg, duration=duration)

    def _safe_alert(self, msg: str, duration: float = 5.0) -> None:
        now = time.time()
        if now - self._last_alert_time > 0.5:
            self._last_alert_time = now
            self.show_alert(msg, duration=duration)

    @staticmethod
    def _check_compute_control(result):
        if not (isinstance(result, (tuple, list)) and len(result) == 3):
            raise TypeError(
                f"compute_control() must return a 3-tuple or None, "
                f"got {type(result).__name__!r} of length {len(result) if hasattr(result, '__len__') else '?'}."
            )

        throttle, brake, steer = float(result[0]), float(result[1]), float(result[2])

        if not (0.0 <= throttle <= 1.0):
            raise ValueError(f"throttle={throttle} out of [0.0, 1.0].")
        if not (0.0 <= brake <= 1.0):
            raise ValueError(f"brake={brake} out of [0.0, 1.0].")
        if not (-1.0 <= steer <= 1.0):
            raise ValueError(f"steer={steer} out of [-1.0, +1.0].")
        if throttle > 0.0 and brake > 0.0:
            raise ValueError("throttle and brake must not both be > 0 simultaneously.")

        return throttle, brake, steer


def main():
    rclpy.init()
    node = MyADAS()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
