#!/usr/bin/env python3
"""
Vehicle trajectory and course map visualization script
"""

import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np
from matplotlib.patches import Polygon
import os

def parse_osm_map(osm_file_path):
    """
    Parse OSM file to extract road shapes from Lanelet2 format
    """
    tree = ET.parse(osm_file_path)
    root = tree.getroot()
    
    # Extract node coordinates
    nodes = {}
    for node in root.findall('.//node'):
        node_id = node.get('id')
        local_x = None
        local_y = None
        for tag in node.findall('tag'):
            if tag.get('k') == 'local_x':
                local_x = float(tag.get('v'))
            elif tag.get('k') == 'local_y':
                local_y = float(tag.get('v'))
        if local_x is not None and local_y is not None:
            nodes[node_id] = (local_x, local_y)
    
    # Extract way coordinates
    ways = {}
    for way in root.findall('.//way'):
        way_id = way.get('id')
        way_points = []
        for nd in way.findall('nd'):
            node_id = nd.get('ref')
            if node_id in nodes:
                way_points.append(nodes[node_id])
        if len(way_points) > 1:
            ways[way_id] = way_points
    
    # Extract lanelet relations (roads with width)
    roads = []
    for relation in root.findall('.//relation'):
        relation_type = None
        for tag in relation.findall('tag'):
            if tag.get('k') == 'type' and tag.get('v') == 'lanelet':
                relation_type = 'lanelet'
                break
        
        if relation_type == 'lanelet':
            left_way_id = None
            right_way_id = None
            centerline_way_id = None
            
            for member in relation.findall('member'):
                role = member.get('role')
                ref = member.get('ref')
                if role == 'left':
                    left_way_id = ref
                elif role == 'right':
                    right_way_id = ref
                elif role == 'centerline':
                    centerline_way_id = ref
            
            # Create road polygon from left and right boundaries
            if left_way_id in ways and right_way_id in ways:
                left_points = ways[left_way_id]
                right_points = ways[right_way_id]
                
                # Create polygon by combining left and right boundaries
                if len(left_points) > 1 and len(right_points) > 1:
                    # Reverse right points to create a closed polygon
                    polygon_points = left_points + right_points[::-1]
                    if len(polygon_points) > 3:  # Need at least 3 points for a polygon
                        roads.append(polygon_points)
    
    return roads

def load_trajectory_data(csv_file_path):
    """
    Load vehicle trajectory data from CSV file
    """
    df = pd.read_csv(csv_file_path)
    return df[['x', 'y']].values

def create_road_polygon(road_points, width=3.0):
    """
    Create a polygon with width from road centerline
    """
    if len(road_points) < 2:
        return None
    
    # Convert road centerline to numpy array
    center_line = np.array(road_points)
    
    # Calculate road direction vectors
    directions = np.diff(center_line, axis=0)
    lengths = np.linalg.norm(directions, axis=1)
    directions = directions / lengths[:, np.newaxis]
    
    # Calculate perpendicular vectors (road width direction)
    perp_directions = np.array([-directions[:, 1], directions[:, 0]]).T
    
    # Calculate left and right edge points
    left_points = center_line[:-1] + perp_directions * width / 2
    right_points = center_line[:-1] - perp_directions * width / 2
    
    # Create polygon vertices
    polygon_points = np.vstack([
        left_points,
        right_points[::-1],  # Reverse right side points
        left_points[:1]  # Close the polygon
    ])
    
    return polygon_points

