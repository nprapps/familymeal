#!/usr/bin/env python

import os
import json
import re

import boto
from boto.s3.key import Key

from flask import Flask, redirect, Request
from tumblpy import Tumblpy

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

    caption = u"%s %s %s %s %s" % (
        request.form['voted'],
        clean(request.form['voted']),
        strip_breaks(strip_html(request.form['message'])),
        strip_html(request.form['signed_name']),
        strip_html(request.form['location'])
    )

    t = Tumblpy(
        app_key=app_config.TUMBLR_KEY,
        app_secret=os.environ['TUMBLR_APP_SECRET'],
        oauth_token=os.environ['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=os.environ['TUMBLR_OAUTH_TOKEN_SECRET'])

    for s3_bucket in app_config.S3_BUCKETS:
        conn = boto.connect_s3()
        bucket = conn.get_bucket(s3_bucket)
        headers = {
            'Content-Type': request.files['image'].content_type,
            'Cache-Control': 'public, max-age=31536000'
        }
        policy = 'public-read'

        k = Key(bucket)
        k.key = '%s/tmp/%s' % (app_config.DEPLOYED_NAME, request.files['image'].filename)
        k.set_contents_from_string(
            request.files['image'].getvalue(),
            headers=headers,
            policy=policy)

    params = {
        'type': 'photo',
        'caption': caption,
        'tags': u"%s" % request.form['voted'].replace('-', ''),
        'source': 'http://%s.s3.amazonaws.com/%s/tmp/%s' % (app_config.S3_BUCKETS[0], app_config.DEPLOYED_NAME, request.files['image'].filename)
    }

    print params

    tumblr_post = t.post('post', blog_url="staging-family-meal.tumblr.com", params=params)

    return redirect(u"http://%s/%s#posts" % (app_config.TUMBLR_URL, tumblr_post['id']), code=301)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app_config.DEBUG)
