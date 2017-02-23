import glob

from os.path import join
from pprint import pprint

import cv2
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt

from analyzer import plot
from analyzer.project import Project
from analyzer.shot_detection import Shot
from analyzer.utils import window, extract_index, slice_paths, derivative, crop_image


clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(16, 16))


def load_image(path):
	image = cv2.imread(path)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	return gray


def calculate_edges(image):
	con = clahe.apply(image)
	blurred = cv2.GaussianBlur(con, (3, 3), 0)
	edges = cv2.Canny(blurred, 40, 120)

	# show the images
	# plt.hist(image.ravel(), 256, [0, 256])
	# plt.ylim(0, 5000)
	# plt.show()
	#
	# plt.hist(con.ravel(), 256, [0, 256])
	# plt.ylim(0, 5000)
	# plt.show()

	# cv2.imshow("Edges", np.hstack([image, con, edges]))
	# cv2.waitKey(0)

	return con, blurred, edges


def dilate_edges(edge_image, radius=5):
	height, width = edge_image.shape

	# convert to list due to faster accessing of elements
	image = list(edge_image)
	dilated_image = np.zeros((height, width), dtype=np.uint8)

	for i in range(height):
		for j in range(width):
			val = image[i][j]
			if val:
				cv2.circle(dilated_image, (j, i), radius, 255, -1)
			# cv2.imshow("Dilated Edges", np.hstack([edge_image, dilated_image]))
			# cv2.waitKey(1)

	return dilated_image


def count_in_out_edges(i0, i1):
	xor = np.logical_xor(i0, i1)
	logical = np.logical_and(i0, xor)
	counter = np.sum(logical)

	return counter


