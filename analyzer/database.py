from pymongo import MongoClient

from analyzer.shot_detection import Shot
from analyzer.utils import env

DB_HOST = env("DB_HOST")
DB_USER = env("DB_USER")
DB_PASSWD = env("DB_PASSWD")
DB_NAME = env("DB_NAME")


class Database(object):
	def __init__(self, host=DB_HOST, user=DB_USER, passwd=DB_PASSWD):
		self.host = host
		self.user = user
		self.passwd = passwd
		self.db_name = DB_NAME

		self.t_key = "titleId"

		self.client = None
		self.context = self.connect(self.host, self.user, self.passwd, self.db_name)

	def connect(self, host, user, passwd, db_name):
		uri = "mongodb://{}:{}@{}/{}?authMechanism=SCRAM-SHA-1".format(user, passwd, host, db_name)
		self.client = MongoClient(uri)
		db = self.client[db_name]

		self.context = db
		return db

	def find_shots(self, title):
		title_object = self.context.titles.find_one({"name": title})

		return list(self.context.shots.find({"titleId": title_object["_id"]}))

	def find_title(self, project):
		return self.context.titles.find_one({"identifier": project.identifier})

	def remove_shots(self, title):
		self.context.shots.delete_many({"titleId": title["_id"]})

	def cinemetrics(self, movie_id):
		movie = self.context.cinemetrics.find_one({"id": movie_id})

		def cinemetric_to_shot(metrics, index):
			return Shot(start_index=metrics["TC"], id=index)

		return [cinemetric_to_shot(metrics, i) for i, metrics in enumerate(movie["shots"])] if movie else None

	def update_title(self, project):
		self.context.titles.update({"identifier": project.identifier}, {"$set": project.as_dict()}, upsert=True)

	def update_shots(self, project, shots):
		title = self.find_title(project)

		if title is None:
			raise Exception("Can't find title in db")

		title_id = title["_id"]

		collection = self.context.shots
		db_shots = collection.find({self.t_key: title_id})
		if db_shots.count():
			print("delete")
			collection.delete_many({self.t_key: title_id})
		else:
			print("no delete")

		dicts = [self.to_entity(shot, title_id) for shot in shots]
		print(shots[0].keyframe.colors)
		collection.insert(dicts)

	def update_subtitles(self, project, subtitles):
		title = self.find_title(project)

		if title is None:
			raise Exception("Can't find title in db")

		title_id = title["_id"]
		collection = self.context.subtitles
		db_subtitles = collection.find({self.t_key: title_id})

		if db_subtitles.count():
			collection.delete_many({self.t_key: title_id})

		dicts = [self.to_entity(subtitle, title_id) for subtitle in subtitles]
		collection.insert(dicts)

	def update_chapters(self, project, chapters):
		title = self.find_title(project)

		if title is None:
			raise Exception("Can't find title in db")

		title_id = title["_id"]

		collection = self.context.chapters
		db_chapters = collection.find({self.t_key: title_id})

		if db_chapters.count():
			collection.delete_many({self.t_key: title_id})

		dicts = [self.to_entity(chapter, title_id) for chapter in chapters]
		collection.insert(dicts)

		print("Updated")

	def to_entity(self, s, title_id):
		d = s.as_dict()
		d[self.t_key] = title_id
		return d

	def close(self):
		self.client and self.client.close()

