import editdistance
import numpy as np
from scipy.spatial import distance as dist
from tqdm import tqdm
from copy import deepcopy
from itertools import groupby

from analyzer.utils import window
from analyzer.alignment_utils import Alignment
from analyzer.script_entity import ScriptEntity
from analyzer.string_utils import remove_punctuation


class ScoreMatrix(object):
	def __init__(self, grid, traceback, distance_function):
		self.grid = grid
		self.traceback = traceback
		self.distance_function = distance_function

	def score(self, c1, c2):
		return self.distance_function(c1, c2)


def binary_distance(s1, s2):
	return 0 if s1 == s2 else 1


def levenstein_distance(s1, s2):
	d = editdistance.eval(s1, s2)
	return min(d / len(s1), 1)


def pretty_print_grid(alignment):
	grid = alignment.grid
	subtitle_index = alignment.vertical_index
	script_index = alignment.horizontal_index
	alignments = alignment.alignment_list

	def search_indexes(i, j):
		for alignment in alignments:
			if alignment == (i, j):
				return True

		return False

	max = 7
	tail = ".."
	print()
	for i, (word, speech) in enumerate(script_index):
		if i == 0:
			print(" " * 7, end="")

		w = (word[:5] + tail) if len(word) + len(tail) > max else word
		print("{: ^7}".format(w), end="")

		if i == len(script_index) - 1:
			print()

	for row in range(len(grid)):
		for column in range(len(grid[row])):

			d = grid[row][column]

			if column == 0:
				word, subtitle = subtitle_index[row]
				w = (word[:5] + tail) if len(word) + len(tail) > max else word
				print("{:<7}".format(w), end="")

			if search_indexes(row, column):
				print("[{: ^5.1f}]".format(d), end="")
			else:
				print("{: ^7.1f}".format(d), end="")

		print()

	print()
	print(alignments)
	print()


def dtw(template, test, distance_function, logger):
	"""
	Calculates the matrix via dtw algorithm
	Args:
		template: the vertical data stream

	# :param template: the vertical data stream
	# :param test: the horizontal data stream
	# :param distance_function: function to calculate the distance between two strings
	# :param verbose: extended logging
	# :return: grid matrix, traceback matrix
	"""

	template = np.array(template)
	test = np.array(test)

	m = len(template)
	n = len(test)
	size = m * n

	print("\ninitializing grid...\n")

	grid = [x[:] for x in [[0] * n] * m]
	traceback = [x[:] for x in [[None] * n] * m]
	score_matrix = ScoreMatrix(grid, traceback, distance_function)

	progress_bar = tqdm(total=size, desc="dtw")

	for i in range(m):
		for j in range(n):
			s1_word = template[i][0]
			s2_word = test[j][0]
			word_score = score_matrix.score(s1_word, s2_word)

			left_score = grid[i][j - 1]
			upper_score = grid[i - 1][j]
			if (i == 0) and (j == 0):
				grid[i][j] = word_score
				traceback[i][j] = None

			elif i == 0:
				assert left_score >= 0

				grid[i][j] = left_score + word_score
				traceback[i][j] = (i, j - 1)

			elif j == 0:
				assert upper_score >= 0

				grid[i][j] = upper_score + word_score
				traceback[i][j] = (i - 1, j)

			else:
				assert left_score >= 0
				assert upper_score >= 0

				diagonal_score = grid[i - 1][j - 1]
				assert diagonal_score >= 0

				lowest_global_distance = upper_score
				traceback[i][j] = (i - 1, j)

				if left_score < lowest_global_distance:
					lowest_global_distance = left_score
					traceback[i][j] = (i, j - 1)

				if diagonal_score < lowest_global_distance:
					lowest_global_distance = diagonal_score
					traceback[i][j] = (i - 1, j - 1)

				grid[i][j] = lowest_global_distance + word_score
		else:
			progress_bar.update(n)

	progress_bar.close()

	return grid, traceback


def calculate_backtrace(traceback):
	assert len(traceback) > 0
	assert len(traceback[0]) > 0

	m = len(traceback)
	n = len(traceback[0])

	alignment = []

	i, j = m - 1, n - 1
	alignment.append((i, j))

	while (i != 0) or (j != 0):
		coordinates = traceback[i][j]
		alignment.append(coordinates)
		i, j = coordinates

	alignment.reverse()

	return alignment


def convert_to_script_entities(script):
	script_entities = [ScriptEntity.from_dict(script_dict) for script_dict in script]
	return list(filter(lambda x: x.type == "speech", script_entities))


def prepare_text(text):
	text = remove_punctuation(text).lower()

	return text


