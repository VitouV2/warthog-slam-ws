# Warthog SLAM Workspace

**Comparative Evaluation of Fast-LIO2 vs LIO-SAM for Heterogeneous Multi-Robot SLAM using ROS2 Humble**

This repository contains the ROS2 workspace for a thesis project at the **Cambodia University of Technology and Science (CamTech)**. The project deploys two Clearpath robots — a **Husky A200** (indoor warehouse) and a **Warthog W200** (outdoor farm) — in Gazebo simulation, with each robot running a different LiDAR-Inertial SLAM algorithm for comparative evaluation.

| Robot | Environment | SLAM Algorithm | Status |
|-------|-------------|----------------|--------|
| Clearpath Husky A200 | Indoor Warehouse | Fast-LIO2 | ✅ Validated |
| Clearpath Warthog W200 | Outdoor Farm | LIO-SAM | ✅ Validated |

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Running the Simulation](#running-the-simulation)
- [Running Fast-LIO2 on Husky](#running-fast-lio2-on-husky)
- [Running LIO-SAM on Warthog](#running-lio-sam-on-warthog)
- [Running Both Robots Together](#running-both-robots-together)
- [Tuning Parameters](#tuning-parameters)
- [Known Issues](#known-issues)
- [Author](#author)

---

## System Requirements

- **OS:** Ubuntu 22.04 LTS
- **ROS2:** Humble Hawksbill
- **Gazebo:** Ignition Fortress (ign-gazebo 6)
- **GPU:** Any GPU supporting OpenGL 4.0+ (required for Ignition rendering)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** ~5GB for workspace and dependencies

---

## Repository Structure

```
warthog-slam-ws/
└── src/
    ├── FAST_LIO/               # Fast-LIO2 SLAM algorithm (ROS2)
    ├── LIO-SAM/                # LIO-SAM SLAM algorithm (ROS2 branch)
    ├── livox_ros_driver2/      # Livox LiDAR driver (Fast-LIO2 dependency)
    ├── Livox-SDK2/             # Livox SDK (Fast-LIO2 dependency)
    ├── husky_description/      # Clearpath Husky A200 URDF
    ├── warthog_description/    # Clearpath Warthog W200 URDF with VLP-16 LiDAR
    └── warthog_gazebo/         # Launch files and Gazebo worlds
        ├── launch/
        │   ├── multi_robot_warehouse.launch.py   # Husky + Warthog in warehouse
        │   ├── warthog_outdoor_liosam.launch.py  # Warthog in outdoor farm world
        │   └── warthog_warehouse.launch.py       # Warthog only in warehouse
        └── worlds/
            └── outdoor_farm.sdf                  # Custom outdoor farm world
```

---

## Installation

### 1. Install ROS2 Humble

Follow the official ROS2 Humble installation guide:
```bash
https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html
```

Add to your `.bashrc`:
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 2. Install Clearpath Robot Packages

```bash
sudo apt install ros-humble-clearpath-desktop
sudo apt install ros-humble-clearpath-simulator
```

### 3. Install LIO-SAM Dependencies

```bash
sudo add-apt-repository ppa:borglab/gtsam-release-4.1
sudo apt update
sudo apt install -y libgtsam-dev libgtsam-unstable-dev \
  ros-humble-perception-pcl \
  ros-humble-pcl-msgs \
  ros-humble-vision-opencv
```

### 4. Install Fast-LIO2 Dependencies

```bash
sudo apt install -y ros-humble-tf2-sensor-msgs \
  ros-humble-tf2-geometry-msgs \
  ros-humble-nav-msgs
```

### 5. Clone This Repository

```bash
mkdir -p ~/warthog_ws
cd ~/warthog_ws
git clone https://github.com/VitouV2/warthog-slam-ws.git .
```

### 6. Build the Workspace

```bash
cd ~/warthog_ws
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

> **Note:** Add `source ~/warthog_ws/install/setup.bash` to your `.bashrc` so you don't need to source it every time.

---

## Running the Simulation

### Multi-Robot Warehouse (Husky + Warthog)

```bash
ros2 launch warthog_gazebo multi_robot_warehouse.launch.py
```

This spawns:
- **Husky A200** at `x=5, y=0` under namespace `/a200_0001`
- **Warthog W200** at `x=-5, y=0` under namespace `/w200_0001`

### Warthog Outdoor Farm World (Single Robot)

```bash
ros2 launch warthog_gazebo warthog_outdoor_liosam.launch.py
```

This spawns the Warthog at `x=-30, y=0` in the custom outdoor farm world with:
- Barn, water tank, 4 trees, 4 fence posts, and a shed
- VLP-16 LiDAR publishing to `/warthog/lidar/points/points`
- IMU publishing to `/warthog/imu/data`

---

## Running Fast-LIO2 on Husky

**Terminal 1 — Launch simulation:**
```bash
ros2 launch warthog_gazebo multi_robot_warehouse.launch.py
```

**Terminal 2 — Launch Fast-LIO2:**
```bash
cd ~/warthog_ws && source install/setup.bash
ros2 launch fast_lio mapping_avia.launch.py
```

**Terminal 3 — Drive Husky:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/a200_0001/cmd_vel
```

**Verify mapping:**
```bash
ros2 topic hz /cloud_registered
```

---

## Running LIO-SAM on Warthog

**Terminal 1 — Launch outdoor farm simulation:**
```bash
ros2 launch warthog_gazebo warthog_outdoor_liosam.launch.py
```

Wait until Gazebo is fully loaded and `/clock` is publishing:
```bash
ros2 topic hz /clock   # Should show ~1000 Hz
```

**Terminal 2 — Launch LIO-SAM:**
```bash
cd ~/warthog_ws && source install/setup.bash
ros2 launch lio_sam run.launch.py
```

**Terminal 3 — Drive Warthog:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/w200_0001/cmd_vel
```

**Verify mapping:**
```bash
ros2 topic hz /lio_sam/mapping/odometry   # Should show ~5 Hz
```

**RViz2 — View the map:**
- Set **Fixed Frame** to `odom`
- Add `PointCloud2` → topic: `/lio_sam/mapping/cloud_registered`
- Add `Path` → topic: `/lio_sam/mapping/path`

**Save the map:**
```bash
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap \
  "{resolution: 0.1, destination: '/home/$USER/warthog_ws/liosam_map'}"
```

---

## Running Both Robots Together

```bash
# Terminal 1 — Gazebo
ros2 launch warthog_gazebo multi_robot_warehouse.launch.py

# Terminal 2 — Fast-LIO2 on Husky
ros2 launch fast_lio mapping_avia.launch.py

# Terminal 3 — Drive Husky
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/a200_0001/cmd_vel

# Terminal 4 — Drive Warthog
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/w200_0001/cmd_vel
```

---

## Tuning Parameters

### Fast-LIO2 (`src/FAST_LIO/config/`)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `lidar_type` | 1 | Velodyne VLP-16 |
| `N_SCAN` | 16 | Number of LiDAR channels |
| `blind` | 0.5 | Minimum LiDAR range (m) |

### LIO-SAM (`src/LIO-SAM/config/params.yaml`)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `pointCloudTopic` | `/warthog/lidar/points/points` | LiDAR input topic |
| `imuTopic` | `/warthog/imu/data` | IMU input topic |
| `lidarFrame` | `vlp16_link` | LiDAR TF frame |
| `N_SCAN` | 16 | LiDAR channels |
| `use_sim_time` | `true` | Must be true for Gazebo |
| `extrinsicTrans` | `[0, 0, 0.525]` | LiDAR height above base_link |

> **Important:** Always launch Gazebo first and wait for a stable `/clock` before launching LIO-SAM. Launching LIO-SAM before Gazebo causes a TF time jump error that prevents the map from initializing.

---

## Known Issues

**1. LIO-SAM `imuPreintegration` shows as duplicate in `ros2 node list`**
This is a DDS ghost node registration from previous crashed sessions. Check actual process count with:
```bash
ps aux | grep lio_sam_imu | grep -v grep
```
If only 1 process exists, the system is fine — the duplicate is harmless.

**2. `Frame [map] does not exist` in RViz2**
The `map` frame is only created after the robot moves. Drive the robot first, then set Fixed Frame to `odom` in RViz2.

**3. LIO-SAM `Not enough features` warning**
This occurs in feature-sparse environments (flat warehouse floors, long corridors). This is an expected finding — LIO-SAM performs better in outdoor environments with varied geometry. Lower the thresholds in `params.yaml`:
```yaml
edgeFeatureMinValidNum: 3
surfFeatureMinValidNum: 30
```

**4. Gazebo segfault on world load**
Too many objects in the SDF world exceed GPU memory. Reduce the number of models or use simpler geometry. The `outdoor_farm.sdf` world is already optimized to stay within typical GPU limits.

**5. Point cloud timestamp not available**
LIO-SAM deskewing is disabled when the point cloud has no per-point timestamps. This causes increased drift. The system still maps but with reduced accuracy — this is a known Ignition Gazebo limitation for the lidar sensor type.

---

## Author

**Chea Vitou** (ID: 6023010001)
Bachelor of Science in Robotics and Automation Engineering
Cambodia University of Technology and Science (CamTech)

Supervisors: Dr. May Thu & Mr. Kosal Cholsa

---

*This project is part of a thesis comparing Fast-LIO2 and LIO-SAM for multi-robot SLAM in ROS2 Humble simulation.*
