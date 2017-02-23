# -*- coding: utf-8 -*-
import unittest

from analyzer import dtw_merger
from analyzer.script_entity import ScriptEntity
from analyzer.subtitles_parser import Subtitle
from analyzer.logger import Logger


class DtwMergerTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = dtw_merger.perform
		self._logger = Logger(None)

	def test_0(self):
		subtitles = [
			Subtitle(0, 0, "hello my name is micha"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "hello what name is micha", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw_merger.binary_distance, verbose=True)
		dtw_merger.pretty_print_grid(alignment)

	def test_1(self):
		subtitles = [
			Subtitle(0, 0, "hello my name is micha"),
			Subtitle(0, 0, "bla my bla is micha"),
			Subtitle(0, 0, "he is up"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "hello my name is michi", "type": "speech"}),
			ScriptEntity(**{"character": "CHAR1", "text": "who he is", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw_merger.binary_distance, verbose=True)
		dtw_merger.pretty_print_grid(alignment)

	def test_2(self):
		subtitles = [
			Subtitle(0, 0, "hello my name is micha"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "hello my name micha is", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw_merger.levenstein_distance, verbose=True)
		dtw_merger.pretty_print_grid(alignment)

	def test_3(self):
		subtitles = [
			Subtitle(0, 0, "hello what are we doing"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "hello what is it we do", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw_merger.binary_distance, verbose=True)
		dtw_merger.pretty_print_grid(alignment)

