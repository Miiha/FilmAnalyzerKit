import json
import os
import re
from enum import Enum

from analyzer.path_utils import create_directory
from analyzer.utils import Model


class StoragePath(Enum):
	local = 1
	remote = 2

	def base_path(self, identifier):
		from analyzer.utils import env

		if self == StoragePath.local:
			data_path = env("DATA_DIR", "data")
			return os.path.join(data_path, identifier)
		elif self == StoragePath.remote:
			return identifier


class Project(Model):
	keyframe_montage_size = None
	keyframe_size = None

	def __init__(self, title):
		self.name = title

		identifier = re.sub('[^a-zA-Z0-9-_*.]', ' ', title.lower())
		self.identifier = identifier.replace(" ", "_")

		local_base_path = StoragePath.local.base_path(self.identifier)
		create_directory(local_base_path)

	class Folder(Enum):
		frames = 1
		keyframes = 2
		keyframe_thumbnails = 3
		spatio = 4
		plots = 5

		def __str__(self):
			return {
				Project.Folder.frames: "frames",
				Project.Folder.keyframes: "keyframes",
				Project.Folder.keyframe_thumbnails: "keyframe_thumbnails",
				Project.Folder.spatio: "spatio_temporal_slices",
				Project.Folder.plots: "plots",
			}[self]

	class File(Enum):
		shots = 1
		chapters = 2
		subtitles = 3
		merged_subtitles = 4
		original_subtitles = 5
		script = 6
		keyframe_montage = 7
		shot_change_ratio = 8

		def __str__(self):
			return {
				Project.File.shots: "shots.json",
				Project.File.chapters: "chapters.json",
				Project.File.subtitles: "subtitles.json",
				Project.File.original_subtitles: "subtitles.srt",
				Project.File.merged_subtitles: "merged_subtitles.json",
				Project.File.script: "script.json",
				Project.File.keyframe_montage: "keyframe_montage.jpg",
				Project.File.shot_change_ratio: "shot_change_ratio.json",
			}[self]

	def setup(self):
		for folder_type in Project.Folder:
			self.folder_path(folder_type)

	@staticmethod
	def file_exists(path):
		return os.path.exists(path)

	def folder_path(self, folder_type, destination=None, storage_env=StoragePath.local):
		assert folder_type is not None

		folder = str(folder_type) if type(folder_type) == Project.Folder else folder_type

		if destination:
			return self.__folder_path(destination, storage_env)
		else:
			base_path = storage_env.base_path(self.identifier)
			default_path = os.path.join(base_path, folder)
			return self.__folder_path(default_path, storage_env)

	def file_path(self, file_type, destination=None, storage_env=StoragePath.local):
		return self.__file_path(str(file_type), destination, storage_env)

	def write(self, data, file_type, destination=None):
		destination = self.__file_path(str(file_type), destination)
		write_json(destination, data)

	def read(self, file_type):
		path = self.__file_path(str(file_type))
		with open(path) as data:
			return json.load(data)

	def __folder_path(self, folder, storage_env=StoragePath.local):
		if storage_env == StoragePath.local:
			create_directory(folder)

		return folder

	def __file_path(self, filename, full_path=None, storage_env=StoragePath.local):
		if full_path is None:
			base_path = storage_env.base_path(self.identifier)
			return os.path.join(base_path, filename)

		if os.path.isdir(full_path):
			full_path = os.path.join(full_path, filename)

		dir = os.path.dirname(full_path)
		create_directory(dir)
		return full_path


def write_json(path, data):
	# create_directory(path)
	with open(path, 'w') as outfile:
		json.dump(data, outfile, sort_keys=True, indent=4)
