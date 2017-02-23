# -*- coding: utf-8 -*-
"""
Documentation
"""

from pprint import pprint

import click

from analyzer import __version__
from analyzer import chapters_parser
from analyzer import cinemetrics_ripper
from analyzer import dtw_merger
from analyzer import edge_detection
from analyzer import image_colors
from analyzer import label_detection
from analyzer import needleman_wunsch
from analyzer import path_utils
from analyzer import script_parser
from analyzer import shot_detection
from analyzer import splitter
from analyzer import subtitles_parser

from analyzer.constants import ExtractionType, CharactersAlgorithm
from analyzer.chapters_parser import Chapter
from analyzer.csv_export import export_subtitles, export_script
from analyzer.database import Database
from analyzer.logger import Logger
from analyzer.minio_upload import Uploader
from analyzer.project import Project
from analyzer.script_entity import ScriptEntity
from analyzer.shot_detection import Shot
from analyzer.subtitles_parser import Subtitle
from analyzer.utils import objects_as_dict

PROJECT_KEY = "project"
LOGGER_KEY = "logger"
VERBOSE_KEY = "verbose"
SHOTS_KEY = "shots"
SUBTITLES_KEY = "subtitles"
SCRIPT_KEY = "script"
CHAPTERS_KEY = "chapters"


@click.group(chain=True, invoke_without_command=True)
@click.option('-p', '--project', required=True,
              help="The movie title defining the folder structure DATA_DIR/\"movie_title\"/... and is used as an "
                   "identifier")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Adds verbose stdout")
@click.option('--version', is_flag=True, default=False)
@click.pass_context
def cli(ctx, project, verbose, version):
	"""FILM ANALYZER KIT"""
	project = Project(project)
	project.setup()

	ctx.obj[PROJECT_KEY] = project
	ctx.obj[LOGGER_KEY] = Logger(ctx.obj[PROJECT_KEY], verbose)
	ctx.obj[VERBOSE_KEY] = verbose

	if version:
		print("Version: {}".format(__version__))


@cli.command()
@click.option('-s', '--src', type=click.Path(), required=False,
              help="The path to the video source file")
@click.pass_context
def split(ctx, src):
	"""Splits movies into frames."""
	project = ctx.obj[PROJECT_KEY]
	dest = project.folder_path(Project.Folder.frames)

	splitter.split(src, dest)


@cli.command(name='subtitles')
@click.option('-p', '--path', type=click.Path(), required=False,
              help="The path to the subtitles file. If not specified it will look under "
                   "DATA_DIR/<projectId>/subtitles.srt")
@click.pass_context
def subtitles_parse(ctx, path):
	"""Parses subtitles."""
	project = ctx.obj[PROJECT_KEY]
	path = path if path else project.file_path(Project.File.original_subtitles)

	parsed_subtitles = subtitles_parser.parse_file(path)
	data = objects_as_dict(parsed_subtitles)
	data and project.write(data, Project.File.subtitles)

	ctx.obj[VERBOSE_KEY] and pprint(parsed_subtitles)
	ctx.obj[SUBTITLES_KEY] = parsed_subtitles


@cli.command()
@click.option('-u', '--url', required=False,
              help="The complete url to the imsdb script")
@click.pass_context
def screenplay(ctx, url):
	"""Parses movie scripts."""
	project = ctx.obj[PROJECT_KEY]

	if url:
		entities = script_parser.run(url)
		data = objects_as_dict(entities)
		data and project.write(data, Project.File.script)
	else:
		result = project.read(Project.File.script)
		entities = ScriptEntity.from_dicts(result)

	ctx.obj[VERBOSE_KEY] and pprint(entities)
	ctx.obj[SCRIPT_KEY] = entities


@cli.command()
@click.option('-s', '--subtitles-path', type=click.Path(), required=False,
              help="The path to the subtitles file. If not specified it will look under "
                   "DATA_DIR/<projectId>/subtitles.json")
@click.option('-ms', '--movie-script', type=click.Path(), required=False,
              help="The path to the parsed movie script file. If not specified it will look under "
                   "DATA_DIR/<projectId>/subtitles.json")
@click.option('-a', '--algorithm', type=click.Choice(CharactersAlgorithm.__members__), required=False,
              help="Specify the algorithm for alignment, you can use <dtw> ("
                   "Dynamic Time Warping) or <nw> Needlemann-Wunsch. Default value is is dtw.")