def visualize_trajectory_and_map():
    """
    Visualize vehicle trajectories and course map
    """
    # File paths
    base_path = "aichallenge/workspace/src/aichallenge_submit"
    osm_file = os.path.join(base_path, "aichallenge_submit_launch/map/lanelet2_map.osm")
    trajectory_30km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_30km.csv")
    trajectory_15km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_15km.csv")
    
    # Load data
    print("Loading map data...")
    roads = parse_osm_map(osm_file)
    print(f"Found {len(roads)} road segments")
    
    print("Loading trajectory data...")
    traj_30km = load_trajectory_data(trajectory_30km)
    traj_15km = load_trajectory_data(trajectory_15km)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Draw map (roads with width)
    print("Drawing map...")
    road_color = '#8B8B8B'  # Gray
    road_count = 0
    for road_points in roads:
        if len(road_points) > 2:  # Need at least 3 points for a polygon
            try:
                # Convert to numpy array and create polygon
                road_array = np.array(road_points)
                road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, edgecolor='black', linewidth=0.5)
                ax.add_patch(road_patch)
                road_count += 1
            except Exception as e:
                print(f"Error creating road polygon: {e}")
                continue
    
    print(f"Drew {road_count} road polygons")
    
    # Draw trajectories
    print("Drawing trajectories...")
    ax.plot(traj_30km[:, 0], traj_30km[:, 1], 'r-', linewidth=3, label='30km/h Trajectory', alpha=0.8)
    ax.plot(traj_15km[:, 0], traj_15km[:, 1], 'b-', linewidth=3, label='15km/h Trajectory', alpha=0.8)
    
    # Mark start and end points
    ax.plot(traj_30km[0, 0], traj_30km[0, 1], 'ro', markersize=10, label='30km/h Start')
    ax.plot(traj_30km[-1, 0], traj_30km[-1, 1], 'rs', markersize=10, label='30km/h End')
    ax.plot(traj_15km[0, 0], traj_15km[0, 1], 'bo', markersize=10, label='15km/h Start')
    ax.plot(traj_15km[-1, 0], traj_15km[-1, 1], 'bs', markersize=10, label='15km/h End')
    
    # Graph settings
    ax.set_xlabel('X Coordinate (m)', fontsize=12)
    ax.set_ylabel('Y Coordinate (m)', fontsize=12)
    ax.set_title('Vehicle Trajectories and Course Map', fontsize=16, fontweight='bold')
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Set axis limits (auto-adjust based on data)
    all_x = np.concatenate([traj_30km[:, 0], traj_15km[:, 0]])
    all_y = np.concatenate([traj_30km[:, 1], traj_15km[:, 1]])
    
    x_margin = (all_x.max() - all_x.min()) * 0.05
    y_margin = (all_y.max() - all_y.min()) * 0.05
    
    ax.set_xlim(all_x.min() - x_margin, all_x.max() + x_margin)
    ax.set_ylim(all_y.min() - y_margin, all_y.max() + y_margin)
    
    # Save and display
    num = 100
    plt.tight_layout()
    plt.savefig('trajectory_and_map_visualization%d.png' % num, dpi=300, bbox_inches='tight')
    print("Image saved: trajectory_and_map_visualization%d.png" % num)
    plt.show()

def create_animation():
    """
    Create animation of vehicle movement (optional)
    """
    from matplotlib.animation import FuncAnimation
    
    # File paths
    base_path = "aichallenge/workspace/src/aichallenge_submit"
    osm_file = os.path.join(base_path, "aichallenge_submit_launch/map/lanelet2_map.osm")
    trajectory_30km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_30km.csv")
    trajectory_15km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_15km.csv")
    
    # Load data
    roads = parse_osm_map(osm_file)
    traj_30km = load_trajectory_data(trajectory_30km)
    traj_15km = load_trajectory_data(trajectory_15km)
    
    # Create animation plot
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Draw map
    road_color = '#8B8B8B'
    for road_points in roads:
        if len(road_points) > 2:
            try:
                road_array = np.array(road_points)
                road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, edgecolor='black', linewidth=0.5)
                ax.add_patch(road_patch)
            except Exception as e:
                continue
    
    # Draw trajectory lines
    line_30km, = ax.plot([], [], 'r-', linewidth=2, alpha=0.6, label='30km/h Trajectory')
    line_15km, = ax.plot([], [], 'b-', linewidth=2, alpha=0.6, label='15km/h Trajectory')
    
    # Vehicle position points
    point_30km, = ax.plot([], [], 'ro', markersize=8, label='30km/h Vehicle')
    point_15km, = ax.plot([], [], 'bo', markersize=8, label='15km/h Vehicle')
    
    # Axis settings
    all_x = np.concatenate([traj_30km[:, 0], traj_15km[:, 0]])
    all_y = np.concatenate([traj_30km[:, 1], traj_15km[:, 1]])
    
    x_margin = (all_x.max() - all_x.min()) * 0.05
    y_margin = (all_y.max() - all_y.min()) * 0.05
    
    ax.set_xlim(all_x.min() - x_margin, all_x.max() + x_margin)
    ax.set_ylim(all_y.min() - y_margin, all_y.max() + y_margin)
    ax.set_xlabel('X Coordinate (m)')
    ax.set_ylabel('Y Coordinate (m)')
    ax.set_title('Vehicle Trajectory Animation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    def animate(frame):
        # Update trajectories based on frame
        if frame < len(traj_30km):
            line_30km.set_data(traj_30km[:frame+1, 0], traj_30km[:frame+1, 1])
            point_30km.set_data([traj_30km[frame, 0]], [traj_30km[frame, 1]])
        
        if frame < len(traj_15km):
            line_15km.set_data(traj_15km[:frame+1, 0], traj_15km[:frame+1, 1])
            point_15km.set_data([traj_15km[frame, 0]], [traj_15km[frame, 1]])
        
        return line_30km, line_15km, point_30km, point_15km
    
    # Create animation
    anim = FuncAnimation(fig, animate, frames=min(len(traj_30km), len(traj_15km)), 
                        interval=50, blit=True, repeat=True)
    
    plt.tight_layout()
    plt.show()
    
    return anim

if __name__ == "__main__":
    print("Starting vehicle trajectory and course map visualization...")
    
    try:
        # Basic visualization
        visualize_trajectory_and_map()
        
        # Animation (optional)
        # create_animation()
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print("Please check the file paths.")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc() 