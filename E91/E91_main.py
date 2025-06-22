import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.components.instructions import INSTR_MEASURE, INSTR_MEASURE_X, INSTR_H, INSTR_CNOT
from netsquid.components.models.qerrormodels import FibreLossModel, DepolarNoiseModel
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.cchannel import ClassicalChannel
from netsquid.components.models import FibreDelayModel
from netsquid.qubits.qubitapi import create_qubits
from netsquid.components.qprogram import QuantumProgram

import E91_Alice
import E91_Bob
from performance import PerformanceTracker

class BellPairProgram(QuantumProgram):
    def __init__(self):
        super().__init__()

    def program(self):
        self.apply(INSTR_H, 0)
        self.apply(INSTR_CNOT, [0, 1])
        yield self.run()

def run_e91():
    ns.sim_reset()
    NUM_PAIRS = 1000
    perf = PerformanceTracker(num_pairs=NUM_PAIRS)
    perf.start_simulation()

    alice = Node("Alice", port_names=["qin", "c1", "c2"])
    bob = Node("Bob", port_names=["qin", "c1", "c2"])
    source = Node("EPR_Source", port_names=["qout0", "qout1"])

    processorA = QuantumProcessor("procA", num_positions=NUM_PAIRS,
        phys_instructions=[
            PhysicalInstruction(INSTR_MEASURE, duration=3700),
            PhysicalInstruction(INSTR_MEASURE_X, duration=3700)
        ])
    processorB = QuantumProcessor("procB", num_positions=NUM_PAIRS,
        phys_instructions=[
            PhysicalInstruction(INSTR_MEASURE, duration=3700),
            PhysicalInstruction(INSTR_MEASURE_X, duration=3700)
        ])

    qchannel_alice = QuantumChannel("qchannel_alice", length=10,
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })

    qchannel_bob = QuantumChannel("qchannel_bob", length=10,
        models={
            "delay_model": FibreDelayModel(c=2e5),
            "fibre_loss": FibreLossModel(p_loss_init=0.0, p_loss_length=0.2),
            "depolar_model": DepolarNoiseModel(depolar_rate=0.01)
        })

    source.ports["qout0"].connect(qchannel_alice.ports["send"])
    source.ports["qout1"].connect(qchannel_bob.ports["send"])
    qchannel_alice.ports["recv"].connect(alice.ports["qin"])
    qchannel_bob.ports["recv"].connect(bob.ports["qin"])

    cchannel_B2A = ClassicalChannel("cB2A", length=10)
    cchannel_A2B = ClassicalChannel("cA2B", length=10)
    bob.ports["c1"].connect(cchannel_B2A.ports["send"])
    alice.ports["c1"].connect(cchannel_B2A.ports["recv"])
    alice.ports["c2"].connect(cchannel_A2B.ports["send"])
    bob.ports["c2"].connect(cchannel_A2B.ports["recv"])

    start_bob = time.time()
    bob_protocol = E91_Bob.BobProtocol(bob, processorB, NUM_PAIRS, ["qin", "c1", "c2"], perf)
    bob_protocol.start()
    start_alice = time.time()
    alice_protocol = E91_Alice.AliceProtocol(alice, processorA, NUM_PAIRS, ["qin", "c1", "c2"], perf)
    alice_protocol.start()
    perf.set_sync_time(abs(start_bob - start_alice))

    entangler = QuantumProcessor("Entangler", num_positions=2,
        phys_instructions=[
            PhysicalInstruction(INSTR_H, duration=1),
            PhysicalInstruction(INSTR_CNOT, duration=1)
        ])

    for i in range(NUM_PAIRS):
        q1, q2 = create_qubits(2)
        entangler.put([q1, q2])
        bell_prog = BellPairProgram()
        entangler.execute_program(bell_prog)
        ns.sim_run()
        qout = entangler.pop([0, 1])
        perf.record_epr_sent()
        source.ports["qout0"].tx_output(qout[0])
        source.ports["qout1"].tx_output(qout[1])

    ns.sim_run()

    perf.received_qubits_alice = len(alice_protocol.key)
    perf.received_qubits_bob = len(bob_protocol.key)
    min_len = min(len(alice_protocol.key), len(bob_protocol.key))
    mismatches = sum(1 for i in range(min_len) if alice_protocol.key[i] != bob_protocol.key[i])
    perf.record_basis_match(min_len)
    perf.record_mismatches(mismatches)
    perf.end_simulation()

    print("\n[E91] Alice Key:", alice_protocol.key)
    print("\n[E91] Bob Key:  ", bob_protocol.key)
    perf.report()

if __name__ == "__main__":
    run_e91()
