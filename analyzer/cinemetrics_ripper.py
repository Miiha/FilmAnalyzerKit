import time
from bs4 import BeautifulSoup
import urllib.request
from analyzer.database import Database
import re
from datetime import datetime


def run():
	rip_site()


def load(id):
	url = "http://www.cinemetrics.lv/data.php?movie_ID={}".format(id)
	try:
		request = urllib.request.Request(url)
		webpage_bytes = urllib.request.urlopen(request)
		soup = BeautifulSoup(webpage_bytes, 'lxml')
	except urllib.error.URLError as err:
		print(err)
		return None
	else:
		return soup


HEADERS = ["title", "year", "director", "country", "submittedBy", "mode", "date", "asl", "msl", "stdev"]


def int_representation(s):
	try:
		i = int(s)
		return i
	except ValueError:
		return None


def float_representation(s):
	try:
		i = float(s)
		return i
	except ValueError:
		return None


def none_empty_string(s):
	if len(s):
		return s
	else:
		return None


def date_time(s):
	date_object = datetime.strptime('2016-10-06', '%Y-%m-%d')
	return date_object


def rip_movie_list(path):
	db = Database()

	try:
		data = open(path).read()
		soup = BeautifulSoup(data, 'lxml')
	# soup = BeautifulSoup(str, 'lxml')
	except urllib.error.URLError as err:
		print(err)
		db.close()
		return None
	else:
		rows = soup.find_all("tr")
		movie_id_regex = re.compile("(?<=movie_ID=).*[0-9]")

		for row in rows:
			if "onclick" in row.attrs:
				onclick = row.attrs['onclick']
				id_match = movie_id_regex.search(onclick)

				if id_match:
					movie_id = int_representation(id_match.group(0))
					entities = row.find_all("td")

					meta_dict = {
						HEADERS[0]: none_empty_string(entities[0].text),
						HEADERS[1]: int_representation(entities[1].text),
						HEADERS[2]: none_empty_string(entities[2].text),
						HEADERS[3]: none_empty_string(entities[3].text),
						HEADERS[4]: none_empty_string(entities[4].text),
						HEADERS[5]: none_empty_string(entities[5].text),
						HEADERS[6]: date_time(entities[6]),
						HEADERS[7]: float_representation(entities[7].text),
						HEADERS[8]: float_representation(entities[8].text),
						HEADERS[9]: float_representation(entities[9].text),
						"id": movie_id
					}

					db.context.cinemetrics.update_one(
						{"id": movie_id},
						{"$set": meta_dict},
						True,
						True
					)
					print(movie_id)
	db.close()


def rip_site(start=0, end=25004):
	db = Database()

	for id in range(start, end):
		soup = load(id)
		shots = parse(soup)
		result = {"shots": shots, "id": id}

		db.context.cinemetrics.update_one(
			{"id": id},
			{"$set": result},
			True
		)

		print(id)
		time.sleep(0.25)


def parse(soup):
	table = soup.find("table")
	headers = []
	for th in table.find_all("th"):
		span = th.a.find("span")
		description = span.text
		span.unwrap()
		identifier = th.a.text.replace(description, "")
		headers.append({"identifier": identifier, "description": description})

	rows = [[td.text for td in tr.find_all("td")] for tr in table.find_all('tr')]

	# ensure that empty rows are represented as empty lists
	if len(rows) == 0:
		rows = [[] for _ in headers]

	converted_rows = []
	for row in rows:
		if not len(row):
			continue

		dict = {}
		for i, entity in enumerate(row):
			if len(headers) <= i:
				continue

			header = headers[i]
			if header["identifier"] != "Type":
				entity = int_representation(entity)

			dict[header["identifier"]] = entity

		if len(dict) > 0:
			converted_rows.append(dict)

	return converted_rows


def parse_lists(soup):
	table = soup.find("table")
	headers = []
	for th in table.find_all("th"):
		span = th.a.find("span")
		description = span.text
		span.unwrap()
		identifier = th.a.text.replace(description, "")
		headers.append({"identifier": identifier, "description": description})

	rows = [[td.text for td in tr.find_all("td")] for tr in table.find_all('tr')]
	values = list(map(list, zip(*rows)))

	# ensure that empty rows are represented as empty lists
	if len(values) == 0:
		values = [[] for _ in headers]

	# convert
	result = {}
	for i, header in enumerate(headers):
		if header["identifier"] is not "Type":
			rows = values[i]
			values[i] = map(int, rows)

		result[header["identifier"]] = values[i]

	return result

