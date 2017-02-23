import glob
import math
import os
import shlex
import subprocess
from os.path import join
from pprint import pprint
from shutil import copy2
from statistics import mean

import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import distance as dist
from tqdm import tqdm

from analyzer import path_utils
from analyzer import utils
from analyzer import plot as uplot
from analyzer.constants import ExtractionType
from analyzer.project import Project
from analyzer.utils import Model, image_filename, derivative, slice_paths, extract_index, window

HSV_COLOR_SPACE = [(8, [0, 256]), (4, [0, 256]), (4, [0, 256])]
RGB_CHANNEL_SIZES = [(8, [0, 256]), (8, [0, 256]), (8, [0, 256])]


SCIPY_METHODS = (
	("Euclidean", dist.euclidean),
	("Manhattan", dist.cityblock),
	("Chebysev", dist.chebyshev))


def histogram(image):
	bins, sizes = zip(*RGB_CHANNEL_SIZES)
	bins = list(bins)
	sizes = utils.flatten(list(sizes))

	hist = cv2.calcHist([image], [0, 1, 2], None, list(bins), list(sizes))
	hist = cv2.normalize(hist, None).flatten()

	return hist


def quadrant_histograms(image):
	blocks = utils.block_shaped(image, 2, 2)
	# plot_color_histograms(blocks)
	# plot_image(blocks)
	histograms = [histogram(block) for block in blocks]

	return histograms


def avg_histogram_difference(base_histograms, test_histograms, method=SCIPY_METHODS[0][1]):
	distances = [method(w1, w2) for w1, w2 in zip(base_histograms, test_histograms)]

	distances = np.array(distances)
	return distances.mean()


a = 0


def plot_color_histograms(blocks):
	global a

	i = 0
	for c in range(1, 3):
		for r in range(1, 3):
			plt.subplot(2, 2, i + 1)
			block = blocks[i]

			color = ('b', 'g', 'r')
			for channel, (col, (bin, size)) in enumerate(zip(color, HSV_COLOR_SPACE)):
				histr = cv2.calcHist([block], [channel], None, [bin], size)
				plt.plot(histr, color=col)
				plt.xlim([0, 256])

			plt.legend(['h', 's', 'v'], loc='upper right')

			w, h, _ = block.shape
			plt.ylim([0, w * h])
			plt.xlim([0, 8])

			i += 1
	# plt.savefig("plot/" + image_filename(a, "png"), transparent=True)
	plt.show()

	plt.clf()
	plt.cla()
	plt.close()
	a += 1


def plot_image(blocks):
	i = 0

	plt.figure("Results {}".format(1))
	for c in range(1, len(blocks) - 1):
		for r in range(1, len(blocks) - 1):
			block = blocks[i]

			# block = cv2.cvtColor(block, cv2.COLOR_HSV2RGB)
			plt.subplot(2, 2, i + 1)
			plt.imshow(block)
			plt.axis("off")
			i += 1

	# plt.savefig("plot/" + image_filename(a, "png"), transparent=True)
	plt.show()
	plt.clf()
	plt.cla()
	plt.close()


def calculate_difference(histograms, method):
	methodName = method[0]
	algorithm = method[1]

	cv2.compareHist(histograms[0], histograms[1], cv2.HISTCMP_CHISQR)

	d = algorithm(histograms[0], histograms[1])
	return d


def convert_to_second_derivative(distances):
	first_derivative = derivative(distances)
	second_derivative = derivative(first_derivative)

	return second_derivative


def load_image(path):
	image = cv2.imread(path)
	if image is None:
		return None

	image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	return image


def plot(data, title, project, store=False):
	plt.figure("Results {}".format(title))
	plt.plot(data)

	if not store:
		plt.show()
	else:
		base_path = project.folder_path("plots")
		path = os.path.join(base_path, "{}.jpg".format(title))
		plt.savefig(path)

	plt.clf()
	plt.cla()
	plt.close()


def detect(project, threshold, limit=None, local_sequence=False, type=None):
	src = project.folder_path(Project.Folder.frames)
	image_paths = glob.glob(src + "/*.jpg")

	if limit:
		image_paths = slice_paths(image_paths, limit)

	if local_sequence:
		sequence = project.read(Project.File.shot_change_ratio)
	else:
		sequence = calculate_sequence(image_paths, type)
		sequence and project.write(sequence, Project.File.shot_change_ratio)

	shots = extract_shots(sequence, image_paths, threshold, project)

	return shots


def simple_hist_difference(image0, image1):
	hist0 = histogram(image0)
	hist1 = histogram(image1)

	return dist.euclidean(hist0, hist1)


