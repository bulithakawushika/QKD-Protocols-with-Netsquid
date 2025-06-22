# MDI_Bob.py — Prepares qubits and sends to Charlie

from netsquid.protocols import NodeProtocol
from netsquid.qubits.qubitapi import create_qubits, operate
from netsquid.qubits.operators import H, X
import random

class BobProtocol(NodeProtocol):
    def __init__(self, node, num_bits, perf):
        super().__init__(node)
        self.node = node
        self.num_bits = num_bits
        self.perf = perf
        self.key = ""

    def run(self):
        for _ in range(self.num_bits):
            bit = random.randint(0, 1)
            basis = random.randint(0, 1)  # 0: Z, 1: X

            q = create_qubits(1)[0]

            if bit == 1:
                operate(q, X)
            if basis == 1:
                operate(q, H)

            self.node.ports["qout"].tx_output(q)
            self.perf.record_epr_sent()

            # Save bit and basis for post-processing
            self.key += str(bit)
            yield self.await_timer(1e-6)
