# benchmarks/math_opt.py

def sum_evens_original(n):
    """Iterative summation of even numbers up to n."""
    res = 0
    for i in range(n):
        if i % 2 == 0:
            res += i
    return res

def sum_evens_mutant(n):
    """
    Optimized analytical solution for summing even numbers.
    NSEV uses induction to prove this equivalent to the loop above.
    """
    # Assuming m is the count of even numbers
    m = (n - 1) // 2
    return m * (m + 1)
