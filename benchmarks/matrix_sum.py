# benchmarks/matrix_sum.py

def matrix_sum_original(matrix, N, M):
    """Original nested loop for matrix summation."""
    total = 0
    for i in range(N):
        for j in range(M):
            total += matrix[i][j]
    return total

def matrix_sum_mutant(matrix, N, M):
    """
    Mutant with swapped loop headers.
    Commonly equivalent in pure summation contexts.
    """
    total = 0
    for j in range(M):
        for i in range(N):
            total += matrix[i][j]
    return total
