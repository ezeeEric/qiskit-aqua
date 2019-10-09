# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Test Clique """

from test.aqua.common import QiskitAquaTestCase

import numpy as np
from qiskit import BasicAer

from qiskit.aqua import run_algorithm, aqua_globals
from qiskit.aqua.input import EnergyInput
from qiskit.optimization.ising import clique
from qiskit.optimization.ising.common import random_graph, sample_most_likely
from qiskit.aqua.algorithms import ExactEigensolver


class TestClique(QiskitAquaTestCase):
    """Cplex Ising tests."""

    def setUp(self):
        super().setUp()
        self.k = 5  # K means the size of the clique
        self.seed = 100
        aqua_globals.random_seed = self.seed
        self.num_nodes = 5
        self.w = random_graph(self.num_nodes, edge_prob=0.8, weight_range=10)
        self.qubit_op, self.offset = clique.get_operator(self.w, self.k)
        self.algo_input = EnergyInput(self.qubit_op)

    def _brute_force(self):
        # brute-force way: try every possible assignment!
        def bitfield(n, length):
            result = np.binary_repr(n, length)
            return [int(digit) for digit in result]

        nodes = self.num_nodes  # length of the bitstring that represents the assignment
        maximum = 2**nodes
        has_sol = False
        for i in range(maximum):
            cur = bitfield(i, nodes)
            cur_v = clique.satisfy_or_not(np.array(cur), self.w, self.k)
            if cur_v:
                has_sol = True
                break
        return has_sol

    def test_clique(self):
        """ Clique test """
        params = {
            'problem': {'name': 'ising'},
            'algorithm': {'name': 'ExactEigensolver'}
        }
        result = run_algorithm(params, self.algo_input)
        x = sample_most_likely(result['eigvecs'][0])
        ising_sol = clique.get_graph_solution(x)
        np.testing.assert_array_equal(ising_sol, [1, 1, 1, 1, 1])
        oracle = self._brute_force()
        self.assertEqual(clique.satisfy_or_not(ising_sol, self.w, self.k), oracle)

    def test_clique_direct(self):
        """ Clique Direct test """
        algo = ExactEigensolver(self.algo_input.qubit_op, k=1, aux_operators=[])
        result = algo.run()
        x = sample_most_likely(result['eigvecs'][0])
        ising_sol = clique.get_graph_solution(x)
        np.testing.assert_array_equal(ising_sol, [1, 1, 1, 1, 1])
        oracle = self._brute_force()
        self.assertEqual(clique.satisfy_or_not(ising_sol, self.w, self.k), oracle)

    def test_clique_vqe(self):
        """ VQE Clique test """
        algorithm_cfg = {
            'name': 'VQE',
            'max_evals_grouped': 2
        }

        optimizer_cfg = {
            'name': 'COBYLA'
        }

        var_form_cfg = {
            'name': 'RY',
            'depth': 5,
            'entanglement': 'linear'
        }

        params = {
            'problem': {'name': 'ising', 'random_seed': 10598},
            'algorithm': algorithm_cfg,
            'optimizer': optimizer_cfg,
            'variational_form': var_form_cfg
        }
        backend = BasicAer.get_backend('statevector_simulator')
        result = run_algorithm(params, self.algo_input, backend=backend)
        x = sample_most_likely(result['eigvecs'][0])
        ising_sol = clique.get_graph_solution(x)
        np.testing.assert_array_equal(ising_sol, [1, 1, 1, 1, 1])
        oracle = self._brute_force()
        self.assertEqual(clique.satisfy_or_not(ising_sol, self.w, self.k), oracle)
