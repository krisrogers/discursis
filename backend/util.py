"""Utility functions."""
import numpy as np


def generate_term_vectors(terms):
    """Generate one-hot encoded term vectors for list of `terms`."""
    base = np.zeros(len(terms))
    term_vectors = {}
    for i, term in enumerate(terms):
        term_vectors[term] = np.copy(base)
        term_vectors[term][i] = 1

    return term_vectors
