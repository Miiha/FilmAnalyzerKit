import json
import os
from os.path import normpath, basename


def filename(path):
	return basename(normpath(path))


def create_directory(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)


def load_json(src):
	with open(src) as script_data:
		return json.load(script_data)


def delete_files_in_folder(path):
	for the_file in os.listdir(path):
		file_path = os.path.join(path, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as e:
			print(e)
