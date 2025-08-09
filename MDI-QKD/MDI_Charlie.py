# MDI_Charlie.py — Performs Bell-State Measurement (BSM) with realistic loss tracking and logs BSM success

from netsquid.protocols import NodeProtocol
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import INSTR_CNOT, INSTR_H, INSTR_MEASURE
from netsquid.qubits import discard

class BSMProgram(QuantumProgram):
    def __init__(self):
        super().__init__()

    def program(self):
        self.apply(INSTR_CNOT, [0, 1])
        self.apply(INSTR_H, 0)
        self.apply(INSTR_MEASURE, [0], output_key="m0", physical=True)
        self.apply(INSTR_MEASURE, [1], output_key="m1", physical=True)
        yield self.run()

class CharlieProtocol(NodeProtocol):
    def __init__(self, node, processor, num_bits, perf):
        super().__init__(node)
        self.node = node
        self.processor = processor
        self.num_bits = num_bits
        self.perf = perf
        self.success_indices = []

    def run(self):
        count = 0
        while count < self.num_bits:
            yield self.await_port_input(self.node.ports["qin_a"])
            msg_a = self.node.ports["qin_a"].rx_input()

            yield self.await_port_input(self.node.ports["qin_b"])
            msg_b = self.node.ports["qin_b"].rx_input()

            if not msg_a or not msg_b:
                continue

            q_a = msg_a.items[0]
            q_b = msg_b.items[0]

            self.processor.put([q_a, q_b])

            bsm = BSMProgram()
            self.processor.execute_program(bsm, qubit_mapping=[0, 1])
            yield self.await_program(self.processor)

            m0 = bsm.output["m0"]
            m1 = bsm.output["m1"]

            # Only count as "received" if BSM succeeded (both measurements valid)
            if m0 is not None and m1 is not None:
                self.perf.record_qubit_received("alice")
                self.perf.record_qubit_received("bob")
                self.perf.record_classical_message()  # simulate BSM broadcast
                self.success_indices.append(count)

            discard(q_a)
            discard(q_b)
            count += 1
