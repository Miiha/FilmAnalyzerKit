# -*- coding: utf-8 -*-
import unittest

from analyzer.shot_detection import Shot, Label
from analyzer.subtitles_parser import Subtitle
from analyzer.timestamp import Timestamp


class ShotModelTests(unittest.TestCase):
	def setUp(self):
		self._sut = Shot(0, 10, 0)

	def test_shot_model(self):
		assert self._sut.length == 10
		assert self._sut.duration == 400
		assert self._sut.keyframe.index == 0
		assert self._sut.keyframe.colors is None
		assert self._sut.keyframe.labels is None

	def test_camel_case(self):
		result = self._sut.as_dict(camel=True)

		assert result is not None
		assert "endIndex" in result
		assert "startIndex" in result
		assert "startDiff" in result

	def test_mongo_representation(self):
		shot = self._sut
		shot.keyframe.labels = [Label("sut", 0.5)]

		result = shot.to_mongo_dict()

		assert result is not None
		assert result["length"] == 10
		assert result["keyframe.index"] == 0
		assert result["keyframe.colors"] is None
		assert result["keyframe.labels"] is not None

	def test_mongo_representation_with_labels(self):
		result = self._sut.to_mongo_dict()

		assert result is not None
		assert result["length"] == 10
		assert result["keyframe.index"] == 0
		assert result["keyframe.colors"] is None
		assert result["keyframe.labels"] is None

	def test_from_dict(self):
		data = self._sut.as_dict(camel=True)
		result = Shot.from_dict(data)

		assert type(result) is Shot

	def test_from_empty_labels_dict(self):
		result = self._sut.as_dict()
		assert result["keyframe"]["labels"] is None

	def test_shots_with_labels_from_dict(self):
		shot = self._sut
		shot.keyframe.labels = [Label("sut", 0.5)]

		result = shot.as_dict()

		assert len(result["keyframe"]["labels"]) == 1
		label = result["keyframe"]["labels"][0]
		assert "description" in label
		assert "score" in label
		assert label["description"] == "sut"
		assert label["score"] == 0.5


class SubtitleModelTests(unittest.TestCase):
	def setUp(self):
		self._sut = Subtitle(0, 10, "stub", character="char")

	def test_model(self):
		assert type(self._sut.t1) == Timestamp
		assert type(self._sut.t2) == Timestamp
		assert self._sut.t1.millis == 0
		assert self._sut.t2.millis == 10

	def test_camel_case(self):
		result = self._sut.as_dict(camel=True)

		assert result is not None
		assert "originalText" in result
		assert "t1" in result
		assert "t2" in result

		assert result["t1"] == 0
		assert result["t2"] == 10

	def test_mongo_representation(self):
		result = self._sut.to_mongo_dict()

		assert result is not None
		assert result["t1"] == 0
		assert result["t2"] == 10

	def test_from_dict(self):
		data = self._sut.as_dict(camel=True)
		result = Subtitle.from_dict(data)

		assert type(result) is Subtitle
		assert type(result.t1) is Timestamp
		assert type(result.t2) is Timestamp
		assert result.original_text == "stub"
		assert result.text == "stub"
		assert result.character == "char"

