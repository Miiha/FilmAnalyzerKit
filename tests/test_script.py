# -*- coding: utf-8 -*-
import unittest

from analyzer import script_parser


class ScriptTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = script_parser.clean_script

	def test_parentheses_removeal(self):
		script = [{"text": "(grumpy) some more text", "type": "speech"}]

		cleaned_script = self._sut(script)
		assert cleaned_script[0]["text"] == "some more text"

	def test_parentheses_removeal_space(self):
		script = [{"text": " (grumpy) some more text", "type": "speech"}]

		cleaned_script = self._sut(script)
		assert cleaned_script[0]["text"] == "some more text"

	def test_parentheses_removeal_middle(self):
		script = [{"text": 'some more (grumpy) text', "type": "speech"}]

		cleaned_script = self._sut(script)
		assert cleaned_script[0]["text"] == "some more  text"

	def test_parentheses_removeal_double(self):
		script = [{"text": '(argh) some more (grumpy) text', "type": "speech"}]

		cleaned_script = self._sut(script)
		assert cleaned_script[0]["text"] == "some more  text"
