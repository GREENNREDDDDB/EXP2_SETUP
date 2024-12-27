import cv2
import numpy as np
from ultralytics import YOLO
import pyrealsense2 as rs
from modules.d435_driver import D435
from modules.PointCloudController import PointCloudController
from modules.VisualYolo import VisualYolo

def main():
    try:
        d435 = D435()
        # Load a model
        model = YOLO('/home/greenddb/Projects/IEEE_RAL_EXP2_SETUP/yolov8/runs/detect/ieee_ral_exp214/weights/best.pt')  # load a custom model
        # 创建一个空的二维列表来存储结果，每个被检测到的物体为一个列表，其中obj[n][0]为id，obj[n][1]为检测框的中心坐标
        while True:
            # 创建列表来存储检测到的物体
            objects = []
            i = 0
            color_image, depth_image, depth_frames, depth_intrin, _, intri_matrix, coeffs = d435.getColorAndDepthImage()
            # 获取aruco码信息，其中绘制出来的坐标图，红轴为x，绿轴为y，蓝轴为z，transformation_matrix为aruco码坐标系到相机坐标系的变换矩阵
            corners, ids, transformation_matrix, markerPoints, color_image = d435.arucoPosition(color_image, intri_matrix, coeffs)
            if corners is None:
                print("No ArcUo detected")
                break
            # 对变换矩阵进行逆变换，得到相机坐标系到aruco码坐标系的变换矩阵
            transformation_matrix = np.linalg.inv(transformation_matrix)
            # obtain the depth frames's limits
            width = depth_frames.get_width()
            height = depth_frames.get_height()
            # print("corners:")
            # print(corners)
            # print("ids:")
            # print(ids)
            # print("transformation_matrix:")
            # print(transformation_matrix)
            # print("markerPoints:")
            # print(markerPoints)
            results = model.track(color_image, persist=True, conf=0.5, iou=0.5)
            
            # Visualize the results on the frame
            annotated_frame = results[0].plot()
            # Display the annotated frame
            cv2.imshow("YOLOv8 Inference", annotated_frame)
            print("test:")
            if results[0].boxes.id is not None:
                for box in results[0].boxes:
                    # 输出检测到的物体id
                    id = int(box.id)
                    # 获取检测框的坐标
                    x1, y1, w, h = box.xywh[0]
                    x1 = float(x1)
                    y1 = float(y1)
                    w = float(w)
                    h = float(h)
                    # 检测框的中心点
                    cx = round(x1 + w / 2)
                    cy = round(y1 + h / 2)
                    # estimate the center point is in the depth image
                    if 0 <= cx <= width and 0 <= cy <= height:
                        # 获取三维坐标
                        depth = depth_frames.get_distance(cx, cy)
                    else:
                        print("The center point is out of the depth image")
                        break
                    # print("depth:")
                    # print(depth)
                    position = d435.get3dposition(cx, cy, depth, depth_intrin)
                    # 将目标相对于相机坐标系的位置写成齐次矩阵形式
                    position = np.array([position[0], position[1], position[2], 1])
                    # 坐标变换，将目标相对于相机坐标系的位置转换为相对于aruco码坐标系的位置
                    position = np.dot(transformation_matrix, position)
                    # position = np.array([position[0], ])
                    # 将id添加到位置列表末尾
                    position_id = np.append(position, id)
                    # 将位置列表添加到objects列表中
                    objects.append(position_id)
                    
                    # print("objects:")
                    # print(objects)
                    # print(id)
                    # print(position)
                    # objects[i].append(id)
                    # objects[i].append(position[0])
                    # objects[i].append(position[1])
                    # i = i+1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("Shutting down...")
        D435.pipeline.stop()

if __name__ == "__main__":
    main()
