# -*- coding: utf-8 -*-
import unittest

from analyzer import needleman_wunsch as nw
from analyzer.needleman_wunsch import AdaptiveGapPenalty, GapPenalty, Weighting
from analyzer.script_entity import ScriptEntity
from analyzer.subtitles_parser import Subtitle
from analyzer.logger import Logger


def test_gap_filter():
	s1 = "millegeeee"
	s2 = "mille_asde"

	fs1, fs2 = nw.filter_gaps(s1, s2)
	assert len(fs1) == 9
	assert len(fs2) == 9
	assert fs1[5] == "e"
	assert fs2[5] == "a"


def test_gap_filter_only_gaps():
	s1 = "millegeeee"
	s2 = "__________"

	fs1, fs2 = nw.filter_gaps(s1, s2)
	assert len(fs1) == 0
	assert len(fs2) == 0


class NeedlemanWunschMergerTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = nw.perform
		self._logger = Logger(None)

	def test_bio_string(self):
		subtitles = [
			Subtitle(0, 0, "GCATGCU"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "GATTACA", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, logger=self._logger)
		nw.pretty_print_grid(alignment)

	def test_bio_string_2(self):
		subtitles = [
			Subtitle(0, 0, "CNJRQCLU"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "CJRQDLN", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, Weighting(1, -1, AdaptiveGapPenalty(-5, -1)), logger=self._logger)
		nw.pretty_print_grid(alignment)

	def test_character_detection(self):
		subtitles = [
			Subtitle(0, 0, "Hello sir"),
			Subtitle(0, 0, "my name is micha"),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "Hallo Mr", "type": "speech"}),
			ScriptEntity(**{"character": "CHAR1", "text": "my name is michi", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, logger=self._logger)
		nw.pretty_print_grid(alignment)

		assert len(alignment.subtitles) == 2
		assert alignment.subtitles[0].character == "CHAR0"
		assert alignment.subtitles[1].character == "CHAR1"

	def test_gap_penalty_alignment_adaptive(self):
		s1 = "GAAAAAAT"
		s1_index = [(s, None) for s in list(s1)]

		s2 = "GAAT"
		s2_index = [(s, None) for s in list(s2)]

		grid, traceback = nw.nw(s1_index, s2_index, Weighting(1, -1, AdaptiveGapPenalty(-5, -1)))
		alignment = nw.calculate_backtrace(grid, traceback, s1_index, s2_index)

		nw.pretty_print_grid(alignment)
		s1_string = "".join([char for char, _ in alignment.vertical_index])
		s2_string = "".join([char for char, _ in alignment.horizontal_index])
		print(s1_string)
		print(s2_string)

		assert s2_string == "GAA____T"

	def test_gap_penalty_alignment_linear(self):
		s1 = "GAAAAAAT"
		s1_index = [(s, None) for s in list(s1)]

		s2 = "GAAT"
		s2_index = [(s, None) for s in list(s2)]

		grid, traceback = nw.nw(s1_index, s2_index, Weighting(1, -1, GapPenalty(-2)))
		alignment = nw.calculate_backtrace(grid, traceback, s1_index, s2_index)

		nw.pretty_print_grid(alignment)
		s1_string = "".join([char for char, _ in alignment.vertical_index])
		s2_string = "".join([char for char, _ in alignment.horizontal_index])
		print(s1_string)
		print(s2_string)

		assert s2_string == "GAA____T"

	def test_split_words(self):
		subtitles = [
			Subtitle(0, 0, "Millage Ville, Georgia."),
		]

		script_entities = [
			ScriptEntity(**{"character": "CHAR0", "text": "Milledgeville, Georgia", "type": "speech"}),
		]

		alignment = self._sut(script_entities, subtitles, logger=self._logger)

		assert alignment.subtitles[0].character == "CHAR0"

	def test_punctuation_removal(self):
		s1 = [Subtitle(0, 0, "m.")]
		s2 = [ScriptEntity(**{"character": "CHAR0", "text": ".m", "type": "speech"})]

		alignment = self._sut(s1, s2, logger=self._logger)

		assert len(alignment.vertical_index) == 1
		assert len(alignment.horizontal_index) == 1
