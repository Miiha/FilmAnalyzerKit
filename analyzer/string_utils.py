import re
import string


def remove_punctuation(text):
	exclude = set(string.punctuation)
	exclude.add("'")

	characters = []
	for character in text:
		if character not in exclude:
			characters.append(character)
		else:
			characters.append(" ")

	cleaned_text = "".join(characters)
	var = re.sub(' +', ' ', cleaned_text)

	return var
