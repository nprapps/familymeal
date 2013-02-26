#!/usr/bin/env python

import datetime
import os
import re
import unicodedata

import boto
from boto.s3.key import Key

from flask import Flask, redirect
from tumblpy import Tumblpy
from tumblpy import TumblpyError, TumblpyRateLimitError, TumblpyAuthError

import app_config

app = Flask(app_config.PROJECT_NAME)
app.config['PROPAGATE_EXCEPTIONS'] = True


@app.route('/family-meal/', methods=['POST'])
def _post_to_tumblr():

    def slugify(value):
        """
        Converts to lowercase, removes non-word characters (alphanumerics and
        underscores) and converts spaces to hyphens. Also strips leading and
        trailing whitespace.
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub('[^\w\s-]', '', value).strip().lower()
        return re.sub('[-\s]+', '-', value)

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

    t = Tumblpy(
        app_key=app_config.TUMBLR_KEY,
        app_secret=os.environ['TUMBLR_APP_SECRET'],
        oauth_token=os.environ['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=os.environ['TUMBLR_OAUTH_TOKEN_SECRET'])

    filename = slugify(request.files['image'].filename)

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
        k.set_contents_from_string(
            request.files['image'].getvalue(),
            headers=headers,
            policy=policy)

    params = {
        'type': 'photo',
        'caption': caption,
        'tags': u"food,dinner,plate,confession,crunchtime,npr",
        'source': 'http://%s.s3.amazonaws.com/%s/tmp/%s' % (
            app_config.S3_BUCKETS[0],
            app_config.DEPLOYED_NAME,
            filename
        )
    }

    tumblr_post = t.post('post', blog_url=app_config.TUMBLR_URL, params=params)
    return redirect(u"http://%s/%s#posts" % (app_config.TUMBLR_URL, tumblr_post['id']), code=301)

    # tumblr_dict = {}
    # tumblr_dict['timestamp'] = datetime.datetime.now()

    # try:
    #     tumblr_post = t.post('post', blog_url="staging-family-meal.tumblr.com", params=params)
    #     tumblr_dict['tumblr_id'] = tumblr_post['id']
    #     tumblr_dict['tumblr_url'] = u"http://%s/%s" % (app_config.TUMBLR_URL, tumblr_post['id'])
    #     tumblr_dict['result'] = {'code': 200, 'message': 'success'}

    #     return redirect(u"http://%s/%s#posts" % (app_config.TUMBLR_URL, tumblr_post['id']), code=301)
    # except TumblpyAuthError:
    #     tumblr_dict['result'] = {'code': 401, 'message': 'Failed: Not authenticated.'}
    #     return 'NOT AUTHENTICATED'

    # except TumblpyRateLimitError:
    #     tumblr_dict['result'] = {'code': 403, 'message': 'Failed: Rate limited.'}
    #     return 'RATE LIMITED'

    # except:
    #     tumblr_dict['result'] = {'code': 400, 'message': 'Failed: Unknown.'}
    #     return 'UNKNOWN FAILURE'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app_config.DEBUG)
