
from flask import Flask
from flask import request,send_file,redirect,render_template, abort

import os
import random

# import db_handler
# import utils 
import wormnest.db_handler as db_handler
import wormnest.utils as utils

'''
To run the App:
FLASK_APP=wormnest/__main__.py python -m flask run --host=127.0.0.1 --port=8080
'''
app = Flask(__name__)

SRV_DIR = "test_directory/"
ALIAS_DIGITS_MIN = 8
ALIAS_DIGITS_MAX = 8
LISTING_URL_DIR = 'listing'
MANAGE_URL_DIR = 'manage'
REDIRECT_URL = 'https://amazon.com'
DEFAULT_FILENAME = 'ClientDesktopApp'
USE_ORIGINAL_EXTENSION = True


def redirect_away():
	return redirect(REDIRECT_URL, code=302)

def abort_404():
	return abort(404)

default_miss = abort_404
on_expired = abort_404
# default_miss = redirect_away
on_expired = redirect_away


def get_random_alias(length=None):
	assert ALIAS_DIGITS_MIN <= ALIAS_DIGITS_MAX
	if length == None:
		length = random.randint(ALIAS_DIGITS_MIN, ALIAS_DIGITS_MAX)
	return utils.randomword(length)


@app.route(
	'/%s/%s/' % (MANAGE_URL_DIR, LISTING_URL_DIR),
	defaults={'req_path': ''}
	)
@app.route('/%s/%s/<path:req_path>' %
 (MANAGE_URL_DIR, LISTING_URL_DIR),)
def dir_listing(req_path):
	'''
	Found here:
https://stackoverflow.com/questions/23718236/python-flask-browsing-through-directory-with-files
	'''
	BASE_DIR = SRV_DIR

	# Joining the base and the requested path
	abs_path = os.path.join(BASE_DIR, req_path)

	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		return abort(404)

	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		return send_file(abs_path)

	# Show directory contents
	files = os.listdir(abs_path)
	return render_template('file.html', files=files)


@app.route('/<url_alias>')
def resolve_url(url_alias):
	try:
		resolved_url = db_handler.get_path(url_alias)
	except KeyError:
		return default_miss()
	except utils.LinkExpired:
		return on_expired()

	return send_file(
		resolved_url.path,
		as_attachment = True,
		attachment_filename = resolved_url.attachment,
		)


@app.route('/%s/add' % MANAGE_URL_DIR)
def add_url():
	path = request.args.get("path")
	expires = request.args.get("clicks")
	alias = request.args.get("alias")
	attach_name = request.args.get("filename")

	try:
		original_filename = path.split('/')[-1]
		original_extension = original_filename.split('.')[-1]
	except Exception as e:
		return render_template(
			'custom_error.html', 
			error_msg=e
			)

	if original_filename == original_extension:
		# If they are the same, there is no extension
		original_extension = ''
	else:
		original_extension = '.' + original_extension

	if not attach_name:

		if not DEFAULT_FILENAME:
			# The filename is the path's filename
			attach_name = original_filename
		else:
			attach_name = DEFAULT_FILENAME
			if USE_ORIGINAL_EXTENSION:
				attach_name += original_extension


	if not os.path.isfile(path):
		return render_template(
			'custom_error.html', 
			error_msg="The path '{}' is NOT a file".format(path)
			)

	if not alias:
		alias = get_random_alias()

	try:
		if expires is not None: 
			int(expires)
	except:
		return render_template(
			'custom_error.html', 
			error_msg="Parameter 'clicks' must be positive Integer"
			)
	try:
		db_handler.add_url(path, alias, expires, attach_name)
	except Exception as e:
		print (e)
		err =  "Error adding alias '{}'' for path '{}'".format(alias, path)
		return render_template(
			'custom_error.html', 
			error_msg=err
			)
	full_link = request.url_root + alias
	return render_template(
			'added_alias.html', 
			alias=alias,
			path=path,
			link=full_link
			)


@app.route('/%s/show' % MANAGE_URL_DIR)
def show_all(path=None):
	entries = db_handler.get_all(path)
	return render_template(
				'show.html',
				entries = entries
				)


def main(*args, **kwargs):

	import sys
	print (sys.argv)
	app.run(
		host=os.getenv('IP', '127.0.0.1'), 
		port=int(os.getenv('PORT',8080)),
		debug=True
		)

if __name__=="__main__":
	main()