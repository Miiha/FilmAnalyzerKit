# -*- coding: utf-8 -*-
import unittest

from analyzer.project import Project, StoragePath


class ProjectTests(unittest.TestCase):
	"""Some test case"""

	def setUp(self):
		self.sut = Project("sut")
		self.output_dir = "data"

	def test_file(self):
		assert str(Project.File.subtitles) == "subtitles.json"
		assert str(Project.File.merged_subtitles) == "merged_subtitles.json"
		assert str(Project.File.chapters) == "chapters.json"
		assert str(Project.File.shots) == "shots.json"

	def test_folders(self):
		assert str(Project.Folder.keyframes) == "keyframes"
		assert str(Project.Folder.frames) == "frames"
		assert str(Project.Folder.spatio) == "spatio_temporal_slices"

	def test_local_frames_path(self):
		path = self.sut.folder_path(Project.Folder.frames)

		assert path == "{}/sut/frames".format(self.output_dir)

	def test_remote_frames_path(self):
		path = self.sut.folder_path(Project.Folder.frames, storage_env=StoragePath.remote)

		assert path == "sut/frames"

	def test_local_keyframes_path(self):
		path = self.sut.folder_path(Project.Folder.keyframes, storage_env=StoragePath.local)

		assert path == "{}/sut/keyframes".format(self.output_dir)

	def test_remote_keyframes_path(self):
		path = self.sut.folder_path(Project.Folder.keyframes, storage_env=StoragePath.remote)

		assert path == "sut/keyframes"

	def test_local_spatio_path(self):
		path = self.sut.folder_path(Project.Folder.spatio, storage_env=StoragePath.local)

		assert path == "{}/sut/spatio_temporal_slices".format(self.output_dir)

	def test_remote_spatio_path(self):
		path = self.sut.folder_path(Project.Folder.spatio, storage_env=StoragePath.remote)

		assert path == "sut/spatio_temporal_slices"

	def test_explicit_local_path(self):
		path = self.sut.folder_path("test", storage_env=StoragePath.local)

		assert path == "{}/sut/test".format(self.output_dir)

	def test_remote_path(self):
		path = self.sut.folder_path("dir", storage_env=StoragePath.remote)

		assert path == "sut/dir"
