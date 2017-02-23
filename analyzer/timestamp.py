import re


class Timestamp(object):
	def __init__(self, val):
		if type(val) is str:
			timestamp_pattern = "(?:(?:(?:(\d?\d):)?(\d?\d):)?(\d?\d))?(?:[,.](\d?\d?\d))?"
			regex = re.compile(timestamp_pattern)
			regex_result = regex.match(val)

			if regex_result is not None:
				groups = regex_result.groups()
				hours = entity_to_int(groups[0])
				minutes = entity_to_int(groups[1])
				seconds = entity_to_int(groups[2])
				milliseconds = entity_to_int(groups[3])

				self.millis = (hours_to_millis(hours) +
				               minutes_to_millis(minutes) +
				               seconds_to_millis(seconds) +
				               milliseconds)
		elif type(val) is int:
			self.millis = val
		else:
			raise Exception("Timestamp parse failed")

	def __str__(self):
		return "{}".format(self.millis)

	def __repr__(self):
		return self.__str__()

	def __add__(self, other):
		return Timestamp(self.millis + other.millis)

	def __sub__(self, other):
		return Timestamp(self.millis - other.millis)


def entity_to_int(entity):
	if entity is None:
		return 0

	return int(entity)


def hours_to_millis(hours):
	return minutes_to_millis(hours * 60)


def minutes_to_millis(minutes):
	return seconds_to_millis(minutes * 60)


def seconds_to_millis(seconds):
	return seconds * 1000