def quadrant_hist_difference(image0, image1):
	hist0 = quadrant_histograms(image0)
	hist1 = quadrant_histograms(image1)

	return avg_histogram_difference(hist0, hist1)


def calculate_sequence(image_paths, extraction_type):
	chds = []

	if extraction_type == ExtractionType.simpleHistogram.value:
		diff_function = simple_hist_difference
	else:
		diff_function = quadrant_hist_difference

	base_image = None
	progress_bar = tqdm(total=len(image_paths), desc="shots detection")
	for path in image_paths:
		if base_image is not None:
			image = load_image(path)
			diff = diff_function(base_image, image)

			base_image = image
			chds.append(diff)
		else:
			base_image = load_image(path)

		progress_bar.update()
	progress_bar.close()

	return chds


def extract_shots(distances, image_paths, threshold, project):
	uplot.plot("plot_detection_histogram", [distances], project=project, store=True)
	distances = convert_to_second_derivative(distances)
	uplot.plot("plot_second_derivative", [distances], project=project, store=True)

	file_index = extract_index(image_paths[0])
	last_shot_index = file_index - 1
	relative = file_index - 1

	shots = []

	windows = list(window(zip(distances, image_paths), 3))
	last_index = len(windows) - 1

	progress_bar = tqdm(total=len(distances), desc="shots extraction")
	for i, ((t1_d, p1), (t2_d, p2), (t3_d, p3)) in enumerate(windows):
		actual_index = relative + i + 2  # center of the window

		prev_diff = abs(t1_d - t2_d)

		if t1_d < t2_d and prev_diff > threshold:
			shot = Shot(start_index=last_shot_index, end_index=actual_index, id=len(shots), relative_diff=t2_d)
			shots.append(shot)
			last_shot_index = actual_index

		if last_index == i:
			shot = Shot(start_index=last_shot_index, end_index=actual_index + 1, id=len(shots), relative_diff=t2_d)
			shots.append(shot)

		progress_bar.update()

	progress_bar.close()

	return shots


def adaptive_threshold(distances):
	ave = np.array(distances).mean()

	filtered = [val for val in distances if val > 0.0]
	ave = np.array(filtered).mean()

	sliding_window = utils.window(distances, 3)
	local_maxima = [d2 for d1, d2, d3 in sliding_window if d2 > ave and d1 < d2 and d3 < d2]

	t = np.array(local_maxima).mean()

	return t


def log_statistics(shots, fps=25):
	shot_lengths = [shot.length for shot in shots]
	average_shot_length = mean(shot_lengths)

	print("average shot length: {:.1f} frames ~ {:.2f} sec".format(average_shot_length, average_shot_length / fps))


class Keyframe(object):
	def __init__(self, index):
		self.index = index
		self.colors = None
		self.labels = None


class Shot(Model):
	def __init__(self, start_index=None, end_index=None, id=None, relative_diff=None):
		if end_index:
			self.keyframe = Keyframe(start_index)
			self.end_index = end_index
			self.length = end_index - start_index
			self.duration = int(self.length / 25 * 1000)
		else:
			self.keyframe = None
			self.end_index = None
			self.duration = None

		self.start_index = start_index
		self.id = id
		self.start_diff = relative_diff

	def as_dict(self, camel=True):
		d = Model.as_dict(self)
		if self.keyframe.labels:
			d["keyframe"]["labels"] = [label.as_dict() for label in self.keyframe.labels]

		return d

	def to_mongo_dict(self):
		d = self.as_dict()
		return utils.to_mongo_dict(d)

	@classmethod
	def from_dict(cls, data, from_camel=True):
		d = Model.from_dict(data, from_camel)
		shot = Shot(d.get("start_index"), d.get("end_index"), d.get("id"), d.get("relative_diff"))

		if "labels" in d["keyframe"] and d["keyframe"]["labels"] is not None:
			shot.keyframe.labels = [Label.from_dict(l) for l in (d["keyframe"]["labels"])]

		if "colors" in d["keyframe"] and d["keyframe"]["colors"] is not None:
			shot.keyframe.colors = [l for l in (d["keyframe"]["colors"])]

		return shot

	def __str__(self):
		return "id: {}, start_index: {} length: {}, end_index: {}" \
			.format(self.id, self.start_index, self.length, self.end_index)

	def __repr__(self):
		return self.__str__()


class Label(Model):
	def __init__(self, description, score):
		self.description = description
		self.score = score

	@classmethod
	def from_dict(cls, data, from_camel=True):
		d = Model.from_dict(data, from_camel)
		return cls(d.get("description"), d.get("score"))

	def __str__(self):
		return "{:<12} => {}".format(self.description, self.score)

	def __repr__(self):
		return self.__str__()


