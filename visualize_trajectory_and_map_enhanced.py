#!/usr/bin/env python3
"""
Enhanced vehicle trajectory and course map visualization script
"""

import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np
from matplotlib.patches import Polygon
import os

def parse_osm_map(osm_file_path):
    """
    Parse OSM file to extract road shapes from Lanelet2 format with speed limits
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
    
    # Extract lanelet relations (roads with width and speed limits)
    roads = []
    for relation in root.findall('.//relation'):
        relation_type = None
        speed_limit = 15  # Default speed limit
        
        for tag in relation.findall('tag'):
            if tag.get('k') == 'type' and tag.get('v') == 'lanelet':
                relation_type = 'lanelet'
            elif tag.get('k') == 'speed_limit':
                try:
                    speed_limit = int(tag.get('v'))
                except:
                    speed_limit = 15
        
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
                        roads.append({
                            'points': polygon_points,
                            'speed_limit': speed_limit,
                            'left_way': left_way_id,
                            'right_way': right_way_id,
                            'centerline_way': centerline_way_id
                        })
    
    return roads

def load_trajectory_data(csv_file_path):
    """
    Load vehicle trajectory data from CSV file
    """
    df = pd.read_csv(csv_file_path)
    return df[['x', 'y']].values

def get_road_color(speed_limit):
    """
    Get color based on speed limit
    """
    if speed_limit <= 10:
        return '#FF6B6B'  # Light red
    elif speed_limit <= 20:
        return '#4ECDC4'  # Teal
    elif speed_limit <= 30:
        return '#45B7D1'  # Blue
    elif speed_limit <= 40:
        return '#96CEB4'  # Green
    else:
        return '#FFEAA7'  # Yellow

def visualize_trajectory_and_map_enhanced():
    """
    Enhanced visualization with speed-based coloring and detailed information
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
    
    # Create plot with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Plot 1: Basic visualization
    print("Drawing basic map...")
    road_count = 0
    speed_limits = set()
    
    for road in roads:
        road_points = road['points']
        speed_limit = road['speed_limit']
        speed_limits.add(speed_limit)
        
        if len(road_points) > 2:
            try:
                road_array = np.array(road_points)
                road_color = get_road_color(speed_limit)
                road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, edgecolor='black', linewidth=0.5)
                ax1.add_patch(road_patch)
                road_count += 1
            except Exception as e:
                print(f"Error creating road polygon: {e}")
                continue
    
    print(f"Drew {road_count} road polygons")
    print(f"Speed limits found: {sorted(speed_limits)}")
    
    # Draw trajectories on basic plot
    ax1.plot(traj_30km[:, 0], traj_30km[:, 1], 'r-', linewidth=3, label='30km/h Trajectory', alpha=0.8)
    ax1.plot(traj_15km[:, 0], traj_15km[:, 1], 'b-', linewidth=3, label='15km/h Trajectory', alpha=0.8)
    
    # Mark start and end points
    ax1.plot(traj_30km[0, 0], traj_30km[0, 1], 'ro', markersize=10, label='30km/h Start')
    ax1.plot(traj_30km[-1, 0], traj_30km[-1, 1], 'rs', markersize=10, label='30km/h End')
    ax1.plot(traj_15km[0, 0], traj_15km[0, 1], 'bo', markersize=10, label='15km/h Start')
    ax1.plot(traj_15km[-1, 0], traj_15km[-1, 1], 'bs', markersize=10, label='15km/h End')
    
    # Basic plot settings
    ax1.set_xlabel('X Coordinate (m)', fontsize=12)
    ax1.set_ylabel('Y Coordinate (m)', fontsize=12)
    ax1.set_title('Vehicle Trajectories and Course Map (Speed-based Coloring)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    # Plot 2: Detailed visualization with speed limit legend
    print("Drawing detailed map...")
    
    # Create legend for speed limits
    legend_elements = []
    for speed_limit in sorted(speed_limits):
        color = get_road_color(speed_limit)
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.7, 
                                           label=f'{speed_limit} km/h'))
    
    # Draw roads with speed-based coloring
    for road in roads:
        road_points = road['points']
        speed_limit = road['speed_limit']
        
        if len(road_points) > 2:
            try:
                road_array = np.array(road_points)
                road_color = get_road_color(speed_limit)
                road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, edgecolor='black', linewidth=0.5)
                ax2.add_patch(road_patch)
            except Exception as e:
                continue
    
    # Draw trajectories on detailed plot
    ax2.plot(traj_30km[:, 0], traj_30km[:, 1], 'r-', linewidth=3, label='30km/h Trajectory', alpha=0.8)
    ax2.plot(traj_15km[:, 0], traj_15km[:, 1], 'b-', linewidth=3, label='15km/h Trajectory', alpha=0.8)
    
    # Mark start and end points
    ax2.plot(traj_30km[0, 0], traj_30km[0, 1], 'ro', markersize=10, label='30km/h Start')
    ax2.plot(traj_30km[-1, 0], traj_30km[-1, 1], 'rs', markersize=10, label='30km/h End')
    ax2.plot(traj_15km[0, 0], traj_15km[0, 1], 'bo', markersize=10, label='15km/h Start')
    ax2.plot(traj_15km[-1, 0], traj_15km[-1, 1], 'bs', markersize=10, label='15km/h End')
    
    # Detailed plot settings
    ax2.set_xlabel('X Coordinate (m)', fontsize=12)
    ax2.set_ylabel('Y Coordinate (m)', fontsize=12)
    ax2.set_title('Detailed Course Map with Speed Limit Legend', fontsize=14, fontweight='bold')
    ax2.legend(handles=legend_elements, title='Speed Limits', fontsize=10, loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Set axis limits for both plots
    all_x = np.concatenate([traj_30km[:, 0], traj_15km[:, 0]])
    all_y = np.concatenate([traj_30km[:, 1], traj_15km[:, 1]])
    
    x_margin = (all_x.max() - all_x.min()) * 0.05
    y_margin = (all_y.max() - all_y.min()) * 0.05
    
    for ax in [ax1, ax2]:
        ax.set_xlim(all_x.min() - x_margin, all_x.max() + x_margin)
        ax.set_ylim(all_y.min() - y_margin, all_y.max() + y_margin)
    
    # Save and display
    plt.tight_layout()
    plt.savefig('trajectory_and_map_enhanced.png', dpi=300, bbox_inches='tight')
    print("Enhanced image saved: trajectory_and_map_enhanced.png")
    plt.show()

def create_speed_analysis():
    """
    Create speed analysis visualization
    """
    # File paths
    base_path = "aichallenge/workspace/src/aichallenge_submit"
    osm_file = os.path.join(base_path, "aichallenge_submit_launch/map/lanelet2_map.osm")
    trajectory_30km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_30km.csv")
    trajectory_15km = os.path.join(base_path, "simple_trajectory_generator/data/raceline_awsim_15km.csv")
    
    # Load data
    roads = parse_osm_map(osm_file)
    traj_30km = load_trajectory_data(trajectory_30km)
    traj_15km = load_trajectory_data(trajectory_15km)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Draw roads with speed-based coloring
    speed_stats = {}
    for road in roads:
        road_points = road['points']
        speed_limit = road['speed_limit']
        
        if speed_limit not in speed_stats:
            speed_stats[speed_limit] = 0
        speed_stats[speed_limit] += 1
        
        if len(road_points) > 2:
            try:
                road_array = np.array(road_points)
                road_color = get_road_color(speed_limit)
                road_patch = Polygon(road_array, facecolor=road_color, alpha=0.7, edgecolor='black', linewidth=0.5)
                ax.add_patch(road_patch)
            except Exception as e:
                continue
    
    # Draw trajectories
    ax.plot(traj_30km[:, 0], traj_30km[:, 1], 'r-', linewidth=3, label='30km/h Trajectory', alpha=0.8)
    ax.plot(traj_15km[:, 0], traj_15km[:, 1], 'b-', linewidth=3, label='15km/h Trajectory', alpha=0.8)
    
    # Create legend
    legend_elements = []
    for speed_limit in sorted(speed_stats.keys()):
        color = get_road_color(speed_limit)
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.7, 
                                           label=f'{speed_limit} km/h ({speed_stats[speed_limit]} segments)'))
    
    # Plot settings
    ax.set_xlabel('X Coordinate (m)', fontsize=12)
    ax.set_ylabel('Y Coordinate (m)', fontsize=12)
    ax.set_title('Course Map with Speed Limit Analysis', fontsize=16, fontweight='bold')
    ax.legend(handles=legend_elements, title='Speed Limits', fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Set axis limits
    all_x = np.concatenate([traj_30km[:, 0], traj_15km[:, 0]])
    all_y = np.concatenate([traj_30km[:, 1], traj_15km[:, 1]])
    
    x_margin = (all_x.max() - all_x.min()) * 0.05
    y_margin = (all_y.max() - all_y.min()) * 0.05
    
    ax.set_xlim(all_x.min() - x_margin, all_x.max() + x_margin)
    ax.set_ylim(all_y.min() - y_margin, all_y.max() + y_margin)
    
    # Save and display
    plt.tight_layout()
    plt.savefig('speed_analysis.png', dpi=300, bbox_inches='tight')
    print("Speed analysis image saved: speed_analysis.png")
    plt.show()

if __name__ == "__main__":
    print("Starting enhanced vehicle trajectory and course map visualization...")
    
    try:
        # Enhanced visualization
        visualize_trajectory_and_map_enhanced()
        
        # Speed analysis
        create_speed_analysis()
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print("Please check the file paths.")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc() 