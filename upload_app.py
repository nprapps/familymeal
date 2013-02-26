#!/usr/bin/env python

import datetime
import os
import re
import logging

import boto
from boto.s3.key import Key

from flask import Flask, redirect
from tumblpy import Tumblpy
from tumblpy import TumblpyRateLimitError, TumblpyAuthError
from werkzeug import secure_filename

import app_config

app = Flask(app_config.PROJECT_NAME)
app.config['PROPAGATE_EXCEPTIONS'] = True

@app.route('/family-meal/', methods=['POST'])
def _post_to_tumblr():

    """
    Handles the POST to Tumblr.
    """
    def clean(string):
        """
        Formats a string all pretty.
        """
        return string.replace('-', ' ').replace("id ", "I'd ").replace("didnt", "didn't").replace('i ', 'I ')

    # Request is a global. Import it down here where we need it.
    from flask import request

    def strip_html(value):
        """
        Strips HTML from a string.
        """
        return re.compile(r'</?\S([^=]*=(\s*"[^"]*"|\s*\'[^\']*\'|\S*)|[^>])*?>', re.IGNORECASE).sub('', value)

    def strip_breaks(value):
        """
        Converts newlines, returns and other breaks to <br/>.
        """
        value = re.sub(r'\r\n|\r|\n', '\n', value)
        return value.replace('\n', '<br />')

    caption = u"""
        <p class='message'>%s</p>
        <p class='signature-name'>Initialed,<br/>%s from %s</p>
        <p class='footnote'>Dinner is hard. We want to know what's on your family's table, and why.
        Share yours at <a href='http://%s/'>NPR's Dinnertime Confessional</a>.</p>
    """ % (
        strip_breaks(strip_html(request.form['message'])),
        strip_html(request.form['signed_name']),
        strip_html(request.form['location']),
        app_config.TUMBLR_URL
    )

    filename = secure_filename(request.files['image'].filename.replace(' ', '-'))

    for s3_bucket in app_config.S3_BUCKETS:
        conn = boto.connect_s3()
        bucket = conn.get_bucket(s3_bucket)
        headers = {
            'Content-Type': request.files['image'].content_type,
            'Cache-Control': 'public, max-age=31536000'
        }
        policy = 'public-read'

        k = Key(bucket)
        k.key = '%s/tmp/%s' % (app_config.DEPLOYED_NAME, filename)
        k.set_contents_from_file(
            request.files['image'],stream,
            headers=headers,
            policy=policy)

    t = Tumblpy(
        app_key=app_config.TUMBLR_KEY,
        app_secret=os.environ['TUMBLR_APP_SECRET'],
        oauth_token=os.environ['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=os.environ['TUMBLR_OAUTH_TOKEN_SECRET'])

    s3_path = 'http://%s.s3.amazonaws.com/%s/tmp/%s' % (
            app_config.S3_BUCKETS[0],
            app_config.DEPLOYED_NAME,
            filename
        )

    params = {
        'type': 'photo',
        'caption': caption,
        'tags': u"food,dinner,plate,confession,crunchtime,npr",
        'source': s3_path
    }

    tumblr_dict = {}
    tumblr_dict['timestamp'] = datetime.datetime.now()

    logger = logging.getLogger('tumblr')
    file_handler = logging.FileHandler('/var/log/familymeal.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    try:
        tumblr_post = t.post('post', blog_url=app_config.TUMBLR_URL, params=params)
        tumblr_dict['tumblr_id'] = tumblr_post['id']
        tumblr_dict['tumblr_url'] = u"http://%s/%s" % (app_config.TUMBLR_URL, tumblr_post['id'])
        tumblr_dict['result'] = {'code': 200, 'message': 'success'}
        logger.info('200 %s' % tumblr_dict['tumblr_url'])

        return redirect(u"http://%s/%s#posts" % (app_config.TUMBLR_URL, tumblr_post['id']), code=301)

    except TumblpyAuthError:
        tumblr_dict['result'] = {'code': 401, 'message': 'Failed: Not authenticated.'}
        logger.error('401 Not Authenticated')
        return 'NOT AUTHENTICATED'

    except TumblpyRateLimitError:
        tumblr_dict['result'] = {'code': 403, 'message': 'Failed: Rate limited.'}
        logger.error('403 Rate Limited')
        return 'RATE LIMITED'

    except:
        tumblr_dict['result'] = {'code': 400, 'message': 'Failed: Unknown.'}
        logger.error('400 Unknown')
        return 'UNKNOWN FAILURE'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app_config.DEBUG)
