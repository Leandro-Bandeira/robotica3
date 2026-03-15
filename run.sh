#!/bin/bash

SESSION="jetauto"

# Se a sessão já existir, apenas conecta
tmux has-session -t $SESSION 2>/dev/null
if [ $? -eq 0 ]; then
  tmux attach -t $SESSION
  exit 0
fi

# Cria nova sessão tmux em background
tmux new-session -d -s $SESSION -n description

# Aba 0 - Robot Description
tmux send-keys -t $SESSION:0 \
  "source install/setup.bash && ros2 launch robotics_subject robot_description.launch.py" C-m
sleep 1 # Aguarda 1 segundo

# Aba 1 - Simulation World
tmux new-window -t $SESSION -n simulation
tmux send-keys -t $SESSION:1 \
  "source install/setup.bash && ros2 launch robotics_subject simulation_world.launch.py " C-m
sleep 5 

# Aba 2 - EKF
tmux new-window -t $SESSION -n ekf
tmux send-keys -t $SESSION:2 \
  "source install/setup.bash && ros2 launch robotics_subject ekf.launch.py" C-m
sleep 1

# Aba 3 - RViz
tmux new-window -t $SESSION -n rviz
tmux send-keys -t $SESSION:3 \
  "source install/setup.bash && ros2 launch robotics_subject rviz.launch.py" C-m
sleep 1

# Aba 4 - Teleop
tmux new-window -t $SESSION -n teleop
tmux send-keys -t $SESSION:4 \
  "source install/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=jetauto/cmd_vel" C-m
sleep 1

# Aba 6 - SLAM (última)

#tmux new-window -t $SESSION -n slam
#tmux send-keys -t $SESSION:6 \
#  "source install/setup.bash && ros2 launch robotics_subject slam.launch.py" C-m

# Volta para a primeira aba
tmux select-window -t $SESSION:0

# Anexa à sessão
tmux attach -t $SESSION