@click.option('-p', '--partial', type=int, required=False,
              help="Use only a fraction of the available data. If you want to use 1/4 of the data write -p 4. Mainly "
                   "handy for testing the algorithms.")
@click.pass_context
def characters(ctx, subtitles_path, movie_script, algorithm, partial):
	"""Merges movie scripts and subtitles."""
	project = ctx.obj[PROJECT_KEY]
	logger = ctx.obj[LOGGER_KEY]

	partial = 1 if partial is None else partial

	if subtitles_path:
		subtitles = Subtitle.from_dicts(path_utils.load_json(subtitles_path))
	elif SUBTITLES_KEY in ctx.obj:
		subtitles = ctx.obj[SUBTITLES_KEY]
	else:
		data = project.read(Project.File.subtitles)
		subtitles = Subtitle.from_dicts(data)

	if movie_script is not None:
		obj = path_utils.load_json(movie_script)
		speeches = ScriptEntity.from_dicts(obj)
	elif SCRIPT_KEY in ctx.obj:
		speeches = ctx.obj[SCRIPT_KEY]
	else:
		data = project.read(Project.File.script)
		data = script_parser.clean_script(data)  # remove when no longer required
		speeches = ScriptEntity.from_dicts(data)

	speeches = [speech for speech in speeches if speech.type == "speech"]

	if algorithm == CharactersAlgorithm.dtw.value:
		alignment = dtw_merger.run(speeches, subtitles, partial, logger, ctx.obj[VERBOSE_KEY])
	elif algorithm == CharactersAlgorithm.nw.value:
		alignment = needleman_wunsch.run(speeches, subtitles, partial, logger, ctx.obj[VERBOSE_KEY])
	else:
		alignment = dtw_merger.run(speeches, subtitles, partial, logger, ctx.obj[VERBOSE_KEY])

	merged_subtitles = alignment.subtitles
	ctx.obj[SUBTITLES_KEY] = merged_subtitles

	data = objects_as_dict(merged_subtitles)
	data and project.write(data, Project.File.merged_subtitles)

	logger.write()


@cli.command(name='shots')
@click.option("-t", "--threshold", type=float,
              help="Specify the threshold for which shots should be accepted.")
@click.option("-e", "--extraction-type", is_flag=False, type=click.Choice(ExtractionType.__members__),
              help="specify the extraction type, currently specified are <simpleHistoram, edge, "
                   "edgeim>.\nsimpleHistram works with color historams,\nedge uses canny edge detection.\n edgeim "
                   "uses canny edge detection with image registration.")
@click.option("-p", '--frames-path', type=click.Path(), required=False,
              help="Specify the frames path. Currenlty only works for shots processing, not for copying of keyframes "
                   "etc.")
@click.option("-f", "--from-file", is_flag=True,
              help="This option uses the locally stored shots.json. This way one can run color detection at some "
                   "other point in time. Very useful")
@click.option("-ls", "--local-sequence", is_flag=True,
              help="Use this if you like to run shot detection on pre calculated shot change ratio. The file is read "
                   "from DATA_DIR/<project>/shot-change-ratio.json")
@click.option("-c", "--color", type=int, required=False,
              help="Runs the color clustering to find the main colors. You can specify the number of clusters.")
@click.option("-k", "--keyframes", is_flag=True,
              help="Copies the keyframes of the detected shots into DATA_DIR/<project>/keyframes")
@click.option("-kt", "--keyframe-thumbnails", is_flag=True,
              help="Copies and scales down the keyframes of the detected shots into "
                   "DATA_DIR/<project>/keyframes_thumbnails")
@click.option("-km", "--keyframe-montage", is_flag=True,
              help="Generates a 10x... jpg grid which contains all keyframes.")
@click.option("-l", "--label", is_flag=True,
              help="Uses google vision api the retrieve labels to all keyframes. Don't forget to specify the path to "
                   "your google api credentials in GOOGLE_APPLICATION_CREDENTIALS.")
@click.option("-lt", "--limit", is_flag=False, nargs=2, required=False,
              help="Limits the considered frames for shot boundary detection by the given limit. e.g. --limit 100 "
                   "2000 if you like to only detect shots within the frames 100 to 2000.")
