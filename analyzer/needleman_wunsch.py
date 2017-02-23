import editdistance
from enum import Enum
from tqdm import tqdm
from copy import deepcopy

from analyzer.alignment_utils import Alignment
from analyzer.string_utils import remove_punctuation


class Direction(Enum):
	up = 1
	left = 2
	diagonal = 3


class GapPenalty(object):
	def __init__(self, gap):
		self.gap = gap

	def score(self, i, j, traceback, direction):
		return self.gap


class AdaptiveGapPenalty(GapPenalty):
	def __init__(self, gap, extended_gap):
		super().__init__(gap)

		self.extended_gap = extended_gap

	def score(self, i, j, traceback, direction):
		if direction == Direction.left:
			coordinates = traceback[i][j - 1]
			if coordinates is not None and coordinates[0] == i:
				return self.extended_gap
			else:
				return self.gap
		elif direction == Direction.up:
			coordinates = traceback[i - 1][j]
			if coordinates is not None and coordinates[1] == j:
				return self.extended_gap
			else:
				return self.gap
		else:
			return None


class Weighting(object):
	def __init__(self, match, miss_match, gap_penalty):
		self.match = match
		self.miss_match = miss_match
		self.gap_penalty = gap_penalty

	def match_characters(self, a, b):
		return self.match if a == b else self.miss_match


class ScoreMatrix(object):
	def __init__(self, grid, traceback, weighting):
		self.grid = grid
		self.traceback = traceback
		self.weighting = weighting

	def score(self, direction, i, j, c1=None, c2=None):
		if direction == Direction.diagonal:
			assert (c1)
			assert (c2)

			return self.weighting.match_characters(c1, c2)
		elif direction == Direction.up or direction == Direction.left:
			return self.weighting.gap_penalty.score(i, j, self.traceback, direction)
		else:
			return None


DEFAULT_WEIGHTING = Weighting(1, -1, GapPenalty(-2))


def pretty_print_grid(alignment):
	grid = alignment.grid
	subtitle_index = alignment.old_vertical_index
	script_index = alignment.old_horizontal_index
	alignments = alignment.alignment_list

	def search_indexes(i, j):
		for alignment in alignments:
			if alignment == (i, j):
				return True

		return False

	max = 10

	print()
	for i, (char, speech) in enumerate(script_index):
		if i == 0:
			print("     ", end="")
			print("{: ^7}".format(" "), end="")

		print("{: ^7}".format(char), end="")

		if i == len(script_index) - 1:
			print()

	for row in range(len(grid)):
		for column in range(len(grid[row])):

			d = grid[row][column]

			if column == 0 and row == 0:
				print("{:<5}".format(" "), end="")
			elif column == 0:
				char, subtitle = subtitle_index[row - 1]
				w = (char[:max] + '..') if len(char) + 2 > max else char
				print("{:<5}".format(w), end="")

			if search_indexes(row, column):
				print("[{: ^5.1f}]".format(d), end="")
			else:
				print("{: ^7.1f}".format(d), end="")

		print()

	print()


def map_characters_to_entity(entities, extraction_function):
	index = []
	lower_boundary = 0

	for i, entity in enumerate(entities):
		text = extraction_function(entity)
		characters = list(text)

		for j, char in enumerate(characters):
			index.append((char, entity))

		lower_boundary += len(characters)

	return index


def prepare_data(speeches, subtitles):
	subtitle_index = map_characters_to_entity(subtitles, lambda entity: entity.text)
	speeches_index = map_characters_to_entity(speeches, lambda entity: entity.text)

	return subtitle_index, speeches_index


def nw(subtitle_index, script_index, weighting, verbose=False):
	m = len(subtitle_index) + 1
	n = len(script_index) + 1
	size = m * n

	print("\ninitializing grid...\n")

	grid = [x[:] for x in [[0] * n] * m]
	traceback = [x[:] for x in [[0] * n] * m]
	score_matrix = ScoreMatrix(grid, traceback, weighting)

	progress_bar = tqdm(total=size, desc="nw")

	for i in range(m):
		for j in range(n):

			if (i == 0) and (j == 0):
				grid[i][j] = 0
				traceback[i][j] = None

			elif i == 0:
				assert grid[i][j - 1] <= 0
				penalty = score_matrix.score(Direction.left, i, j)

				grid[i][j] = grid[i][j - 1] + penalty
				traceback[i][j] = (i, j - 1)

			elif j == 0:
				assert grid[i - 1][j] <= 0
				penalty = score_matrix.score(Direction.up, i, j)

				grid[i][j] = grid[i - 1][j] + penalty
				traceback[i][j] = (i - 1, j)

			else:
				# upper
				penalty = score_matrix.score(Direction.up, i, j)

				current_maximum = grid[i - 1][j] + penalty
				traceback[i][j] = (i - 1, j)

				# left
				penalty = score_matrix.score(Direction.left, i, j)

				if grid[i][j - 1] + penalty > current_maximum:
					current_maximum = grid[i][j - 1] + penalty
					traceback[i][j] = (i, j - 1)

				# diagonal
				if grid[i - 1][j - 1] > current_maximum:
					prev_distance = grid[i - 1][j - 1]
					s1_char, _ = subtitle_index[i - 1]
					s2_char, _ = script_index[j - 1]

					distance = score_matrix.score(Direction.diagonal, i, j, s1_char, s2_char)
					current_maximum = prev_distance + distance
					traceback[i][j] = (i - 1, j - 1)

				grid[i][j] = current_maximum

		progress_bar.update(n)
	progress_bar.close()

	return grid, traceback


