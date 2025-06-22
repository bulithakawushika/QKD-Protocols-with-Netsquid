import netsquid as ns
from netsquid.components import QuantumChannel, QuantumProcessor, PhysicalInstruction
from netsquid.components.instructions import INSTR_MEASURE
from netsquid.components.models import FibreLossModel, DepolarNoiseModel, FibreDelayModel
from netsquid.nodes import Node
from netsquid.qubits import create_qubits, operate, measure, Z
from netsquid.qubits.operators import H, X
from performance import PerformanceTracker
import random

NUM_BITS = 1000

def random_bits(n):
    return [random.randint(0, 1) for _ in range(n)]

def run_bb84():
    ns.sim_reset()
    perf = PerformanceTracker(num_pairs=NUM_BITS)
    perf.start_simulation()

    # Create nodes
    alice = Node("Alice", port_names=["qout"])
    bob = Node("Bob", port_names=["qin"])

    # Create quantum processors
    procA = QuantumProcessor("procA", num_positions=NUM_BITS,
        phys_instructions=[
            PhysicalInstruction(INSTR_MEASURE, duration=3700)
        ])
    procB = QuantumProcessor("procB", num_positions=NUM_BITS,
        phys_instructions=[
            PhysicalInstruction(INSTR_MEASURE, duration=3700)
        ])

    # Quantum channel with realistic fiber models
    qchannel = QuantumChannel("qchannel", length=10,  # 10 km fiber
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })
    alice.ports["qout"].connect(qchannel.ports["send"])
    bob.ports["qin"].connect(qchannel.ports["recv"])

    # Generate random bits and bases
    alice_bits = random_bits(NUM_BITS)
    alice_bases = random_bits(NUM_BITS)
    bob_bases = random_bits(NUM_BITS)
    bob_results = []

    for i in range(NUM_BITS):
        bit = alice_bits[i]
        basis = alice_bases[i]
        bob_basis = bob_bases[i]

        # Prepare qubit
        qubit = create_qubits(1)[0]
        if bit == 1:
            operate(qubit, X)
        if basis == 1:
            operate(qubit, H)

        procA.put(qubit)
        tx_qubit = procA.pop(0)
        alice.ports["qout"].tx_output(tx_qubit)
        perf.record_epr_sent()

        ns.sim_run()

        msg = bob.ports["qin"].rx_input()
        if msg is None:
            continue

        qubit_bob = msg.items[0]
        perf.record_qubit_received("bob")

        # Apply Bob’s basis
        if bob_basis == 1:
            operate(qubit_bob, H)

        m, _ = measure(qubit_bob, observable=Z)
        bob_results.append(int(m))

    # Compare bases and extract keys
    match_indices = [i for i in range(NUM_BITS) if alice_bases[i] == bob_bases[i]]
    valid_indices = [i for i in match_indices if i < len(bob_results)]
    alice_key = [alice_bits[i] for i in valid_indices]
    bob_key = [bob_results[i] for i in valid_indices]

    mismatches = sum(a != b for a, b in zip(alice_key, bob_key))
    perf.record_basis_match(len(valid_indices))
    perf.record_mismatches(mismatches)
    perf.end_simulation()

    print(f"\n[BB84] Alice key: {''.join(map(str, alice_key))}")
    print(f"\n[BB84] Bob key:   {''.join(map(str, bob_key))}")
    perf.report()

if __name__ == "__main__":
    run_bb84()
