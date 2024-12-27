# 记录修改

## 1. 运行 Real Robot Arm 时错误

运行 `roslaunch z1_bringup real_arm.launch rviz:=true` 时出现 `Lose connection with UDP sdk` 的问题，怀疑是 `UDP` 设置的问题。

- 尝试：插拔线缆后运行 --> 失败
- 尝试：修改 z1_ws/src/z1_ros/z1_hw/config/config.yaml 文件的port为8881 ---> 连接上，但是rviz打不开，机械臂异动
- 尝试：修改 z1_ws/src/z1_ros/z1_hw/config/config.yaml 与 z1_ws/src/z1_ros/z1_controller/config/config.yaml 的port为8881 运行 `roslaunch z1_bringup real_ctrl.launch ` 卡在 `Wait for connection with SDK ...`
- 尝试：上述恢复后，`ping 192.168.123.110` 能通，执行 `source ./devel/setup.bash` 后能执行通。但是rivz的robotmodel中报错：`No transform from [link01] to [world]` ，猜测是因为机械臂垫高了，于 URDF/Xacro 文件冲突
- 尝试：更改文件 `z1_ws/src/z1_ros/unitree_ros/robots/z1_description/xacro/z1.urdf ` 和 `z1_ws/src/z1_ros/unitree_ros/robots/z1_description/xacro/robot.xacro ` 的 `<link>`与 `<world>`的关系，修改了 `base_static_joint `此为 `<world>`与 `<link00>`的关系，重新 `catkin_make` --> 失败，单独执行 `z1_rviz.launch` 时，模型正确显示，但是执行 `roslaunch z1_bringup real_arm.launch rviz:=true` 时还是出错，link的tf出现问题，怀疑要重新编译 controller 的 <.so> 文件
- 尝试：发现 `z1_ws/src/z1_ros/z1_controller/config/z1.urdf` 这还有 URDF 文件，尝试修改，并重 `catkin_make` 和 `source`  --> 失败
- 尝试：通过 `rosrun tf static_transform_publisher 0 0 0 0 0 0 link00 link01 100` 和 `rosrun rqt_tf_tree rqt_tf_tree` 检查发现，是因为link没有正确发布，详细阅读 `real_arm.launch` 一步一步查看修改
- 尝试：`z1_ws/src/z1_ros/z1_controller/config/config.yaml` 修改打开碰撞检测；`z1_ws/src/z1_ros/z1_moveit_config/launch/move_group.launch` 中的 `<argname="load_robot_description"default="false" />` 改为 `<true>`查看能否解决 --> 失败；
- 尝试：模型问题出现在 `<joint_state_publisher>` 没有正常启动导致，在 `<real_arm.launch>` 中加入 `<nodepkg="joint_state_publisher"type="joint_state_publisher"name="joint_state_publisher" />` --> 成功，RobotModel的报错解决，但是moveit依旧无法控制机械表
- 尝试：检查发现，控制器没有正常发布；其中z1_hw.launch文件没有正常启动
- 将pinocchio重装至2.6.19，重新catkin_make / source 后分布执行程序，代码报错解决，但是moveit plan&exec依旧失败，报错：
- ```
  [ERROR] [1729492919.938141891, 206.323000000]: Unable to identify any set of controllers that can actuate the specified joints: [ joint1 joint2 joint3 joint4 joint5 joint6 ]
  [ERROR] [1729492919.938209728, 206.323000000]: Known controllers and their joints:

  [ERROR] [1729492919.938256465, 206.323000000]: Apparently trajectory initialization failed

  ```
- 尝试：将 `<z1_ws/src/z1_ros/z1_hw/config/controllers.yaml>` 的内容复制进 `<z1_ws/src/z1_ros/z1_moveit_config/config/ros_controllers.yaml>` --> 失败
