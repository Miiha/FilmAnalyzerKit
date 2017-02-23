import os
import ffmpy


def split(src, dest):
	if not os.path.exists(dest):
		os.makedirs(dest)

	ff = ffmpy.FFmpeg(
		inputs={src: None},
		outputs={dest + "/%010d.jpg": '-f image2 -r 25 -vf scale=512:-1'}
	)

	ff.run(verbose=True)

