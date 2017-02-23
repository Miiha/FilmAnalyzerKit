import base64
from os import path

from tqdm import tqdm
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from analyzer import utils
from analyzer.project import Project
from analyzer.shot_detection import Label

DISCOVERY_URL = 'https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'


def run(project, shots):
	def shot_to_keyframe_path(shot):
		index = shot.keyframe.index
		filename = utils.image_filename(index)
		return path.join(project.folder_path(Project.Folder.keyframes), filename)

	progress_bar = tqdm(total=len(shots), desc="labels")
	for shot in shots:
		p = shot_to_keyframe_path(shot)
		label_annotations = detect(p)

		if label_annotations:
			shot.keyframe.labels = [Label.from_dict(a, from_camel=False) for a in label_annotations]

		progress_bar.update()

	progress_bar.close()

	return shots


def detect(file_path):
	"""Run a label request on a single image"""

	credentials = GoogleCredentials.get_application_default()
	service = discovery.build('vision', 'v1', credentials=credentials,
	                          discoveryServiceUrl=DISCOVERY_URL)

	with open(file_path, 'rb') as image:
		image_content = base64.b64encode(image.read())
		service_request = service.images().annotate(body={
			'requests': [{
				'image': {
					'content': image_content.decode('UTF-8')
				},
				'features': [{
					'type': 'LABEL_DETECTION',
					'maxResults': 3
				}]
			}]
		})
		response = service_request.execute()
		responses = response.get('responses')
		if responses and len(response) > 0:
			label_annotations = responses[0].get('labelAnnotations')
			return label_annotations
		else:
			return None
