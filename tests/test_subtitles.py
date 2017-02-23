# -*- coding: utf-8 -*-
import unittest
import mongomock

from analyzer import subtitles_parser


class SubtitlesTest(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self._sut = mongomock.MongoClient().testdb

	def test_parse_double_text(self):
		text = """16
00:00:54,000 --> 00:00:55,200
- Yeah. Call me.
- When?
"""

		subtitles = subtitles_parser.parse_text(text)
		assert subtitles[0].text == "- Yeah. Call me."
		assert subtitles[1].text == "- When?"

	def test_parse_double_text_single_dash(self):
		text = """16
00:00:54,000 --> 00:00:55,200
Yeah. Call me.
- When?
"""

		subtitles = subtitles_parser.parse_text(text)
		assert subtitles[0].text == "Yeah. Call me."
		assert subtitles[1].text == "- When?"

	def test_parse_single_text(self):
		text = """16
00:00:54,000 --> 00:00:55,200
Yeah. Call me.
When?
"""

		subtitles = subtitles_parser.parse_text(text)
		assert len(subtitles) == 1
		assert subtitles[0].text == "Yeah. Call me. When?"

	def test_parse_double_line_plus_single(self):
		text = """16
00:00:54,000 --> 00:00:55,200
Yeah. Call me.
Yeah. Call me.
- When?
"""

		subtitles = subtitles_parser.parse_text(text)
		assert len(subtitles) == 2
		assert subtitles[0].text == "Yeah. Call me. Yeah. Call me."
		assert subtitles[1].text == "- When?"

