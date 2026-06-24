# benchmarks/sample_p.py

def compute_sum(n):
    """
    Calculates the sum of integers from 0 to n-1.
    Used as the original program (P_orig) for NSEV verification.
    """
    total = 0
    for i in range(n):
        total += i
    return total
