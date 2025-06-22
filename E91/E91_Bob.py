# E91_Bob.py with perf tracking for classical messages (transmissions only)

from netsquid.protocols import NodeProtocol
from netsquid.components import QuantumProgram
from netsquid.components.instructions import INSTR_MEASURE, INSTR_MEASURE_X

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from functions import Random_basis_gen, Compare_basis

class QG_B_measure(QuantumProgram):
    def __init__(self, basisList):
        self.basisList = basisList
        super().__init__()

    def program(self):
        for i, basis in enumerate(self.basisList):
            if basis == 0:
                self.apply(INSTR_MEASURE, [i], output_key=str(i), physical=True)
            else:
                self.apply(INSTR_MEASURE_X, [i], output_key=str(i), physical=True)
        yield self.run(parallel=True)

class BobProtocol(NodeProtocol):
    def __init__(self, node, processor, num_bits, port_names, perf):
        super().__init__()
        self.node = node
        self.processor = processor
        self.num_bits = num_bits
        self.portQ, self.portC1, self.portC2 = port_names
        self.perf = perf
        self.basisList = Random_basis_gen(num_bits)
        self.loc_measRes = []
        self.key = ""

    def run(self):
        all_qubits = []
        while len(all_qubits) < self.num_bits:
            yield self.await_port_input(self.node.ports[self.portQ])
            qubits = self.node.ports[self.portQ].rx_input().items
            if qubits:
                all_qubits.extend(qubits)

        self.processor.put(all_qubits)

        measure_program = QG_B_measure(self.basisList)
        positions = list(range(self.num_bits))
        self.processor.execute_program(measure_program, qubit_mapping=positions)
        yield self.await_program(self.processor)

        for i in range(self.num_bits):
            self.loc_measRes.append(measure_program.output[str(i)][0])

        self.node.ports[self.portC1].tx_output(self.basisList)
        self.perf.record_classical_message()  # Only transmission counted

        yield self.await_port_input(self.node.ports[self.portC2])
        basis_A = self.node.ports[self.portC2].rx_input().items

        self.loc_measRes = Compare_basis(self.basisList, basis_A, self.loc_measRes)
        self.key = ''.join(map(str, self.loc_measRes))
