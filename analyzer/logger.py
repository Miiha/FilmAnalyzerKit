import datetime


class Logger(object):
	def __init__(self, project, verbose=True):
		self.project = project
		self.verbose = verbose
		self.messages = []

	def add(self, message, end="\n"):
		print(message)
		self.messages.append(message)
		self.messages.append(end)

	def write(self):
		formatted_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H-%M-%S')
		path = self.project.file_path(formatted_date + ".txt")
		with open(path, "w") as log:
			log.write("".join(self.messages))
