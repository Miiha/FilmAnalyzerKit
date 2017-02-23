#!/usr/bin/python
# coding: utf-8

# Thumps up for Adrien Luxey for providing the basis for the script parser

import re
import urllib.request
from pprint import pprint
from bs4 import BeautifulSoup, Tag, UnicodeDammit

from analyzer.script_entity import ScriptEntity

BLOCK_TYPES = ['character', 'speech', 'stage direction', 'location', 'transition']
CHARACTER = 0
SPEECH = 1
DIRECTIONS = 2
LOCATION = 3
TRANSITION = 4

spaces_regex = re.compile("^(\s*).*")
location_regex = re.compile("^\s*(INT\.|EXT\.)")
transition_regex = re.compile("\s*(CUT|DISSOLVE|FADE)[^:]+(TO|OUT):")


def load(url):
	script_text = None
	script_url = ''
	is_web_page_fetched = False
	original_encoding = None

	while not is_web_page_fetched:
		# get the script's URL from the parameters if it was passed
		if script_url == '' and url is not None:
			script_url = url
		else:
			print('Please provide the URL of a movie script you want to see parsed as JSON.')
			print('The parser was intended to work with imsdb.com, and you must provide a full URL (with http[s]://)')

			script_url = input('--> ')

		try:
			request = urllib.request.Request(script_url)
			webpage_bytes = urllib.request.urlopen(request)
			soup = BeautifulSoup(webpage_bytes, 'lxml')
			original_encoding = soup.original_encoding
			print('Detected encoding is ', soup.original_encoding)
			is_web_page_fetched = True
		except urllib.error.URLError as err:
			print('Catched an URLError while fetching the URL:', err)
			print()
			pass
		except ValueError as err:
			print('Catched a ValueError while fetching the URL:', err)
			print()
			pass
		except:
			print('Catched an unrecognized error')
			raise
		else:
			# script_text = soup.find("td", class_="scrtext").find("pre")
			script_text = soup.find("pre")

			if script_text.find("pre"):
				print('Found a <pre> inside the <pre>')
				script_text = script_text.find("pre")

			print("Parsing and extracting the first <pre> resulted in the following text:")
			print(str(script_text)[:256])
			answer = input('Is that the script you expected? (Y/n) ')

			if answer == 'N' or answer == 'n':
				answer = input('Shall we try with another URL? (Y/n) ')
				if answer == 'N' or answer == 'n':
					raise ValueError('The result was not what we expected.')

			is_web_page_fetched = True

	return script_text, original_encoding


def get_line_type(line, stripped_line, usual_spaces, characters):
	# Counting the number of spaces at the beginning of the line
	spmatch = spaces_regex.search(line)
	spaces_number = len(spmatch.group(1))
	block_type = 0

	if transition_regex.search(line) is not None:
		return TRANSITION

	if location_regex.search(line) is not None:
		return LOCATION

	if stripped_line in characters:
		return CHARACTER

	# Look for space
	for block_type_usual_spaces in usual_spaces:
		if spaces_number in block_type_usual_spaces:
			block_type = usual_spaces.index(block_type_usual_spaces)
			# print('We consider {:d} leading spaces as a \'{:s}\' block.'.format(
			#      spaces_number, BLOCK_TYPES[block_type]))
			return usual_spaces.index(block_type_usual_spaces)

	print('There are {:d} space(s) at the beginning of this line'.format(spaces_number))
	question = "What kind of block is that?\n"
	for i in range(len(BLOCK_TYPES)):
		question += '\t(' + str(i) + ') ' + BLOCK_TYPES[i] + '\n'
	print(question)

	validated = False
	while not validated:
		try:
			block_type = int(input('? [0-{:d}] '.format(len(BLOCK_TYPES) - 1)))
			while block_type < 0 or block_type >= len(BLOCK_TYPES):
				block_type = int(input('? [0-{:d}] '.format(len(BLOCK_TYPES) - 1)))
		except ValueError:
			continue

		validated = True
		answer = input('You said the last block type was \'{:s}\', sure about that? (Y/n) '.format(
			BLOCK_TYPES[block_type]))
		if answer == 'n' or answer == 'N':
			validated = False

	remember_spaces = False
	validated = False
	while not validated:
		answer_spaces = input('Are all  lines with {:d} leading spaces \'{:s}\' blocks ? (Y/n) '.format(
			spaces_number, BLOCK_TYPES[block_type]))

		if answer_spaces == 'n' or answer_spaces == 'N':
			print('You said no: we will ask you again next time.')
			remember_spaces = False
		else:
			print('You said yes: ' +
				  'every new block with {:d} leading spaces '.format(spaces_number) +
				  'will now be considered a \'{:s}\'.'.format(BLOCK_TYPES[block_type]))
			remember_spaces = True

		validated = True
		answer = input('Are you sure? (Y/n) ')
		if answer == 'n' or answer == 'N':
			validated = False

	if remember_spaces:
		usual_spaces[block_type].append(spaces_number)

	return block_type


