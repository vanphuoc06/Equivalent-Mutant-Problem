# benchmarks/parity_check.py

def is_even_original(n):
    """Original implementation using modulo operator."""
    return n % 2 == 0

def is_even_mutant(n):
    """
    Mutant implementation using bitwise AND.
    Semantically equivalent to (n % 2 == 0) for integers.
    """
    return (n & 1) == 0

# NSEV should prove: forall n: (n % 2 == 0) == ((n & 1) == 0)
