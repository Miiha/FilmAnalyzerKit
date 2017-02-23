# -*- coding: utf-8 -*-
from analyzer.utils import Model


class ScriptEntity(Model):
	def __init__(self, character, text, type="speech"):
		self.character = character
		self.type = type
		self.original_text = text

		self.text = text.rstrip().replace('\n', ' ') if type == 'speech' else text

	def __str__(self):
		return "type: {}, character: {}, text: \"{}\"".format(self.type, self.character, self.text)

	def __repr__(self):
		return self.__str__()

	@classmethod
	def from_dict(cls, data, from_camel=True):
		d = Model.from_dict(data, from_camel)
		return cls(d.get("character"), d.get("text"), type=d.get("type"))

	@classmethod
	def from_dicts(cls, data, from_camel=True):
		return [cls.from_dict(d) for d in data]


class Speech(object):
	def __init__(self, character, text):
		self.character = character
		self.original_text = text
		self.text = text.rstrip().replace('\n', ' ')

	def __str__(self):
		return "character: {}, text: \"{}\"".format(self.character, self.text)

	def __repr__(self):
		return "character: {}, text: \"{}\"".format(self.character, self.text)
