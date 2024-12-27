import cv2
import numpy as np
import pyrealsense2 as rs
import cv2.aruco as aruco


class D435:
    pipeline = rs.pipeline()
    config = rs.config()
    # depth_frame = None

    # 配置RealSense相机
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    # 启动RealSense相机
    # pipeline.start(config)
    # 启动RealSense相机
    profile = pipeline.start(config)

    def __init__(self):
        # 等待相机稳定
        for i in range(30):
            D435.pipeline.wait_for_frames()

    def getColorAndDepthImage(self):

        # 对齐到RGB的相机坐标系
        align_to_color = rs.align(rs.stream.color)
        frames = D435.pipeline.wait_for_frames()
        frames = align_to_color.process(frames)

        # 获取深度图和彩色图
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        # 获取内参
        depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics     # 获取深度参数（像素坐标系转相机坐标系会用到）
        color_intrin = color_frame.profile.as_video_stream_profile().intrinsics     # 获取相机内参
        # 获取相机内参矩阵用于获取aruco位置
        aruco_intr_matrix = np.array([[color_intrin.fx, 0, color_intrin.ppx], [0, color_intrin.fy, color_intrin.ppy], [0, 0, 1]])
        if not depth_frame or not color_frame:
            print("D435获取图像失败")
            return None, None
        # 将深度图和彩色图转换为NumPy数组
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        # print('return 2 args')
        # coeffs为相机畸变系数
        return color_image, depth_image, depth_frame, depth_intrin, color_intrin, aruco_intr_matrix, np.array(color_intrin.coeffs)

    def getIntrinsics(self):
        # 获得内参
        intrinsics = D435.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
        return intrinsics

    def get3dposition(self,x,y,depth,intrinsics):
        depth_point = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], depth)
        return depth_point
    
    def arucoPosition(self,color_image,intr_matrix,intr_coeffs):
        # 3. 创建 ArUco 码字典和检测参数
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        parameters = aruco.DetectorParameters()
        # Aruco检测
        corners, ids, rejected = aruco.detectMarkers(color_image, aruco_dict, parameters=parameters)
        # 如果检测到 ArUco 码
        if ids is not None:
            # 绘制检测到的 ArUco 码
            aruco.drawDetectedMarkers(color_image, corners, ids)

            # 估计每个 ArUco 码的姿态
            marker_length = 0.05  # 假设 ArUco 码边长为 5cm
            rvecs, tvecs, markerPoints = aruco.estimatePoseSingleMarkers(corners, marker_length, intr_matrix, intr_coeffs)

            for i in range(len(ids)):
                # 绘制坐标轴
                cv2.drawFrameAxes(color_image, intr_matrix, intr_coeffs, rvecs[i], tvecs[i], 0.1)

                # 将旋转向量转换为旋转矩阵
                rmat, _ = cv2.Rodrigues(rvecs[i])

                # 生成4x4变换矩阵 (T = [R|t])
                transformation_matrix = np.eye(4)
                transformation_matrix[:3, :3] = rmat
                # transformation_matrix[:3, 3] = tvecs
                transformation_matrix[:3, 3] = tvecs[i].flatten()
                
                
            return corners, ids, transformation_matrix, markerPoints, color_image
                # print(f"ArUco ID: {ids[i]}")
                # print("Transformation Matrix:\n", transformation_matrix)
        else:
            print("No ArUco markers detected.")
            return None, None, None, None, None

        # # 显示图像
        # cv2.imshow('ArUco Detection', color_image)
        # # 获取dictionary, 4x4的码，指示位50个
        # aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        # # 创建detector parameters
        # parameters = aruco.DetectorParameters()
        # # 输入rgb图, aruco的dictionary, 相机内参, 相机的畸变参数
        # detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        # corners, ids, rejected_img_points = detector.detectMarkers(color_image)
        # # corners, ids, rejected_img_points = aruco.detectMarkers(color_image, aruco_dict, parameters=parameters,cameraMatrix=intr_matrix, distCoeff=intr_coeffs)
        # # 估计出aruco码的位姿，0.045对应markerLength参数，单位是meter
        # # rvec是旋转向量， tvec是平移向量
        # rvec, tvec, markerPoints = aruco.estimatePoseSingleMarkers(corners, 0.045, intr_matrix, intr_coeffs)
        # try:
        # 	# 在图片上标出aruco码的位置
        #     aruco.drawDetectedMarkers(color_image, corners)
        #     # 根据aruco码的位姿标注出对应的xyz轴, 0.05对应length参数，代表xyz轴画出来的长度 
        #     aruco.drawAxis(color_image, intr_matrix, intr_coeffs, rvec, tvec, 0.05)
        #     return corners, ids, rvec, tvec, markerPoints, color_image
        # except:
        #     print("未检测到aruco码")
# image, _ = d435.getColorAndDepthImage()
# cv2.imshow("Color Image1", image)
# cv2.waitKey(0)

# d435 = D435()
# image, _ = d435.getColorAndDepthImage()
# cv2.imshow("Color Image2", image)
# cv2.waitKey(0)

# D435.pipeline.stop()
