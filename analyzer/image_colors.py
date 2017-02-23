import cv2
import numpy as np

from sklearn.cluster import KMeans
from os import path
from tqdm import tqdm

from analyzer.project import Project
from analyzer.utils import image_filename


def colors_from_image(image_path, count):
	gbr_image = cv2.imread(image_path)

	rgb_image = cv2.cvtColor(gbr_image, cv2.COLOR_BGR2RGB)
	img = rgb_image.reshape((rgb_image.shape[0] * rgb_image.shape[1], 3))

	clt = KMeans(n_clusters=count)
	clt.fit(img)

	hist = centroid_histogram(clt)
	cluster_centers = clt.cluster_centers_

	bundle = sort_frequency_with_clusters(hist, cluster_centers)

	clusters = rearrange_cluster(bundle)

	return clusters


def sort_frequency_with_clusters(hist, cluster_centers):
	cluster_centers = cluster_centers.astype(int).tolist()
	hist = [round(val, 4) for val in hist]

	bundle = list(zip(hist, cluster_centers))
	bundle.sort(reverse=True)

	return bundle


def centroid_histogram(clt):
	num_labels = np.arange(0, len(np.unique(clt.labels_)) + 1)
	(hist, _) = np.histogram(clt.labels_, bins=num_labels)

	hist = hist.astype("float")
	hist /= hist.sum()

	return hist


def rearrange_cluster(colors):
	return [{"frequency": bundle[0], "values": bundle[1]} for bundle in colors]


def run(project, shots, cluster_count):
	progress_bar = tqdm(total=len(shots), desc="colors")

	for shot in shots:
		filename = image_filename(shot.keyframe.index)
		image_path = path.join(project.folder_path(Project.Folder.keyframes), filename)

		shot.keyframe.colors = colors_from_image(image_path, cluster_count)
		progress_bar.update()

	progress_bar.close()

	return shots