def analyze_content(script_text, encoding):
	print("\n\nStarting script parsing!\n\n")
	print("Start by telling me when the introduction will end.")

	is_intro = True
	movie_script = []
	intro = []
	last_line_type = -1
	last_character = ''
	line_type = None
	text = []
	characters = []
	usual_spaces = [[] for _ in range(len(BLOCK_TYPES))]

	for block in script_text.descendants:
		if isinstance(block, Tag):
			continue

		# UnicodeDammit converts any string to UTF-8
		# does not work so well
		block = UnicodeDammit(block, encoding).unicode_markup

		# remove leading and ending end of lines
		block = block.strip('\n')

		# if the block doesn't have any text, skip it
		if re.search('\w', block) is None:
			continue

		for line in block.split('\n'):
			stripped_line = line.strip(' \n\t\r')
			if re.search(r'\w', line) is None:
				continue

			print('------------------------------ Begin line ------------------------------')
			print(line)
			print('------------------------------- End line -------------------------------')

			if is_intro:
				print()
				answer = input("Is that still part of the intro? (Y/n) ")

				if answer == 'n' or answer == 'N':
					is_intro = False
					movie_script.append({
						'type': 'introduction',
						'text': '\n'.join(intro)})

					print(movie_script[-1])
				else:
					print("OK")
					print()
					intro.append(stripped_line)
					continue

			line_type = get_line_type(line, stripped_line, usual_spaces, characters)
			print("The last line was interpreted as '{}'".format(BLOCK_TYPES[line_type]))
			print()

			if last_line_type == -1 or last_line_type == line_type:  # -1 = not initialized
				text.append(stripped_line)
			else:
				if last_line_type == CHARACTER:
					last_character = '\n'.join(text)
					if not last_character in characters:
						characters.append(last_character)
				elif last_line_type == SPEECH:
					movie_script.append({
						'type': BLOCK_TYPES[last_line_type],
						BLOCK_TYPES[CHARACTER]: last_character,
						'text': '\n'.join(text)})
					print('We just parsed this JSON block:')
					print(movie_script[-1])
				else:
					movie_script.append({
						'type': BLOCK_TYPES[last_line_type],
						'text': '\n'.join(text)})
					print('We just parsed this JSON block:')
					print(movie_script[-1])
				text = [stripped_line]

			last_line_type = line_type
			print()

		print()
		print()

	movie_script.append({
		'type': BLOCK_TYPES[line_type],
		'text': '\n'.join(text)})

	print('We just parsed this JSON block:')
	print(movie_script[-1])
	print()
	print()

	return movie_script


def clean_script(script):
	for script_entity in script:
		if script_entity["type"] == "speech":
			text = script_entity["text"]
			sub_str = re.sub('\(.*?\)', '', text)

			if sub_str:
				script_entity["text"] = sub_str.strip()
				script_entity["original_text"] = text

	return script


def convert_to_hierarchy(project, script):
	locations = []
	speeches_in_location = []
	current_location = None
	for i, script_entity in enumerate(script):
		if script_entity["type"] == "location":
			if len(speeches_in_location) > 0:
				locations.append({"location": current_location, "speeches": speeches_in_location})
				speeches_in_location = []

			current_location = script_entity["text"]

		if script_entity["type"] == "speech":
			speeches_in_location.append(script_entity)

		if i == len(script) - 1 and len(speeches_in_location) > 0:
			locations.append({"location": current_location, "speeches": speeches_in_location})

	pprint(locations)


def run(url):
	script_text, encoding = load(url)
	parsed_entities = analyze_content(script_text, encoding)
	script = clean_script(parsed_entities)
	entities = [ScriptEntity.from_dict(d) for d in script]

	return entities
