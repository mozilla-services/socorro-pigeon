Pigeon
======

Pigeon is an AWS Lambda function that reacts to S3 ObjectCreated:Put events
looking for new raw crashes in the S3 bucket. For each raw crash, it looks
at the accept/defer annotation and sends the crash id to configured RabbitMQ
queues for accepted crashes.

The accept/defer annotation is the 7th-to-last character of the key::

  v2/raw_crash/000/20180313/00007bd0-2d1c-4865-af09-80bc00180313
                                                         ^

* ``0`` - defer
* ``1`` - accept
* any other values are junk and ignored


Quickstart
==========

1. `Install docker 18.00.0+ <https://docs.docker.com/install/>`_ and
   `install docker-compose 1.20.0+ <https://docs.docker.com/compose/install/>`_
   on your machine.

   You'll also need git, make, Python (2 or 3), and bash.

2. Clone the repo:

   .. code-block:: shell

      $ git clone https://github.com/mozilla-services/socorro-pigeon

3. Download and build Pigeon Docker images and Python libraries:

   .. code-block:: shell

      $ make build

   Anytime you change requirements files or code, you'll need to run
   ``make build`` again.

4. Run tests:

   .. code-block:: shell

      $ make test

   You can also get a shell and run them manually:

   .. code-block:: shell

      $ make testshell
      app@4205495cfa57:/app$ pytest
      <test output>

   Using the shell lets you run and debug tests more easily.

5. Run the integration test:

   .. code-block:: shell

      $ ./bin/integration_test.sh
      <test output>

6. Invoke the function with a sample S3 ObjectCreated:Put event:

   .. code-block:: shell

      $ ./bin/generate_event.py --key v2/raw_crash/000/20180313/00007bd0-2d1c-4865-af09-80bc00180313 > event.json
      $ cat event.json | ./bin/run_invoke.sh
      <invoke output>

   Then consume and print the contents of the RabbitMQ queue:

   .. code-block:: shell

      $ docker-compose run test bin/consume_queue.py


Caveats of this setup
=====================

1. Because ``pigeon.py`` is copied into ``build/`` and that version is tested
   and invoked, if you edit ``pigeon.py``, you need to run ``make build``
   again. This is kind of annoying when making changes.

2. Packaging the ``.zip`` file and deploying it are not handled by the
   scaffolding in this repo.


Scripts
=======

All scripts are in the ``bin/`` directory.

* ``consume_queue.py``: Used in dev environment to consume and print out
  everything in the RabbitMQ queue.

* ``generate_event.py``: Generates a sample AWS S3 event.

* ``run_invoke.sh``: Invokes the pigeon function in a AWS Lambda Python
  3.6 runtime environment.

* ``integration_test.sh``: Runs an integration test.

* ``run_circle.sh``: The script that Circle CI runs.


Configuration
=============

All configuration for Pigeon relates to the RabbitMQ service it needs to connect
to.

Required environment variables:

``PIGEON_HOST``
    The RabbitMQ host.

``PIGEON_PORT``
    The RabbitMQ host port.

``PIGEON_VIRTUAL_HOST``
    The RabbitMQ virtual host.

``PIGEON_USER``
    The RabbitMQ user.

``PIGEON_PASSWORD``
    The RabbitMQ user password.

``PIGEON_QUEUE``
    The RabbitMQ queue to use.

    Queues are comma separated.

    Each queue can specify a throttle in the form of ``THROTTLE:QUEUE`` where
    the throttle is an integer between 0 (no crashes are published (which is
    silly)) and 100 (all crashes are published).

    Example values:

    * ``normal``: publish to a single "normal" queue
    * ``normal,submitter``: publish to "normal" and "submitter" queues
    * ``normal,15:submitter``: publish 100% of things to "normal" and 15% of things to "submitter" queues
    * ``normal,submitter,jimbob``: publish to "normal", "submitter", and "jimbob" queues

``PIGEON_AWS_REGION``
    The AWS region to use.

``PIGEON_ENV``
    Optional. The name of the environment. This should be all letters with no
    punctuation. This should be unique between environments. For example,
    "prod", "stage", and "newstage".


If any of these are required, but missing from the environment, Pigeon will
raise a ``KeyError``.