####################################################################
# keyframes


def copy_keyframes(project, _shots):
	key_frames_file_names = [image_filename(shot.keyframe.index) for shot in _shots]
	copy_keyframe = lambda file_name: copy2(join(project.folder_path(Project.Folder.frames), file_name),
	                                        join(project.folder_path(Project.Folder.keyframes), file_name))
	[copy_keyframe(file_name) for file_name in key_frames_file_names]


####################################################################
# spatio temporal slices


def write_spatio_temporal_slices(project, shots):
	progress_bar = tqdm(total=len(shots), desc="spatio temporal slices")
	for shot in shots:
		slices = calculate_patio_temporal_slice(project.folder_path(Project.Folder.frames), shot)
		vis = np.concatenate(slices, axis=1)

		filename = image_filename(shot.id)
		path = os.path.join(project.folder_path(Project.Folder.spatio), filename)
		cv2.imwrite(path, vis)
		progress_bar.update()

	progress_bar.close()


def calculate_patio_temporal_slice(base_path, shot):
	cropped_images = []
	for index in range(shot.start_index, shot.end_index):
		filename = image_filename(index)
		path = join(base_path, filename)
		image = cv2.imread(path)

		shape = image.shape
		y = 0
		x = shape[1] // 2
		width = 1
		height = shape[0]

		cropped_image = image[y:y + height, x:x + width]
		resize_image = cv2.resize(cropped_image, (cropped_image.shape[1], 50))
		cropped_images.append(resize_image)

	return cropped_images


####################################################################
# keyframe thumbnails


def keyframe_thumbnails(project):
	keyframes_path = project.folder_path(Project.Folder.keyframes)
	keyframe_paths = glob.glob(keyframes_path + "/*.jpg")

	if len(keyframe_paths) == 0:
		return None

	required_width = 200
	keyframe_thumbnails_path = project.file_path(Project.Folder.keyframe_thumbnails)

	for keyframe_path in keyframe_paths:
		filename = path_utils.filename(keyframe_path)
		dest = join(keyframe_thumbnails_path, filename)
		args = "{} -resize {}x1^ {}".format(keyframe_path, required_width, dest)
		cmd = "{} {}".format("convert", args)
		subprocess.call(shlex.split(cmd))


def keyframe_thumbnail_size(project):
	path = project.file_path(Project.Folder.keyframe_thumbnails)
	keyframe_thumbnails_path = glob.glob(path + "/*.jpg")

	if len(keyframe_thumbnails_path) == 0:
		return None

	image = load_image(keyframe_thumbnails_path[0])
	height, width = image.shape[:2]

	return width, height


####################################################################
# KEYFRAME MONTAGE

KEYFRAME_MONTAGE_COLUMNS = 10


def keyframe_montage(project):
	keyframes_path = project.folder_path(Project.Folder.keyframes)
	keyframe_paths = glob.glob(keyframes_path + "/*.jpg")

	if len(keyframe_paths) == 0:
		return None

	required_width = 200
	rows = int(math.ceil(len(keyframe_paths) / KEYFRAME_MONTAGE_COLUMNS))

	output_path = project.file_path(Project.File.keyframe_montage)

	args = "-tile {}x{} -geometry {}x1^ {}/*.jpg {}".format(KEYFRAME_MONTAGE_COLUMNS, rows, required_width,
	                                                        keyframes_path, output_path)
	cmd = "{} {}".format("montage", args)
	subprocess.call(shlex.split(cmd))


def montage_keyframe_size(project):
	path = project.file_path(Project.File.keyframe_montage)
	image = load_image(path)

	if image is None:
		return None

	keyframes_path = project.folder_path(Project.Folder.keyframes)
	keyframe_paths = glob.glob(keyframes_path + "/*.jpg")

	if len(keyframe_paths) == 0:
		return None

	height, width = image.shape[:2]
	rows = int(math.ceil(len(keyframe_paths) / KEYFRAME_MONTAGE_COLUMNS))
	cell_width = int(width / KEYFRAME_MONTAGE_COLUMNS)
	cell_height = int(height / rows)

	return cell_width, cell_height


def keyframe_size(project):
	keyframes_path = project.folder_path(Project.Folder.keyframes)
	keyframe_paths = glob.glob(keyframes_path + "/*.jpg")

	if len(keyframe_paths) == 0:
		return None

	image = load_image(keyframe_paths[0])
	height, width = image.shape[:2]
	return width, height
