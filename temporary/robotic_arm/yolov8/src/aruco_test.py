import pyrealsense2 as rs
import numpy as np
import cv2
import cv2.aruco as aruco

# 1. 初始化 RealSense 相机
pipeline = rs.pipeline()
config = rs.config()

# 启动流，配置彩色流和深度流
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
pipeline.start(config)

# 2. 加载相机内参
# 如果有相机标定文件，可以在这里加载，否则使用 RealSense 内置的标定参数
profile = pipeline.get_active_profile()
intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
camera_matrix = np.array([[intrinsics.fx, 0, intrinsics.ppx],
                          [0, intrinsics.fy, intrinsics.ppy],
                          [0, 0, 1]])
dist_coeffs = np.zeros((5, 1))  # 假设 RealSense 相机的畸变系数接近零

# 3. 创建 ArUco 码字典和检测参数
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# 4. 实时检测 ArUco 码并估计姿态
try:
    while True:
        # 捕获 RealSense 帧
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # 转换为 NumPy 数组格式
        color_image = np.asanyarray(color_frame.get_data())

        # 5. ArUco 码检测
        corners, ids, rejected = aruco.detectMarkers(color_image, aruco_dict, parameters=parameters)

        # 如果检测到 ArUco 码
        if ids is not None:
            # 绘制检测到的 ArUco 码
            aruco.drawDetectedMarkers(color_image, corners, ids)

            # 估计每个 ArUco 码的姿态
            marker_length = 0.05  # 假设 ArUco 码边长为 5cm
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeffs)

            for i in range(len(ids)):
                # 绘制坐标轴
                cv2.drawFrameAxes(color_image, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], 0.1)

                # 将旋转向量转换为旋转矩阵
                rmat, _ = cv2.Rodrigues(rvecs[i])

                # 生成4x4变换矩阵 (T = [R|t])
                transformation_matrix = np.eye(4)
                transformation_matrix[:3, :3] = rmat
                transformation_matrix[:3, 3] = tvecs[i].flatten()

                print(f"ArUco ID: {ids[i]}")
                print("Transformation Matrix:\n", transformation_matrix)

        # 显示图像
        cv2.imshow('ArUco Detection', color_image)

        # 按下 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 停止管道
    pipeline.stop()
    cv2.destroyAllWindows()