@click.option("-s", "--slices", is_flag=True, required=False,
              help="Creates spatio temporal slices from the frames within each shot. Is stored under "
                   "DATA_DIR/<project>/spatio_temporal_slices.")
@click.pass_context
def shots_parse(ctx, threshold, extraction_type, frames_path, from_file, local_sequence, color, keyframes,
                keyframe_thumbnails, keyframe_montage, label, limit, slices):
	"""Shot detection and feature extraction."""

	project = ctx.obj[PROJECT_KEY]

	if from_file:
		shots = Shot.from_dicts(project.read(Project.File.shots))
	else:
		if extraction_type == ExtractionType.edge.value or extraction_type == ExtractionType.edgeim.value:
			threshold = threshold if threshold is not None else 1000
			shots = edge_detection.edge_detect(project, threshold,
			                                   limit, extraction_type == ExtractionType.edgeim.value, local_sequence)
		else:
			threshold = threshold if threshold is not None else 0.4
			shots = shot_detection.detect(project, threshold, limit, local_sequence, extraction_type)

		ctx.obj[VERBOSE_KEY] and pprint(shots)

	if label:
		shots = label_detection.run(project, shots)
		pprint([shot.keyframe.labels for shot in shots])

	if keyframes:
		path = project.folder_path(project.Folder.keyframes)
		path_utils.delete_files_in_folder(path)
		path_utils.create_directory(path)

		shot_detection.copy_keyframes(project, shots)

	if keyframe_thumbnails:
		path = project.folder_path(project.Folder.keyframe_thumbnails)
		path_utils.delete_files_in_folder(path)

		shot_detection.keyframe_thumbnails(project)
		size = shot_detection.montage_keyframe_size(project)

	if slices:
		shot_detection.write_spatio_temporal_slices(project, shots)

	if color:
		shots = image_colors.run(project, shots, cluster_count=color)
		ctx.obj[VERBOSE_KEY] and pprint([s.keyframe.colors for s in shots])

	if keyframe_montage:
		shot_detection.keyframe_montage(project)
		size = shot_detection.montage_keyframe_size(project)

	if shots and len(shots):
		data = objects_as_dict(shots)
		data and project.write(data, Project.File.shots)

	ctx.obj[SHOTS_KEY] = shots


@cli.command(name='label')
@click.option('-p', '--path', type=click.Path(), required=True,
              help="The path to the image file")
@click.pass_context
def label_detect(ctx, path):
	"""Detect labels for a image file."""

	result = label_detection.detect(path)

	if ctx.obj["verbose"]:
		pprint(result)


@cli.command()
@click.option("-p", "--path", type=click.Path(),
              help="The path to the image file.")
@click.option("-c", "--count", type=int, default=4,
              help="The number of color clusters. Default is 4.")
@click.pass_context
def image_color(ctx, path, count):
	"""Color clustering for image file."""

	result = image_colors.colors_from_image(path, count)

	ctx.obj[VERBOSE_KEY] and pprint(result)


@cli.command()
@click.pass_context
@click.option("-h", "--host", help="The host url of the database.")
@click.option("-u", "--user", help="The username of the database.")
@click.option("-p", "--passwd", help="The password of the database.")
@click.option("-t", "--title", is_flag=True, default=False,
              help="Write title (project) data to database.")
@click.option("-s", "--shots", is_flag=True, default=False,
              help="Write shots data to database.")
@click.option("-sub", "--subtitles", is_flag=True, default=False,
              help="Write subtitle data to database.")
@click.option("-c", "--chapters", is_flag=True, default=False,
              help="Write chapters data to database.")
