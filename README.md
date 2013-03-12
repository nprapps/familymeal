Dinnertime Confessional
=========================

* [What's in here?](#whats-in-here)
* [Install requirements](#install-requirements)
* [Project secrets](#project-secrets)
* [Run the project locally](#run-the-project-locally)
* [Run javascript tests](#run-javascript-tests)
* [Compile static assets](#compile-static-assets)
* [Test the rendered app](#test-the-rendered-app)
* [Deploy to S3](#deploy-to-s3)
* [Deploy to EC2](#deploy-to-ec2)

What's in here?
---------------

The project contains the following folders and important files:

* ``data`` -- Data files, such as those used to generate HTML
* ``etc`` -- Miscellaneous scripts and metadata for project bootstrapping.
* ``jst`` -- Javascript ([Underscore.js](http://documentcloud.github.com/underscore/#template)) templates
* ``less`` -- [LESS](http://lesscss.org/) files, will be compiled to CSS and concatenated for deployment
* ``templates`` -- HTML ([Jinja2](http://jinja.pocoo.org/docs/)) templates, to be compiled locally
* ``www`` -- Static and compiled assets to be deployed (a.k.a. "the output")
* ``www/test`` -- Javascript tests and supporting files
* ``app.py`` -- A [Flask](http://flask.pocoo.org/) app for rendering the project locally.
* ``upload_app.py`` -- A Flask](http://flask.pocoo.org/) app for writing uploaded data to Tumblr via the V2 API.
* ``app_config.py`` -- Global project configuration for scripts, deployment, etc.
* ``fabfile.py`` -- [Fabric](http://docs.fabfile.org/en/latest/) commands automating setup and deployment


Install requirements
--------------------

Node.js is required for the static asset pipeline. If you don't already have it, get it like this:

```
brew install node
curl https://npmjs.org/install.sh | sh
```

Then install the project requirements:

```
cd familymeal
npm install less universal-jst
mkvirtualenv familymeal
pip install -r requirements.txt
```

Project secrets
---------------

Project secrets should **never** be stored in ``app_config.py`` or anywhere else in the repository. They will be leaked to the client if you do. Instead, always store passwords, keys, etc. in environment variables and document that they are needed here in the README.

In order to use this app, you will need


Run the project locally
-----------------------

A flask app is used to run the project locally. It will automatically recompile templates and assets on demand.

```
workon familymeal
python app.py
```

In a second terminal, run the local version of the Tumblr upload app.

```
workon familymeal
python upload_app.py
```

Visit [localhost:8000](http://localhost:8000) in your browser to see the form. The form will POST data to [localhost:8001](http://localhost:8001), and then upload_app.py will push the photo and some text to Tumblr.

Run Javascript tests
--------------------

With the project running, visit [localhost:8000/test/SpecRunner.html](http://localhost:8000/test/SpecRunner.html).

Compile static assets
---------------------

Compile LESS to CSS, compile javascript templates to Javascript and minify all assets:

```
workon familymeal
fab render
```

(This is done automatically whenever you deploy to S3.)

Test the rendered app
---------------------

If you want to test the app once you've rendered it out, just use the Python webserver:

```
cd www
python -m SimpleHTTPServer
```

Deploy to S3
------------

```
fab staging master deploy
```

Deploy to EC2
-------------

The current configuration is for running cron jobs only. Web server configuration is not included.

* In ``fabfile.py`` set ``env.deploy_to_servers`` to ``True``.
* Run ``fab staging master setup`` to configure the server.
* Run ``fab staging master deploy`` to deploy the app.
