from xml.etree import ElementTree
import urllib
import urllib.request

from analyzer import utils
from analyzer.timestamp import Timestamp
from analyzer.utils import Model, env

API_KEY = env("CHAPTER_DB_API_KEY")
BASE_URL = "http://www.chapterdb.org/chapters/"


class ChapterInfo(Model):
	def __init__(self, id, title, duration):
		self.id = id
		self.title = title
		self.duration = Timestamp(duration)


class Chapter(Model):
	def __init__(self, id, name, t1, t2=None):
		self.id = id
		self.name = name
		self.t1 = Timestamp(t1)
		self.t2 = Timestamp(t2) if t2 is not None else None

	def __str__(self):
		return "{:>2}: {} - {}: {}".format(self.id, self.t1, self.t2, self.name)

	def __repr__(self):
		return "{:>2}: {} - {}: {}".format(self.id, self.t1, self.t2, self.name)

	def as_dict(self, camel=True):
		d = Model.as_dict(self)
		d["t1"] = self.t1.millis
		d["t2"] = self.t2.millis

		return d

	@classmethod
	def from_dict(cls, data, from_camel=True):
		d = Model.from_dict(data, from_camel)

		return cls(d.get("id"), d.get("name"), d.get("t1"), d.get("t2"))


def load_titles(title):
	encoded_title = urllib.request.quote(title, safe='')
	query = "search?title={}".format(encoded_title)
	url = BASE_URL + query

	req = urllib.request.Request(url)
	req.add_header('ApiKey', API_KEY)
	resp = urllib.request.urlopen(req)
	content = resp.read()

	return ElementTree.fromstring(content), {'chapter': 'http://jvance.com/2008/ChapterGrabber'}


def parse_chapter_info(root, ns):
	title = root.find('chapter:title', ns).text
	ref = root.find('chapter:ref', ns)
	id = int(ref.find('chapter:chapterSetId', ns).text)
	confirmations = root.attrib["confirmations"]

	source = root.find('chapter:source', ns)
	duration = source.find('chapter:duration', ns).text

	parsed_chapter_info = ChapterInfo(id, title, duration)
	parsed_chapters = []
	chapters = root.find('chapter:chapters', ns)

	parsed_chapter_info.chapters = parsed_chapters
	print("{}\t\t{}\t\t{}".format(id, confirmations, title))

	for i, chapter in enumerate(chapters):
		attrib = chapter.attrib
		name = attrib["name"]
		time = attrib["time"]

		c = Chapter(i, name, time)
		parsed_chapters.append(c)

	return parsed_chapter_info


def parse_titles(root, ns):
	titles = [parse_chapter_info(chapter_info, ns) for chapter_info in root]
	return titles


def add_end_to_chapters(chapters, duration):
	windows = list(utils.window(chapters))
	last_index = len(windows) - 1

	for i, (c1, c2) in enumerate(windows):
		c1.t2 = c2.t1 - Timestamp(1)  # minus 1ms

		if i == last_index:
			c2.t2 = duration

	return chapters


def run(project, title):
	results, ns = load_titles(title)
	print("<ID>\t<CONFIRMATIONS>\t\t<TITLE>")
	titles = parse_titles(results, ns)

	valid = False
	selected_id = None

	while not valid:
		answer = input('\n\nSelect id: ')

		try:
			selected_id = int(answer)
			valid = True
		except ValueError:
			print("Invalid id\n")

	chapter_infos = [chapter_info for chapter_info in titles if chapter_info.id == selected_id]
	if len(chapter_infos) == 0:
		raise Exception("Failed to find chapters")

	chapter_info = chapter_infos[0]
	chapter_info.chapters = add_end_to_chapters(chapter_info.chapters, chapter_info.duration)

	return chapter_info.chapters

