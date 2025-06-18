import random

def Random_basis_gen(n):
    """Generate a list of n random bases (0, 1, or 2)."""
    return [random.randint(0, 2) for _ in range(n)]

def Compare_basis(basisA, basisB, measRes):
    """Compare two basis lists and return matching bits from measRes."""
    print("[Compare_basis] Matching basis indices:")
    key = []
    for i in range(len(basisA)):
        if i < len(basisB) and basisA[i] == basisB[i]:
            print(f"  ✓ Match at index {i} → bit {measRes[i]}")
            key.append(measRes[i])
    return key