def calculate_backtrace(grid, traceback, subtitle_index, script_index):
	assert len(grid) > 0
	assert len(grid[0]) > 0

	m = len(grid)
	n = len(grid[0])

	alignment = []

	i, j = m - 1, n - 1
	alignment.append((i, j))
	new_subtitle_index = []
	new_script_index = []

	while (i != 0) or (j != 0):
		x, y = traceback[i][j]
		alignment.append((x, y))

		s1_char, subtitle = subtitle_index[i - 1]
		s2_char, script = script_index[j - 1]

		if x < i and y < j:  # match
			new_subtitle_index.append((s1_char, subtitle))
			new_script_index.append((s2_char, script))
		elif x < i and y == j:  # up == insert in s2
			new_subtitle_index.append((s1_char, subtitle))
			new_script_index.append(("_", script))
		elif y < j and x == i:  # left == insert in s1
			new_subtitle_index.append(("_", subtitle))
			new_script_index.append((s2_char, script))

		i, j = x, y

	alignment.reverse()
	new_subtitle_index.reverse()
	new_script_index.reverse()

	a = Alignment(alignment, new_subtitle_index, new_script_index, grid, traceback)
	a.old_vertical_index = subtitle_index
	a.old_horizontal_index = script_index

	return a


def filter_gaps(s1, s2):
	gap = "_"

	gap_filter = lambda c1, c2: False if c1 == gap or c2 == gap else True
	zipped = [(c1, c2) for c1, c2 in zip(s1, s2) if gap_filter(c1, c2)]

	# only gaps, sequences can not be aligned
	if len(zipped) == 0:
		return "", ""

	unzipped = zip(*zipped)
	s1, s2 = ["".join(list(a)) for a in unzipped]

	return s1, s2


def vote(alignment, logger):
	s1_index = 0
	subtitle_index = alignment.vertical_index
	script_index = alignment.horizontal_index
	subtitles = alignment.subtitles

	current_subtitle = subtitle_index[0][1]
	index = 0
	for i, (char, subtitle) in enumerate(subtitle_index):
		if i == len(subtitle_index) - 1:
			pass
		elif current_subtitle == subtitle:
			continue

		s1_matches = subtitle_index[s1_index:1 if i == 0 else i]  # i == 0 cant return the first element
		s2_matches = script_index[s1_index:1 if i == 0 else i]

		s1_chars = "".join([char for char, _ in s1_matches])
		s2_chars = "".join([char for char, _ in s2_matches])

		fs1_chars, fs2_chars = filter_gaps(s1_chars, s2_chars)

		if len(fs1_chars) > 0:
			d = editdistance.eval(fs1_chars, fs2_chars)
			count = len(fs1_chars)
			required_matches = count / 2.0
			matches_in_percent = 100 - d / count * 100
		else:
			d = editdistance.eval(s1_chars, s2_chars)
			required_matches = len(s1_chars) / 2.0
			matches_in_percent = 0

		match = d <= required_matches

		logger.add("{}. {}Match".format(index, "" if match else "No "))
		logger.add("'{}' has lev-dist {} ({:.1f}%).".format(current_subtitle.text, d, matches_in_percent))
		logger.add("'{}'\n'{}'\n\nactual match:\n'{}'\n'{}'".format(s1_chars, s2_chars, fs1_chars, fs2_chars))
		logger.add("\n\n")

		if match:
			script = s2_matches[0][1]
			current_subtitle.character = script.character

		current_subtitle = subtitle
		index += 1
		s1_index = i

	if logger.verbose:
		subtitles_length = len(subtitles)
		merged_subtitles_count = len([subtitle for subtitle in subtitles if subtitle.character is not None])
		success_rate = merged_subtitles_count / subtitles_length * 100
		logger.add("Success Rate: {} of {} ~ {:.1f}%".format(merged_subtitles_count, subtitles_length, success_rate))

	return alignment


def prepare_text(text):
	t = remove_punctuation(text)
	t = t.lower()

	# remove double spaces
	t = " ".join(t.split())

	return t


def perform(speeches, subtitles, weighting=DEFAULT_WEIGHTING, logger=None, verbose=False):
	subtitles = deepcopy(subtitles)
	speeches = deepcopy(speeches)

	# retrieve the index list
	subtitle_index = map_characters_to_entity(subtitles, lambda entity: prepare_text(entity.text))
	speeches_index = map_characters_to_entity(speeches, lambda entity: prepare_text(entity.text))

	print("Characters\nSubtitles:\t{}\nScripts:\t{}".format(len(subtitle_index), len(speeches_index)))

	# perform the algorithm
	grid, traceback = nw(subtitle_index, speeches_index, weighting, verbose=verbose)

	# align via backtrace and update indexes
	alignment = calculate_backtrace(grid, traceback, subtitle_index, speeches_index)
	alignment.subtitles = subtitles

	# voting of matches
	alignment = vote(alignment, logger)

	return alignment


def run(speeches, subtitles, partial=1, logger=None, verbose=False):
	subtitles = subtitles[0:int(len(subtitles) / partial)]
	speeches = speeches[0:int(len(speeches) / partial)]

	print("Subtitles:\t{}\nScripts:\t{}".format(len(subtitles), len(speeches)))

	return perform(speeches, subtitles, logger=logger, verbose=verbose)
