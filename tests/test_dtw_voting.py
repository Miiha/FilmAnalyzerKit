# -*- coding: utf-8 -*-
import unittest

from analyzer import dtw_merger as dtw
from analyzer.script_entity import ScriptEntity
from analyzer.subtitles_parser import Subtitle
from analyzer.logger import Logger


class DtwMergerTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = dtw.perform
		self._logger = Logger(None)

	def test_1(self):
		subtitles = [
			Subtitle(0, 0, "You're playing music?"),
		]

		script_entities = [
			ScriptEntity("CHAR0", "Yeah, they really want you... they really want you... they really do."),
			ScriptEntity("CHAR1", "You guys are playing music?")
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw.levenstein_distance, verbose=True)
		dtw.pretty_print_grid(alignment)
		assert alignment.subtitles[0].character == "CHAR1"

	def test_2(self):
		subtitles = [
			Subtitle(0, 0, "It's cute?"),
		]

		script_entities = [
			ScriptEntity("CHAR0", "I sort of like it. I mean, it's cute."),
			ScriptEntity("CHAR1", "Cute?"),
		]

		alignment = self._sut(script_entities, subtitles, self._logger, dtw.levenstein_distance, verbose=True)
		dtw.pretty_print_grid(alignment)
		assert alignment.subtitles[0].character == "CHAR0"
