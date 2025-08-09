# MDI_main.py — Realistic MDI-QKD with Final Key Extraction and Basis Sifting

import netsquid as ns
from netsquid.nodes import Node
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.models.qerrormodels import FibreLossModel, DepolarNoiseModel
from netsquid.components.models.delaymodels import FibreDelayModel
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.components.instructions import INSTR_MEASURE, INSTR_MEASURE_X, INSTR_H, INSTR_CNOT
from netsquid.protocols import NodeProtocol
from netsquid.qubits.qubitapi import create_qubits, operate, discard
import random, time

from performance import PerformanceTracker
import MDI_Alice, MDI_Bob, MDI_Charlie

NUM_BITS = 1000

def setup_network():
    alice = Node("Alice", port_names=["qout"])
    bob = Node("Bob", port_names=["qout"])
    charlie = Node("Charlie", port_names=["qin_a", "qin_b"])

    qchannel_a = QuantumChannel("A_to_C", length=5,
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })

    qchannel_b = QuantumChannel("B_to_C", length=5,
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })

    alice.ports["qout"].connect(qchannel_a.ports["send"])
    charlie.ports["qin_a"].connect(qchannel_a.ports["recv"])

    bob.ports["qout"].connect(qchannel_b.ports["send"])
    charlie.ports["qin_b"].connect(qchannel_b.ports["recv"])

    return alice, bob, charlie

def run_mdi():
    ns.sim_reset()
    perf = PerformanceTracker(num_pairs=NUM_BITS)
    perf.start_simulation()

    alice, bob, charlie = setup_network()

    proc_charlie = QuantumProcessor("CharlieProc", num_positions=2,
        phys_instructions=[
            PhysicalInstruction(INSTR_H, duration=1),
            PhysicalInstruction(INSTR_CNOT, duration=1),
            PhysicalInstruction(INSTR_MEASURE, duration=3700)
        ])

    alice_protocol = MDI_Alice.AliceProtocol(alice, NUM_BITS, perf)
    bob_protocol = MDI_Bob.BobProtocol(bob, NUM_BITS, perf)
    charlie_protocol = MDI_Charlie.CharlieProtocol(charlie, proc_charlie, NUM_BITS, perf)

    start_bob = time.time()
    bob_protocol.start()
    start_alice = time.time()
    alice_protocol.start()
    perf.set_sync_time(abs(start_bob - start_alice))

    charlie_protocol.start()

    ns.sim_run()

    sift_indices = charlie_protocol.success_indices
    filtered_indices = [i for i in sift_indices if alice_protocol.bases[i] == bob_protocol.bases[i]
                        and i < len(alice_protocol.key) and i < len(bob_protocol.key)]

    final_alice_key = ''.join([alice_protocol.key[i] for i in filtered_indices])
    final_bob_key   = ''.join([bob_protocol.key[i] for i in filtered_indices])

    min_len = min(len(final_alice_key), len(final_bob_key))
    mismatches = sum(1 for i in range(min_len) if final_alice_key[i] != final_bob_key[i])

    perf.record_basis_match(min_len)
    perf.record_mismatches(mismatches)
    perf.end_simulation()

    print("\n[MDI] Final Alice Key:", final_alice_key)
    print("\n[MDI] Final Bob Key:  ", final_bob_key)
    perf.report()

if __name__ == '__main__':
    run_mdi()
