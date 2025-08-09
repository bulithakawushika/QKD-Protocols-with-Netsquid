import subprocess
import re
import matplotlib.pyplot as plt
import os

# Define protocol mapping to folder and file names
PROTOCOLS = {
    "BB84": "BB84/BB84_main.py",
    "E91": "E91/E91_main.py",
    "MDI-QKD": "MDI_QKD/MDI_main.py"
}

# Metrics to capture
METRICS = [
    "Raw Key Rate",
    "QBER",
    "Latency",
    "Channel Loss Rate",
    "Throughput",
    "Communication Overhead",
    "Synchronization Time",
    "Computation Time/Round"
]

# Units for plotting
UNITS = {
    "Raw Key Rate": "qubits",
    "QBER": "%",
    "Latency": "seconds",
    "Channel Loss Rate": "%",
    "Throughput": "qubits/sec",
    "Communication Overhead": "messages",
    "Synchronization Time": "seconds",
    "Computation Time/Round": "seconds"
}

# Regex patterns for extracting metrics
PATTERNS = {
    "Raw Key Rate": r"Raw Key Rate:\s+(\d+)",
    "QBER": r"QBER:\s+([\d.]+)",
    "Latency": r"Latency:\s+([\d.]+)",
    "Channel Loss Rate": r"Channel Loss Rate:\s+([\d.]+)",
    "Throughput": r"Throughput:\s+([\d.]+)",
    "Communication Overhead": r"Communication Overhead:\s+(\d+)",
    "Synchronization Time": r"Synchronization Time:\s+([\d.]+)",
    "Computation Time/Round": r"Computation Time/Round:\s+([\d.]+)"
}

# Create plots directory
os.makedirs("plots", exist_ok=True)


def run_protocol(protocol_file, runs=100):
    """Run a given protocol file multiple times and return metrics data."""
    results = {metric: [] for metric in METRICS}

    for i in range(runs):
        proc = subprocess.run(
            ["python3", protocol_file],
            capture_output=True,
            text=True
        )
        output = proc.stdout

        for metric in METRICS:
            match = re.search(PATTERNS[metric], output)
            if match:
                val = float(match.group(1))
                if metric in ["Raw Key Rate", "Communication Overhead"]:
                    val = int(val)
                results[metric].append(val)

        print(f"[{protocol_file}] Run {i+1}/{runs} completed.")

    return results


def plot_single_protocol(protocol_name, data):
    """Plot individual metrics for one protocol."""
    for metric in METRICS:
        plt.figure()
        plt.plot(range(1, len(data[metric]) + 1), data[metric], marker="o", markersize=3)
        plt.title(f"{protocol_name} - {metric}")
        plt.xlabel("Run")
        plt.ylabel(f"{metric} ({UNITS[metric]})")
        plt.grid(True)
        plt.savefig(f"plots/{protocol_name}_{metric.replace(' ', '_')}.png")
        plt.close()


def plot_all_protocols(all_data):
    """Plot one comparison graph per metric for all protocols."""
    for metric in METRICS:
        plt.figure()
        for protocol_name, results in all_data.items():
            plt.plot(
                range(1, len(results[metric]) + 1),
                results[metric],
                label=protocol_name,
                marker="o",
                markersize=3
            )
        plt.title(f"Comparison - {metric}")
        plt.xlabel("Run")
        plt.ylabel(f"{metric} ({UNITS[metric]})")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"plots/Comparison_{metric.replace(' ', '_')}.png")
        plt.close()


if __name__ == "__main__":
    print("Select a protocol:")
    print("1. BB84")
    print("2. E91")
    print("3. MDI-QKD")
    print("4. All Protocols")
    choice = int(input("Enter choice: ").strip())

    if choice in [1, 2, 3]:
        protocol_name = list(PROTOCOLS.keys())[choice - 1]
        file_path = PROTOCOLS[protocol_name]
        results = run_protocol(file_path)
        plot_single_protocol(protocol_name, results)
        print(f"Plots saved in 'plots/' for {protocol_name}.")

    elif choice == 4:
        all_results = {}
        for protocol_name, file_path in PROTOCOLS.items():
            all_results[protocol_name] = run_protocol(file_path)
        plot_all_protocols(all_results)
        print("Comparison plots saved in 'plots/' for all protocols.")

    else:
        print("Invalid choice.")
