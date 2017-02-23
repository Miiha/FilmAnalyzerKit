from os.path import join

from matplotlib import pyplot as plt


def plot(title, datum, scatter=None, project=None, store=False, xlim=None, ylim=None):
	plt.figure("Results {}".format(title))
	if xlim:
		plt.xlim(xlim)

	if ylim:
		plt.ylim(ylim)

	for data in datum:
		plt.plot(data)

	if scatter:
		for x, y in scatter:
			plt.scatter(x, y, color="green")

	if not store:
		plt.show()
	else:
		base_path = project.folder_path("plots")
		path = join(base_path, "{}.jpg".format(title))
		plt.savefig(path)

	plt.clf()
	plt.cla()
	plt.close()