def map_words_to_entity(entities, extraction_function):
	index = []
	lower_boundary = 0

	for i, entity in enumerate(entities):
		text = extraction_function(entity)
		words = text.split()

		for j, word in enumerate(words):
			index.append((word, entity))

		lower_boundary += len(words)

	return index


class Match(object):
	def __init__(self, vertical, horizontal):
		self.s1_word, self.s1_entity = vertical
		self.s2_word, self.s2_entity = horizontal
		self.matches = self.__matches()

	def __matches(self):
		d = editdistance.eval(self.s1_word, self.s2_word)
		length = len(self.s1_word)

		assert length > 0
		if d <= length and (d / length) <= 0.5:
			return True
		else:
			return False

	def format(self):
		return "[{} {} {}]".format(self.s1_word, "==" if self.matches else "!=", self.s2_word)


def speeches_from_matches(matches):
	d = {}
	for match in matches:
		d[match.s2_entity.text] = match.s2_entity

	return list(d.values())


def group_matches_by_speech(matches):
	groups = list([list(group) for key, group in groupby(matches, lambda m: m.s2_entity)])
	return groups


def max_matching_group(groups):
	match_counts = []
	for group in groups:
		count = len(filter_valid_matches(group))
		match_counts.append(count)

	m = max(match_counts)

	print(match_counts)
	for i, j in enumerate(match_counts):
		if j == m:
			return groups[i]

	return None


def filter_valid_matches(matches):
	return [match for match in matches if match.matches]


def vote(alignment, logger):
	alignments = alignment.alignment_list
	vertical_index = alignment.vertical_index
	horizontal_index = alignment.horizontal_index
	subtitles = alignment.subtitles

	prev_index = 0
	current_subtitle_index = 0
	current_subtitle = vertical_index[0][1]

	for i, (word, subtitle) in enumerate(vertical_index):
		upper_bound = i
		if i == len(vertical_index) - 1:
			upper_bound = i + 1
		elif current_subtitle == subtitle:
			continue

		word_alignments = [(m, n) for m, n in alignments if prev_index <= m < upper_bound]
		aligned_matches = [Match(vertical_index[m], horizontal_index[n]) for m, n in word_alignments]

		# find the best match if multiple speeches are hit by the alignment
		speech_grouped_match = group_matches_by_speech(aligned_matches)
		matches = max_matching_group(speech_grouped_match)

		# retrieve only word matches which are actually matching
		matches = filter_valid_matches(matches)

		possible_matches = upper_bound - prev_index
		matches_count = len(matches)
		match = matches_count >= (possible_matches / 2.0)
		match_in_percent = matches_count / possible_matches * 100

		if match:
			s2_entity = matches[0].s2_entity
			current_subtitle.character = s2_entity.character

		formatted_matches = ", ".join([match.format() for match in matches])

		logger.add("{}. {}Match".format(current_subtitle_index, "" if match else "No "))
		logger.add("\"{}\" {}/{} ({:.1f}%)".format(current_subtitle.text, matches_count, possible_matches,
		                                           match_in_percent))
		logger.add("{}".format([speech.text for speech in speeches_from_matches(matches)]))
		logger.add("{}".format(formatted_matches))
		logger.add("\n")

		prev_index = i
		current_subtitle = subtitle
		current_subtitle_index += 1

	subtitles_length = len(subtitles)
	merged_subtitles_count = len([subtitle for subtitle in subtitles if subtitle.character is not None])
	success_rate = merged_subtitles_count / subtitles_length * 100
	logger.add("Success Rate: {} of {} ~ {:.1f}%".format(merged_subtitles_count, subtitles_length, success_rate))

	return subtitles


def perform(speeches, subtitles, logger, distance_function=binary_distance, verbose=False):
	subtitles = deepcopy(subtitles)
	speeches = deepcopy(speeches)

	subtitle_index = map_words_to_entity(subtitles, lambda entity: prepare_text(entity.text))
	speeches_index = map_words_to_entity(speeches, lambda entity: prepare_text(entity.text))

	print("Words\nSubtitles:\t{}\nScripts:\t{}".format(len(subtitle_index), len(speeches_index)))

	grid, traceback = dtw(subtitle_index, speeches_index, distance_function, logger)

	alignment_list = calculate_backtrace(traceback)
	alignment = Alignment(alignment_list, subtitle_index, speeches_index, grid, traceback, subtitles)

	# voting
	subtitles = vote(alignment, logger)
	alignment.subtitles = subtitles

	return alignment


def run(speeches, subtitles, partial=1, logger=None, verbose=False):
	subtitles = subtitles[0:int(len(subtitles) / partial)]
	speeches = speeches[0:int(len(speeches) / partial)]

	print("Subtitles:\t{}\nScripts:\t{}".format(len(subtitles), len(speeches)))

	return perform(speeches, subtitles, logger, distance_function=binary_distance, verbose=verbose)
