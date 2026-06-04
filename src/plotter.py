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