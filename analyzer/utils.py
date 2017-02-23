import inspect
import ntpath
from os import getenv
from os.path import join, dirname, splitext


from dotenv import load_dotenv

from itertools import islice
from re import *


def env(name, default=None):
	return getenv(name, default)

DEBUG = bool(int(getenv('DEBUG', False)))

if DEBUG:
	dotenv_path = join(dirname(__file__), '../.env')
	load_dotenv(dotenv_path)


def window(seq, n=2):
	"""Returns a sliding window (of width n) over data from the iterable"""
	"   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
	it = iter(seq)
	result = tuple(islice(it, n))
	if len(result) == n:
		yield result
	for elem in it:
		result = result[1:] + (elem,)
		yield result


def block_shaped(image, n_rows, n_cols):
	image_height, image_width, _ = image.shape

	window_width = round(image_width / n_rows)
	window_height = round(image_height / n_cols)

	blocks = []
	for c in range(0, image_height, window_height):
		for r in range(0, image_width, window_width):
			block = image[c:c + window_height, r:r + window_width]
			blocks.append(block)

	return blocks


def flatten(l):
	return [item for sublist in l for item in sublist]


def camel_to_underscore(name):
	camel_pat = compile(r'([A-Z])')
	return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
	under_pat = compile(r'_([a-z])')
	return under_pat.sub(lambda x: x.group(1).upper(), name)


def change_dict_naming_convention(d, convert_function):
	new = {}
	if type(d) == int or type(d) == float:
		return d

	for k, v in d.items():
		new_v = v
		if isinstance(v, dict):
			new_v = change_dict_naming_convention(v, convert_function)
		elif isinstance(v, list):
			new_v = list()
			for x in v:
				new_v.append(change_dict_naming_convention(x, convert_function))
		new[convert_function(k)] = new_v
	return new


class Model(object):
	def as_dict(self, camel=True):
		dictionary = to_dict(self)
		if camel:
			return change_dict_naming_convention(dictionary, underscore_to_camel)
		else:
			return dictionary

	@classmethod
	def from_dict(cls, data, from_camel=True):
		if from_camel:
			return change_dict_naming_convention(data, camel_to_underscore)
		else:
			return data

	@classmethod
	def from_dicts(cls, data, from_camel=True):
		return [cls.from_dict(d) for d in data]

	def to_mongo_dict(self):
		dictionary = self.as_dict()
		return to_mongo_dict(dictionary)


def to_mongo_dict(obj):
	new_dict = {}
	for key, value in obj.items():
		if type(value) == dict:
			for k, v in value.items():
				new_dict[key + "." + k] = v
		else:
			new_dict[key] = value

	return new_dict


def to_dict(obj):
	if not hasattr(obj, "__dict__"):
		return obj
	result = {}
	for key, val in obj.__dict__.items():
		if key.startswith("_"):
			continue
		element = []
		if isinstance(val, list):
			for item in val:
				element.append(to_dict(item))
		else:
			element = to_dict(val)
		result[key] = element
	return result


def props(obj):
	pr = {}
	for name in dir(obj):
		value = getattr(obj, name)
		if not name.startswith('__') and not inspect.ismethod(value):
			pr[name] = value
	return pr


def image_filename(index, file_type="jpg"):
	return '{:010d}.{}'.format(index + 1, file_type)


def extract_filename(path):
	head, tail = ntpath.split(path)
	return tail or ntpath.basename(head)


def extract_name(file):
	return splitext(file)[0]


def basepath(path):
	return path.dirname(path)


def extract_index(path):
	file = extract_filename(path)
	filename = extract_name(file)
	file_index = int(filename)

	return file_index


def objects_as_dict(objects):
	if len(objects) < 0:
		return None

	T = type(objects[0])
	if "as_dict" not in dir(T):
		return None

	if not all(isinstance(n, T) for n in objects):
		return None

	return [o.as_dict() for o in objects]


def slice_paths(paths, limit):
	lower = int(limit[0])
	upper = int(limit[1])

	new_paths = []
	for i, path in enumerate(paths):
		_, file_extension = splitext(path)
		file_index = extract_index(path)

		if lower <= file_index <= upper:
			new_paths.append(path)

	return new_paths


def derivative(distances):
	windows = window(distances)
	derivative_distances = []

	for i, (d1, d2) in enumerate(windows):
		if i == 0:
			derivative_distances.append(0.0)

		if d2 >= d1:
			derivative_distances.append(d2 - d1)
		else:
			derivative_distances.append(0.0)

	distances.insert(0, 0)

	return derivative_distances


def crop_image(image, cx=20, cy=20):
	sz = image.shape
	return image[cy:(sz[0]-cy), cx:(sz[1]-cx)]