# performance.py — Shared for BB84, E91, MDI-QKD

import time

class PerformanceTracker:
    def __init__(self, num_pairs):
        self.sent_epr_pairs = 0
        self.received_qubits_alice = 0
        self.received_qubits_bob = 0
        self.mismatches = 0
        self.matched_bases = 0
        self.classical_msgs = 0
        self.start_time = 0
        self.end_time = 0
        self.sync_time = 0
        self.num_pairs = num_pairs

    def start_simulation(self):
        self.start_time = time.time()

    def end_simulation(self):
        self.end_time = time.time()

    def record_epr_sent(self):
        self.sent_epr_pairs += 1

    def record_qubit_received(self, party):
        if party == "alice":
            self.received_qubits_alice += 1
        elif party == "bob":
            self.received_qubits_bob += 1

    def record_mismatches(self, count):
        self.mismatches += count

    def record_basis_match(self, count):
        self.matched_bases += count

    def record_classical_message(self):
        self.classical_msgs += 1

    def set_sync_time(self, delay):
        self.sync_time = delay

    def report(self):
        total_time = self.end_time - self.start_time
        key_len = self.matched_bases
        qber = (self.mismatches / key_len * 100) if key_len else 0
        raw_key_rate = key_len
        throughput = key_len / total_time if total_time > 0 else 0
        loss_rate_alice = 1 - (self.received_qubits_alice / self.sent_epr_pairs) if self.sent_epr_pairs else 0
        loss_rate_bob = 1 - (self.received_qubits_bob / self.sent_epr_pairs) if self.sent_epr_pairs else 0
        latency = total_time
        comp_time = 0  # Placeholder if you measure program execution time

        print("\n=== MDI-QKD Protocol Performance Report ===")
        print(f"Raw Key Rate:           {raw_key_rate} bits")
        print(f"QBER:                   {qber:.2f}%")
        print(f"Latency:                {latency:.3f} seconds")
        print(f"Channel Loss Rate:      Alice={loss_rate_alice*100:.2f}%, Bob={loss_rate_bob*100:.2f}%")
        print(f"Throughput:             {throughput:.2f} bits/sec")
        print(f"Communication Overhead: {self.classical_msgs} messages")
        print(f"Synchronization Time:   {self.sync_time:.6f} seconds")
        print(f"Computation Time/Round: {comp_time:.6f} seconds")
        print("==========================================")
