import boto3
from boto3.session import Session
from botocore.client import ClientError
import glob
from os.path import join
from analyzer.path_utils import filename
from analyzer.project import StoragePath, Project
from analyzer.utils import env

BUCKET_NAME = "thesis-video-data"

ACCESS_KEY = env("AWS_ACCESS_KEY")
SECRET_KEY = env("AWS_SECRET_KEY")
LOCATION = env("AWS_LOCATION")


def connect_bucket():
	print(ACCESS_KEY, SECRET_KEY)

	session = Session(aws_access_key_id=ACCESS_KEY,
	                  aws_secret_access_key=SECRET_KEY,
	                  region_name=LOCATION)
	s3 = session.resource("s3")

	try:
		s3.meta.client.head_bucket(Bucket=BUCKET_NAME)
		bucket = s3.Bucket(BUCKET_NAME)
	except ClientError:
		bucket = s3.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'})

	return bucket


def upload_frames(project):
	source_path = project.folder_path(Project.Folder.frames)
	remote_path = project.folder_path(Project.Folder.frames, storage_env=StoragePath.remote)

	upload_images(source_path, remote_path)


def upload_keyframes(project):
	source_path = project.folder_path(Project.Folder.keyframes)
	remote_path = project.folder_path(Project.Folder.keyframes, storage_env=StoragePath.remote)

	upload_images(source_path, remote_path)


def upload_slices(project):
	source_path = project.folder_path(Project.Folder.spatio)
	remote_path = project.folder_path(Project.Folder.spatio, storage_env=StoragePath.remote)

	upload_images(source_path, remote_path)


def upload_images(source_path, destination_path):
	bucket = connect_bucket()

	image_paths = sorted(glob.glob(join(source_path, "*.jpg")))
	for path in image_paths:
		remote_path = join(destination_path, filename(path))

		data = open(path, 'rb')
		bucket.put_object(Key=remote_path, Body=data)


def upload_keyframes_montage(project):
	bucket = connect_bucket()

	path = project.file_path(Project.File.keyframe_montage)
	remote_path = join(project.folder_path("", storage_env=StoragePath.remote), filename(path))

	data = open(path, 'rb')
	bucket.put_object(Key=remote_path, Body=data)


def upload_keyframe_thumbnails(project):
	source_path = project.folder_path(Project.Folder.keyframe_thumbnails)
	remote_path = project.folder_path(Project.Folder.keyframe_thumbnails, storage_env=StoragePath.remote)

	upload_images(source_path, remote_path)
