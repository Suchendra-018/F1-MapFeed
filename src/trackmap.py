import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os

# Get project root for saving plots
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOTS_DIR = os.path.join(PROJECT_ROOT, 'plots')


def create_track_map(lap):
    """Plot basic circuit layout from lap position data"""
    position_data = lap.get_pos_data()

    plt.figure(figsize=(8, 8))
    plt.plot(
        position_data["X"],
        position_data["Y"],
        linewidth=2
    )

    plt.title("Circuit Layout")
    plt.axis("equal")
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, "track_map.png"))
    plt.close()


def create_speed_heatmap(lap, telemetry):
    """
    Plot track circuit with speed data colored as a heatmap
    Shows fast sections in green, slow sections in red
    """
    position_data = lap.get_pos_data()
    
    # Align telemetry and position data lengths
    min_len = min(len(position_data), len(telemetry))
    x = position_data["X"].values[:min_len]
    y = position_data["Y"].values[:min_len]
    speeds = telemetry["Speed"].values[:min_len]
    
    # Normalize speeds for colormap
    norm = mcolors.Normalize(vmin=speeds.min(), vmax=speeds.max())
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Draw line segments colored by speed
    for i in range(len(x) - 1):
        speed_color = plt.cm.RdYlGn(norm(speeds[i]))
        ax.plot(
            x[i:i+2],
            y[i:i+2],
            color=speed_color,
            linewidth=3,
            solid_capstyle='round'
        )
    
    ax.set_aspect('equal')
    ax.set_title(f"Speed Heatmap - {lap.Driver}", fontsize=14, fontweight='bold')
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Speed (km/h)', rotation=270, labelpad=20)
    
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, "speed_heatmap.png"), dpi=150)
    plt.close()