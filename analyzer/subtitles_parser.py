#!/usr/bin/python
import re

from analyzer import utils
from analyzer.timestamp import Timestamp
from analyzer.utils import flatten, Model


class Subtitle(Model):
	def __init__(self, t1, t2, text, original_text=None, character=None):
		self.t1 = Timestamp(t1) if (type(t1) == int) else t1
		self.t2 = Timestamp(t2) if (type(t2) == int) else t2
		self.text = text
		self.original_text = text if text is not None else original_text
		self.character = character

	def __str__(self):
		return "t1: {}, t2: {}, text: {}, character: {}".format(self.t1, self.t2, self.text, self.character)

	def __repr__(self):
		return self.__str__()

	def as_dict(self, camel=True):
		d = Model.as_dict(self)
		d["t1"] = self.t1.millis
		d["t2"] = self.t2.millis

		return d

	def to_mongo_dict(self):
		d = self.as_dict()
		return utils.to_mongo_dict(d)

	@classmethod
	def from_dict(cls, data, from_camel=True):
		d = Model.from_dict(data, from_camel)

		return cls(d["t1"], d["t2"], d["text"], d["original_text"], d["character"])


def strip_non_ascii(string):
	""" Returns the string without non ASCII characters"""
	stripped = (c for c in string if 0 < ord(c) < 127)
	return ''.join(stripped)


def parse_subtitle(text):
	lines = text.split('\n')
	ts_split_regex = re.compile('[ \->]*')
	matches = ts_split_regex.split(lines[1])

	if len(matches) != 2:
		return Exception("Missing timestamps")

	ts1 = Timestamp(matches[0])
	ts2 = Timestamp(matches[1])

	speech_lines = lines[2:]
	original_text = '\r\n'.join(speech_lines)

	speeches = extract_speeches(speech_lines)
	subtitles = []
	for speech in speeches:
		text = strip_non_ascii(speech)
		sub = Subtitle(ts1, ts2, text, original_text)
		subtitles.append(sub)

	return subtitles


def extract_speeches(speech_lines):
	dash_pattern = re.compile("^-")
	speeches = []
	extracted_lines = []

	for i, line in enumerate(speech_lines):
		result = dash_pattern.search(line)
		if result:
			if len(extracted_lines) == 0:
				extracted_lines.append(line)
			else:
				speech = " ".join(extracted_lines)
				speeches.append(speech)
				extracted_lines = [line]

			if i == len(speech_lines) - 1:
				if len(extracted_lines) > 0:
					speech = " ".join(extracted_lines)
					speeches.append(speech)
		else:
			extracted_lines.append(line)

			if i == len(speech_lines) - 1:
				if len(extracted_lines) > 0:
					speech = " ".join(extracted_lines)
					speeches.append(speech)
	return speeches


def parse_text(text):
	text_list = text.strip().replace('\r', '').split('\n\n')
	subtitles = [(lambda x: parse_subtitle(x))(sub) for sub in text_list]

	subtitles = flatten(subtitles)
	return subtitles


def parse_file(srt):
	raw_file_list = open(srt).read()

	return parse_text(raw_file_list)


