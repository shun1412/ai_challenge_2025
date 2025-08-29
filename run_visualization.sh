#!/bin/bash

# Vehicle trajectory and course map visualization runner script

echo "=========================================="
echo "Vehicle Trajectory and Course Map Visualization"
echo "=========================================="

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import pandas, matplotlib, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
fi

# Run the visualization
echo "Running visualization..."
python3 visualize_trajectory_and_map_en.py

# Check if image was created
if [ -f "trajectory_and_map_visualization.png" ]; then
    echo "=========================================="
    echo "Visualization completed successfully!"
    echo "Image saved as: trajectory_and_map_visualization.png"
    echo "File size: $(ls -lh trajectory_and_map_visualization.png | awk '{print $5}')"
    echo "=========================================="
else
    echo "Error: Image file was not created."
    exit 1
fi 