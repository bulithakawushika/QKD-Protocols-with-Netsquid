import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.components.qprogram import QuantumProgram
from functions import Random_basis_gen

class QMeasure(QuantumProgram):
    def __init__(self, basis_list):
        super().__init__()
        self.basis_list = basis_list

    def program(self):
        for i, basis in enumerate(self.basis_list):
            if basis == 0:
                self.apply("MEASURE", i)
            elif basis == 1:
                self.apply("H", i)
                self.apply("MEASURE", i)
        yield self.run()

class BobProtocol(NodeProtocol):
    def __init__(self, node, processor, num_bits):
        super().__init__(node)
        self.processor = processor
        self.num_bits = num_bits
        self.bases = []
        self.results = []

    def run(self):
        self.bases = Random_basis_gen(self.num_bits)
        count = 0
        while count < self.num_bits:
            yield self.await_port_input(self.node.ports["qin"])
            qubit = self.node.ports["qin"].rx_input().items[0]
            pos = self.processor.put(qubit)
            if pos is None:
                continue
            idx = pos[0]
            print(f"[Bob] Received qubit {count+1} in basis {self.bases[count]}")
            prog = QMeasure([self.bases[count]])
            yield self.processor.execute_program(prog, qubit_mapping=[idx])
            res = prog.output[str(idx)][0]
            self.results.append(res)
            count += 1
        print(f"[Bob] Results collected: {len(self.results)}")
