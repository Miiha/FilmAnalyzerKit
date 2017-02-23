# -*- coding: utf-8 -*-
import unittest

from analyzer import dtw_merger as dtw
from analyzer import needleman_wunsch as nw
from analyzer.needleman_wunsch import AdaptiveGapPenalty, GapPenalty, Weighting
from analyzer.script_entity import ScriptEntity
from analyzer.subtitles_parser import Subtitle
from analyzer.logger import Logger


def mock_subtitles(string_list):
	return [Subtitle(0, 0, string) for string in string_list]


def mock_speeches(char_text_list):
	return [ScriptEntity(char, text) for char, text in char_text_list]


def seperator():
	print("-" * 50)


class AlgorithmComparisonTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut_dtw = dtw.perform
		self._sut_nw = nw.perform
		self._logger = Logger(None)

		print("=" * 100)

	def test_characters_difference_length(self):
		s1 = "millageville"
		s2 = "millage ville"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)

		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_character_difference_same_length(self):
		s1 = "millegeeee"
		s2 = "mille asde"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)

		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_character_difference(self):
		s1 = "ok"
		s2 = "okay"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.levenstein_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None

		seperator()
		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_character_difference_repeat(self):
		s1 = "three"
		s2 = "threeeee"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.levenstein_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None

		seperator()
		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_unseperated_words_short(self):
		s1 = "All right"
		s2 = "Alright"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger,
		                              distance_function=dtw.levenstein_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is "CHAR0"

		seperator()
		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_unseperated_words_long(self):
		s1 = "Developed by Master Wuxi in the Third Dynasty"
		s2 = "DevelopedbyMasterWuxiInTheThirdDynasty"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger,
		                              distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None

		seperator()
		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_unseperated_words(self):
		s1 = "Hey, All right. All reight."
		s2 = "Alright...alright"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger,
		                              distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None

		seperator()
		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_unseparated_words_2(self):
		s1 = "Millage Ville, Georgia."
		s2 = "Milledgeville, Georgia."

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger,
		                              distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None

		seperator()

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_fill_words(self):
		s1 = "Millage Ville, Georgia."
		s2 = "Millefall ville Geodgia"

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger,
		                              distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is "CHAR0"

		seperator()

		subtitles = mock_subtitles([s1])
		speeches = mock_speeches([("CHAR0", s2)])

		nw_alignment = self._sut_nw(speeches, subtitles, logger=self._logger)
		nw.pretty_print_grid(nw_alignment)
		assert nw_alignment.subtitles[0].character is "CHAR0"

	def test_different_order(self):
		s1 = "Broke in right on the two of them"
		s2 = "No matter what they say, it's all about money"

		subtitles = mock_subtitles([s1, s2])
		speeches = mock_speeches([("CHAR0", s2), ("CHAR1", s1)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is None
		assert dtw_alignment.subtitles[1].character is "CHAR0"

		seperator()

		nw_alignment = self._sut_nw(speeches, subtitles, Weighting(1, -1, GapPenalty(-2)), logger=self._logger)
		assert nw_alignment.subtitles[0].character is None
		assert nw_alignment.subtitles[1].character is None

		seperator()

		# using the adaptive gap penalty, the first subtitle will be fully matched with gaps
		# and the second can match against the first script
		nw_alignment = self._sut_nw(speeches, subtitles, Weighting(1, -1, AdaptiveGapPenalty(-5, -1)),
		                            logger=self._logger)
		assert nw_alignment.subtitles[0].character is None
		assert nw_alignment.subtitles[1].character is "CHAR0"

	def test_different_order_2(self):
		s1 = "No matter what they say"
		s2 = "It is all about money"

		subtitles = mock_subtitles([s1, s2])
		speeches = mock_speeches([("CHAR0", s2), ("CHAR1", s1)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is "CHAR1"
		assert dtw_alignment.subtitles[1].character is None

	def test_doubling_in_subtitles(self):
		text_1 = "Broke in right on the two of them"
		text_2 = "No matter what they say, it's all about money"

		subtitles = mock_subtitles([text_1, text_1])
		speeches = mock_speeches([("CHAR0", text_1), ("CHAR1", text_2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is "CHAR0"
		assert dtw_alignment.subtitles[1].character is None

		seperator()

		nw_alignment = self._sut_nw(speeches, subtitles, Weighting(1, -1, GapPenalty(-2)), logger=self._logger)
		assert nw_alignment.subtitles[0].character is "CHAR0"
		assert nw_alignment.subtitles[1].character is None

		seperator()

		# different weighting won't change the results on doubled subtitles
		nw_alignment = self._sut_nw(speeches, subtitles, Weighting(1, -1, AdaptiveGapPenalty(-5, -1)),
		                            logger=self._logger)
		assert nw_alignment.subtitles[0].character is "CHAR0"
		assert nw_alignment.subtitles[1].character is None

	def test_matching_over_scripts(self):
		text_1 = "Broke in right on the two of them"
		text_2 = "No matter what they say, it's all about money"

		subtitles = mock_subtitles([text_1, text_1])
		speeches = mock_speeches([("CHAR0", text_1), ("CHAR1", text_2)])

		dtw_alignment = self._sut_dtw(speeches, subtitles, self._logger, distance_function=dtw.binary_distance)
		dtw.pretty_print_grid(dtw_alignment)
		assert dtw_alignment.subtitles[0].character is "CHAR0"
		assert dtw_alignment.subtitles[1].character is None