def persist(ctx, host, user, passwd, title, shots, subtitles, chapters):
	"""Persists data into a MongoDB."""

	project = ctx.obj[PROJECT_KEY]

	if host and user and passwd:
		db = Database(host, user, passwd)
	else:
		db = Database()

	if title:
		project.keyframe_size = shot_detection.keyframe_size(project)
		project.keyframe_montage_size = shot_detection.keyframe_thumbnail_size(project)
		db.update_title(project)

	if shots:
		shots = SHOTS_KEY in ctx.obj and ctx.obj[SHOTS_KEY]
		if not shots:
			p = project.file_path(Project.File.shots)
			if Project.file_exists(p):
				data = project.read(Project.File.shots)
				shots = Shot.from_dicts(data)

		shots and db.update_shots(project, shots)

	if subtitles:
		if SUBTITLES_KEY in ctx.obj:
			subtitles = ctx.obj[SUBTITLES_KEY]
		else:
			p = project.file_path(Project.File.merged_subtitles)
			if Project.file_exists(p):
				data = project.read(Project.File.merged_subtitles)
				subtitles = Subtitle.from_dicts(data)
			else:
				data = project.read(Project.File.subtitles)
				subtitles = Subtitle.from_dicts(data)

		subtitles and db.update_subtitles(project, subtitles)

	if chapters:
		if CHAPTERS_KEY in ctx.obj:
			chapters = ctx.obj[CHAPTERS_KEY]
		else:
			p = project.file_path(Project.File.chapters)
			if Project.file_exists(p):
				data = project.read(Project.File.chapters)
				chapters = Chapter.from_dicts(data)
			else:
				data = project.read(Project.File.chapters)
				chapters = Chapter.from_dicts(data)

		chapters and db.update_chapters(project, chapters)

	db.close()


@cli.command()
@click.option("-i", "--id", type=int,
              help="Load a specific ID.")
@click.option("-l", "--list", type=click.Path(),
              help="The data is separated into titles and the content of the title. This persists a list of all movies.")
@click.option("-s", "--start-index", type=int,
              help="Load all entities staring with the given index.")
@click.pass_context
def cinemetrics(ctx, id, list, start_index):
	"""Collect data from cinemetrics database."""

	if id:
		result = cinemetrics_ripper.rip_site(id, id + 1)
	elif start_index:
		result = cinemetrics_ripper.rip_site(start=start_index)
	elif list:
		result = cinemetrics_ripper.rip_movie_list(list)
	else:
		result = cinemetrics_ripper.run()

	ctx.obj[VERBOSE_KEY] and pprint(result)


@cli.command()
@click.option("-k", "--keyframes", is_flag=True, required=False,
              help="Uploads keyframes.")
@click.option("-kt", "--keyframe-thumbnails", is_flag=True, required=False,
              help="Uploads keyframe-thumbnails.")
@click.option("-f", "--frames", is_flag=True, required=False,
              help="Uploads all frames.")
@click.option("-s", "--slices", is_flag=True, required=False,
              help="Uploads spatio temporal slices.")
@click.pass_context
def upload(ctx, keyframes, keyframe_thumbnails, frames, slices):
	"""Uploads assets to a minio server."""
	project = ctx.obj[PROJECT_KEY]

	uploader = Uploader()

	if keyframes:
		uploader.upload_keyframes(project)

	if keyframe_thumbnails:
		uploader.upload_keyframe_thumbnails(project)

	if frames:
		uploader.upload_frames(project)

	if slices:
		uploader.upload_slices(project)

	ctx.obj[VERBOSE_KEY] and print("Uploaded")


@cli.command(name="chapters")
@click.option("-t", "--title", required=False, help="Specify the title of the movie if divergent to the project name. "
                                                    "Make sure you have CHAPTER_DB_API_KEY specified.")
@click.pass_context
def parse_chapters(ctx, title):
	"""Download the chapters for a movie."""

	project = ctx.obj[PROJECT_KEY]
	title = title if title else project.name
	chapters = chapters_parser.run(project, title)

	data = objects_as_dict(chapters)
	data and project.write(data, Project.File.chapters)

	ctx.obj[CHAPTERS_KEY] = chapters
	pprint(chapters)


@cli.command()
@click.option('-s', '--subtitles', is_flag=True, required=False)
@click.option('-ms', '--movie-script', is_flag=True, required=False)
@click.pass_context
def export(ctx, subtitles, movie_script):
	"""Export merge script and subtitles. (Testing)"""
	project = ctx.obj[PROJECT_KEY]

	if subtitles:
		data = project.read(Project.File.merged_subtitles)
		subtitles = Subtitle.from_dicts(data)
		export_subtitles(project, subtitles)

	if movie_script:
		data = project.read(Project.File.script)
		script = ScriptEntity.from_dicts(data)
		export_script(project, script)


def run():
	cli(obj={})


if __name__ == '__main__':
	run()
