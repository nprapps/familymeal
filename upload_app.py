#!/usr/bin/env python

import datetime
import logging
import os
import re
import time

from flask import Flask, redirect
from tumblpy import Tumblpy
from tumblpy import TumblpyError
from werkzeug import secure_filename

import app_config

app = Flask(app_config.PROJECT_NAME)
app.config['PROPAGATE_EXCEPTIONS'] = True

logger = logging.getLogger('tumblr')
file_handler = logging.FileHandler('/var/log/familymeal.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


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

# try:
    caption = """
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

    file_path = '/upload/%s/%s_%s' % (
        'family-meal',
        time.mktime(datetime.datetime.now().timetuple()),
        secure_filename(request.files['image'].filename.replace(' ', '-'))
    )

    with open('/tmp%s' % file_path, 'w') as f:
        f.write(request.files['image'].read())

    params = {
        'type': 'photo',
        'caption': caption,
        'tags': "food,dinner,plate,confession,crunchtime,npr",
        'source': 'http://%s/%s' % (app_config.STAGING_SERVERS[0], file_path)
    }

    # try:
    tumblr_post = t.post('post', blog_url=app_config.TUMBLR_URL, params=params)
    tumblr_url = u"http://%s/%s" % (app_config.TUMBLR_URL, tumblr_post['id'])
    # logger.info('200 %s' % tumblr_url)

    return redirect('%s#posts' % tumblr_url, code=301)

        # except TumblpyError, e:
        #     logger.error('%s %s' % (e.error_code, e.msg))
        #     return 'TUMBLR ERROR'

    # except Exception, e:
    #     logger.error('%s' % e)
    #     return 'ERROR'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app_config.DEBUG)
