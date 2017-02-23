
class Alignment(object):
	old_vertical_index = None
	old_horizontal_index = None

	def __init__(self, alignment_list, vertical_index, horizontal_index, grid, traceback, subtitles=None):
		self.alignment_list = alignment_list
		self.vertical_index = vertical_index
		self.horizontal_index = horizontal_index
		self.grid = grid
		self.traceback = traceback
		self.subtitles = subtitles
