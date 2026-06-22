import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOTS_DIR = os.path.join(PROJECT_ROOT, 'plots')


def plot_speed_graph(telemetry):

    plt.figure(figsize=(12, 6))

    plt.plot(
        telemetry["Distance"],
        telemetry["Speed"]
    )

    plt.title("Speed vs Distance")

    plt.xlabel("Distance (m)")
    plt.ylabel("Speed (km/h)")

    plt.grid()

    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(
        os.path.join(PLOTS_DIR, "speed_graph.png")
    )

    plt.close()


def plot_control_analysis(telemetry):
    """Create a single readable chart for throttle, brake, RPM and gear use."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
    distance = telemetry["Distance"]

    axes[0, 0].plot(distance, telemetry["Throttle"], color="#E10600", linewidth=1.4)
    axes[0, 0].set_title("Throttle")
    axes[0, 0].set_ylabel("Percent")

    brake = telemetry["Brake"].astype(int) * 100 if "Brake" in telemetry else 0
    axes[0, 1].step(distance, brake, color="#2864DC", linewidth=1.2, where="mid")
    axes[0, 1].set_title("Brake Application")
    axes[0, 1].set_ylabel("Percent")

    axes[1, 0].plot(distance, telemetry["RPM"], color="#7C3AED", linewidth=1.2)
    axes[1, 0].set_title("Engine RPM")
    axes[1, 0].set_ylabel("RPM")

    axes[1, 1].step(distance, telemetry["nGear"], color="#059669", linewidth=1.2, where="mid")
    axes[1, 1].set_title("Gear Usage")
    axes[1, 1].set_ylabel("Gear")

    for axis in axes.flat:
        axis.set_xlabel("Distance (m)")
        axis.grid(alpha=0.25)

    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, "control_analysis.png"), dpi=150)
    plt.close()
