Installation
============

Before you install, see the :doc:`prerequisites` guide to make sure you
have all required system packages installed.

Install with PIP
----------------

To install the girder distribution from the python package index, simply run ::

    pip install girder

This will install girder as a site package that can be run as specified in this
section: :ref:`run-girder`.

Install from Git Checkout
-------------------------

The first step, of course, is to checkout girder from the github repository like
so: ::

    git clone https://github.com/girder/girder.git

To run the server, you must install some external python package
dependencies: ::

    pip install -r requirements.txt

Before you can build the client-side code project, you must install the
`Grunt <http://gruntjs.com>`_ command line utilities: ::

    npm install -g grunt grunt-cli

Then cd into the root of the repository and run: ::

    npm install

Finally, when all node packages are installed, run: ::

    grunt init

Build
-----

To build the client side code, run the following command from within the
repository: ::

    grunt

Run this command any time you change a JavaScript or CSS file under
`__clients/web__.`

.. _run-girder:

Run
---

To run the server, first make sure the mongo daemon is running. To manually start it, run: ::

    mongod --setParameter textSearchEnabled=true &

Then, just run: ::

    python -m girder

Then open http://localhost:8080/ in your web browser, and you should see the application. ::