def calculate_image_registration(project, im1, im2, i):
	# Find size of image1
	sz = im1.shape

	# Define the motion model
	warp_mode = cv2.MOTION_TRANSLATION

	# Define 2x3 or 3x3 matrices and initialize the matrix to identity
	if warp_mode == cv2.MOTION_HOMOGRAPHY:
		warp_matrix = np.eye(3, 3, dtype=np.float32)
	else:
		warp_matrix = np.eye(2, 3, dtype=np.float32)

	# Specify the number of iterations.
	number_of_iterations = 5000

	# Specify the threshold of the increment
	# in the correlation coefficient between two iterations
	termination_eps = 1e-10

	# Define termination criteria
	criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)

	# Run the ECC algorithm. The results are stored in warp_matrix.
	try:
		(cc, warp_matrix) = cv2.findTransformECC(im2, im1, warp_matrix, warp_mode, criteria)
	except Exception:
		return im1, im2, crop_image(im1), crop_image(im2)

	if warp_mode == cv2.MOTION_HOMOGRAPHY:
		print("MOTION_HOMOGRAPHY")
		# Use warpPerspective for Homography
		aligned = cv2.warpPerspective(im1, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
	else:
		# Use warpAffine for Translation, Euclidean and Affine
		aligned = cv2.warpAffine(im1, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)

	# plots_path = project.folder_path(Project.Folder.plots)
	# cv2.imwrite(join(plots_path, "{}_im_0.jpg".format(i)), im1)
	# cv2.imwrite(join(plots_path, "{}_im_1.jpg".format(i)), im2)
	# cv2.imwrite(join(plots_path, "{}_im_2.jpg".format(i)), aligned)

	# dst0 = cv2.addWeighted(im1, 0.5, im2, 0.5, 0)
	# dst1 = cv2.addWeighted(aligned, 0.5, im1, 0.5, 0)
	# dst2 = cv2.addWeighted(aligned, 0.5, im2, 0.5, 0)

	# cv2.imwrite(join(plots_path, "{}_im_dst_01.jpg".format(i)), dst0)
	# cv2.imwrite(join(plots_path, "{}_im_dst_20.jpg".format(i)), dst1)
	# cv2.imwrite(join(plots_path, "{}_im_dst2_21.jpg".format(i)), dst2)

	# # Show final results
	# cv2.imshow("Registration", np.hstack([im1, im2, aligned]))
	# cv2.waitKey(0)

	return im1, im2, crop_image(aligned), crop_image(im2)


def edge_detect(project, threshold, limit=None, image_registration=False, local_sequence=False):
	src = project.folder_path(Project.Folder.frames)
	image_paths = glob.glob(src + "/*.jpg")

	if limit:
		image_paths = slice_paths(image_paths, limit)

	if local_sequence:
		sequence = project.read(Project.File.shot_change_ratio)
	else:
		sequence = calculate_sequence(project, image_paths, limit, image_registration)
		sequence and project.write(sequence, Project.File.shot_change_ratio)

	shots = extract_shots(sequence, image_paths, threshold, project)

	return shots


def calculate_sequence(project, image_paths, limit, image_registration):
	sequence = []
	progress_bar = tqdm(total=len(image_paths), desc="shots detection")

	for i, (p0, p1) in enumerate(window(image_paths, 2)):
		file_index = extract_index(p0)
		image0 = load_image(p0)
		image1 = load_image(p1)

		if image_registration:
			image0_orig, image1_orig, image0, image1 = calculate_image_registration(project, image0, image1, file_index)

		con0, blurred0, edges0 = calculate_edges(image0)
		con1, blurred1, edges1 = calculate_edges(image1)

		dilated0 = dilate_edges(edges0)
		dilated1 = dilate_edges(edges1)

		# plots_path = project.folder_path(Project.Folder.plots)
		# cv2.imwrite(join(plots_path, "{}_gray_0.jpg".format(file_index)), image0)
		# cv2.imwrite(join(plots_path, "{}_gray_1.jpg".format(file_index)), image1)
		#
		# cv2.imwrite(join(plots_path, "{}_con_0.jpg".format(file_index)), np.hstack([con0]))
		# cv2.imwrite(join(plots_path, "{}_con_1.jpg".format(file_index)), np.hstack([con1]))
		#
		# cv2.imwrite(join(plots_path, "{}_blurred_0.jpg".format(file_index)), np.hstack([blurred0]))
		# cv2.imwrite(join(plots_path, "{}_blurred_1.jpg".format(file_index)), np.hstack([blurred1]))
		#
		# cv2.imwrite(join(plots_path, "{}_edges_0.jpg".format(file_index)), edges0)
		# cv2.imwrite(join(plots_path, "{}_edges_1.jpg".format(file_index)), edges1)
		# cv2.imwrite(join(plots_path, "{}_dilated_0.jpg".format(file_index)), dilated0)
		# cv2.imwrite(join(plots_path, "{}_dilated_1.jpg".format(file_index)), dilated1)

		out_edges = count_in_out_edges(edges0, dilated1)
		in_edges = count_in_out_edges(edges1, dilated0)

		edge_count0 = np.count_nonzero(edges0)
		edge_count1 = np.count_nonzero(edges1)

		p_out = out_edges/edge_count0 if edge_count0 else 0
		p_in = in_edges/edge_count1 if edge_count1 else 0

		dist = max(p_out, p_in)

		sequence.append(dist)
		progress_bar.update()

	progress_bar.close()

	return sequence


def extract_shots(distances, image_paths, threshold, project):
	# pprint(["{}: {}".format(extract_index(path), d) for d, path in zip(distances, image_paths)])

	distances = derivative(distances)

	# plot.plot("edge_detection_derivative", [distances], project=project, store=True, ylim=(0.0, 1.0), xlim=(0.0, len(distances)))
	# pprin(["{}: {}".format(extract_index(path), d) for d, path in zip(distances, image_paths)])

	last_shot_index = extract_index(image_paths[0])
	last_index = len(distances) - 1
	shots = []

	plot_test = [(0, 0)]

	progress_bar = tqdm(total=len(distances), desc="shots extraction")
	for i, val in enumerate(distances):
		if val > threshold or last_index == i:
			plot_test.append((i, val))
			image_index = extract_index(image_paths[i])

			shot = Shot(last_shot_index, image_index, len(shots), int(val))
			shots.append(shot)
			last_shot_index = image_index
		progress_bar.update()

	progress_bar.close()

	x, y = zip(*plot_test)
	plot.plot("edge_detection", [distances], [(x, y)], project, store=True, ylim=(0.0, 1.0), xlim=(0.0, len(distances)))

	return shots
