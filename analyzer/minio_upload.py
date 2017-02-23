import glob
from tqdm import tqdm
from analyzer.project import Project, StoragePath
from minio import Minio
from minio.policy import Policy
from minio.error import ResponseError

from analyzer.utils import env
from analyzer.path_utils import filename
from os.path import join

BUCKET_NAME = "thesis-video-data"

STORE_HOST = env("STORE_HOST", "localhost")
ACCESS_KEY = env("STORE_ACCESS_KEY")
SECRET_KEY = env("STORE_SECRET_KEY")


class Uploader(object):
	def __init__(self):
		if STORE_HOST is None:
			raise Exception("Missing minio host info")

		if ACCESS_KEY is None or SECRET_KEY is None:
			raise Exception("Missing minio credentials")

		self.minio_client = Minio(STORE_HOST + ':9000',
		                          access_key=ACCESS_KEY,
		                          secret_key=SECRET_KEY,
		                          secure=False)

		try:
			if not self.minio_client.bucket_exists(BUCKET_NAME):
				self.minio_client.make_bucket(BUCKET_NAME, location="us-east-1")
				self.minio_client.set_bucket_policy(BUCKET_NAME, "", Policy.READ_ONLY)
		except ResponseError as err:
			print(err)

	def upload_frames(self, project):
		source_path = project.folder_path(Project.Folder.frames)
		remote_path = project.folder_path(Project.Folder.frames, storage_env=StoragePath.remote)

		self.upload_images(source_path, remote_path)

	def upload_keyframes(self, project):
		source_path = project.folder_path(Project.Folder.keyframes)
		remote_path = project.folder_path(Project.Folder.keyframes, storage_env=StoragePath.remote)

		self.upload_images(source_path, remote_path)

	def upload_slices(self, project):
		source_path = project.folder_path(Project.Folder.spatio)
		remote_path = project.folder_path(Project.Folder.spatio, storage_env=StoragePath.remote)

		self.upload_images(source_path, remote_path)

	def upload_keyframe_thumbnails(self, project):
		source_path = project.folder_path(Project.Folder.keyframe_thumbnails)
		remote_path = project.folder_path(Project.Folder.keyframe_thumbnails, storage_env=StoragePath.remote)

		self.upload_images(source_path, remote_path)

	def upload_images(self, source_path, destination_path):
		image_paths = glob.glob(join(source_path, "*.jpg"))

		progress_bar = tqdm(total=len(image_paths), desc="upload")
		for path in image_paths:
			remote_path = join(destination_path, filename(path))

			try:
				self.minio_client.fput_object(BUCKET_NAME, remote_path, path)
			except ResponseError as error:
				print("Upload failed")
				print(error)

			progress_bar.update()
		progress_bar.close()
