from functools import reduce

import numpy as np
from numpy.testing import assert_allclose
from qiskit.quantum_info import random_density_matrix

from mps_tomo.uncert import pauli_proj, R_hat, iteration
from mps_tomo.utils import pauli_group


def test_pauli_proj():
    NUM_QUBITS = 3
    SEED = 7777
    TOL = 100 * np.spacing(np.complex128(1.0).real)

    dens_mat = random_density_matrix(2 ** NUM_QUBITS, seed=SEED)
    reconstructed = reduce(
        np.add, (pauli_proj(dens_mat, p) for p in pauli_group(NUM_QUBITS))
    )

    assert_allclose(reconstructed, dens_mat, rtol=0.0, atol=TOL)


def test_R_hat():
    TOL = 100 * np.spacing(np.complex128(1.0).real)
    np.random.seed(7777)

    sigmas = [np.random.randn(4, 4) + 1j * np.random.randn(4, 4) for i in range(3)]

    example = (
        np.kron(sigmas[0], np.eye(4))
        + np.kron(np.kron(np.eye(2), sigmas[1]), np.eye(2))
        + np.kron(np.eye(4), sigmas[2])
    )

    assert_allclose(R_hat(sigmas, 4), example, rtol=0.0, atol=TOL)


def test_iteration():
    NUM_QUBITS = 5
    SEED = 7777
    TOL = 0.15
    K = 2

    np.random.seed(SEED)

    dim = 2 ** NUM_QUBITS
    state = np.zeros((dim), dtype=np.complex128)
    for i in range(NUM_QUBITS):
        state[1 << i] = np.random.normal()
    state /= np.linalg.norm(state)

    dens_mat = np.outer(state, state.conj())

    def reduce(qubit):
        left_size = 2 ** qubit
        reduced_size = 2 ** K
        right_size = np.size(dens_mat, axis=0) // (left_size * reduced_size)

        reshaped = np.reshape(
            dens_mat,
            (left_size, reduced_size, right_size, left_size, reduced_size, right_size),
        )

        return np.einsum("aibajb->ij", reshaped)

    sigmas = (reduce(q) for q in range(NUM_QUBITS - K + 1))

    y_vec = iteration(K, sigmas, NUM_QUBITS, max_its=100, delta=0.1)

    assert_allclose(np.abs(state.conj() @ y_vec) ** 2, 1, rtol=0.0, atol=TOL)
