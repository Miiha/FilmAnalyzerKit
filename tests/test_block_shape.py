# -*- coding: utf-8 -*-
import unittest
import numpy as np

from analyzer import utils


class BlockShapeTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = utils.block_shaped

	def test_simple_shape(self):
		image = np.random.rand(4, 6, 3) * 255

		result = self._sut(image, 2, 2)

		assert len(result) == 4
		assert len(result[0]) == 2
		assert len(result[0][0]) == 3

