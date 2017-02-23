import csv


def export_subtitles(project, subtitles):
	path = project.file_path("subtitles_char.csv")

	with open(path, 'w', newline='') as file:
		writer = csv.writer(file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['sep=\t'])
		writer.writerow(["id", "text", "char"])
		for i, s in enumerate(subtitles):
			writer.writerow([i, s.original_text, s.character])


def export_script(project, script):
	path = project.file_path("script.csv")

	with open(path, 'w', newline='') as file:
		writer = csv.writer(file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['sep=\t'])
		writer.writerow(["id", "text", "char"])

		script = [s for s in script if s.type == "speech"]
		for i, s in enumerate(script):
			writer.writerow([i, s.original_text, s.character])

