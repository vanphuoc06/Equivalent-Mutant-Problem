# benchmarks/sample_m.py

def compute_sum(n):
    """
    Calculates the sum of integers from 0 to n-1 using the arithmetic series formula.
    This is an EQUIVALENT mutant to sample_p.py.
    """
    if n <= 0:
        return 0
    # Formula for sum of 0 to n-1 is (n-1)*n / 2
    total = (n * (n - 1)) // 2
    return total
