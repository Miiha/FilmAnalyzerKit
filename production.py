# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
	readme = f.read()

with open('LICENSE') as f:
	license = f.read()

setup(
	name='analyzer',
	version='0.0.1',
	description='Scripts for video analysis',
	long_description=readme,
	author='Michael Kao',
	author_email='michael.kao@posteo.de',
	url='https://github.com/Miiha',
	license=license,
	packages=find_packages(exclude=('tests', 'docs')),
	install_requires=[
		'Click'
	],
	entry_points='''
		[console_scripts]
		analyzer=analyzer.core:run
	'''
)
