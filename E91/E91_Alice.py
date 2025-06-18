from netsquid.protocols import NodeProtocol
from netsquid.components import QuantumProgram
from netsquid.components.instructions import INSTR_MEASURE, INSTR_MEASURE_X

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from functions import Compare_basis, Random_basis_gen

class QG_A_measure(QuantumProgram):
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

class AliceProtocol(NodeProtocol):
    def __init__(self, node, processor, num_bits, port_names):
        super().__init__()
        self.node = node
        self.processor = processor
        self.num_bits = num_bits
        self.portQ, self.portC1, self.portC2 = port_names
        self.basisList = Random_basis_gen(num_bits)
        self.loc_measRes = []
        self.key = ""

    def run(self):
        all_qubits = []
        while len(all_qubits) < self.num_bits:
            yield self.await_port_input(self.node.ports[self.portQ])
            qubits = self.node.ports[self.portQ].rx_input().items
            if qubits:
                print(f"[Alice] Received {len(qubits)} qubit(s)")
                all_qubits.extend(qubits)

        self.processor.put(all_qubits)

        measure_program = QG_A_measure(self.basisList)
        positions = list(range(self.num_bits))
        self.processor.execute_program(measure_program, qubit_mapping=positions)
        yield self.await_program(self.processor)

        for i in range(self.num_bits):
            self.loc_measRes.append(measure_program.output[str(i)][0])

        yield self.await_port_input(self.node.ports[self.portC1])
        basis_B = self.node.ports[self.portC1].rx_input().items
        print("[Alice] Basis from Bob:", basis_B)

        self.node.ports[self.portC2].tx_output(self.basisList)

        self.loc_measRes = Compare_basis(self.basisList, basis_B, self.loc_measRes)
        self.key = ''.join(map(str, self.loc_measRes))
        print("[Alice] Final key:", self.key)
