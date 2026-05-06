cmake_minimum_required(VERSION 3.8)
project(warthog_gazebo)

find_package(ament_cmake REQUIRED)

# Install launch files only (no worlds folder needed)
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
