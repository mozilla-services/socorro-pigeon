Pigeon
======

AWS Lambda function that reacts to S3 object save events and sends crash ids to
a configured RabbitMQ queue.


Quickstart
==========

1. Clone the repo:

   .. code-block:: shell

      $ git clone https://github.com/mozilla/socorro-pigeon

2. `Install docker 1.10.0+ <https://docs.docker.com/engine/installation/>`_ and
   `install docker-compose 1.6.0+ <https://docs.docker.com/compose/install/>`_
   on your machine

3. Download and build Pigeon docker containers:

   .. code-block:: shell

      $ make build

   Anytime you want to update the containers, you can run ``make build``.

4. Run tests:

   .. code-block:: shell

      $ make test


   You can also get a shell and run them manually:

   .. code-block:: shell

      $ make shell
      app@4205495cfa57:/app$ py.test
      <test output>


   This lets you change arguments and run specific tests.
