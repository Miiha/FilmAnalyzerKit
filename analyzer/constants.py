from enum import unique, Enum


@unique
class ExtractionType(Enum):
	histogram = "histogram"
	simpleHistogram = "simpleHistogram"
	edge = "edge"
	edgeim = "edgeim"


@unique
class CharactersAlgorithm(Enum):
	dtw = "dtw"
	nw = "nw"
