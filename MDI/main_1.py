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
    # Create nodes
    alice = Node("Alice", port_names=["qout"])
    bob = Node("Bob", port_names=["qout"])
    charlie = Node("Charlie", port_names=["qin_a", "qin_b"])

    # Connect quantum channels with realistic models
    qchannel_a = QuantumChannel("A_to_C", length=10,
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })

    qchannel_b = QuantumChannel("B_to_C", length=10,
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

    # Instantiate protocols
    alice_protocol = MDI_Alice.AliceProtocol(alice, NUM_BITS, perf)
    bob_protocol = MDI_Bob.BobProtocol(bob, NUM_BITS, perf)
    charlie_protocol = MDI_Charlie.CharlieProtocol(charlie, proc_charlie, NUM_BITS, perf)

    # Start protocols
    start_bob = time.time()
    bob_protocol.start()
    start_alice = time.time()
    alice_protocol.start()
    perf.set_sync_time(abs(start_bob - start_alice))

    charlie_protocol.start()

    ns.sim_run()

    # Reconcile keys (dummy — real reconciliation to be implemented)
    alice_key = alice_protocol.key
    bob_key = bob_protocol.key

    mismatches = sum(a != b for a, b in zip(alice_key, bob_key))
    perf.record_basis_match(len(alice_key))
    perf.record_mismatches(mismatches)
    perf.end_simulation()

    print("\n[MDI] Alice Key:", alice_key)
    print("\n[MDI] Bob Key:  ", bob_key)
    perf.report()


if __name__ == '__main__':
    run_mdi()
