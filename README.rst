Chitty
======

Chat and more.

Backend: `Trio <https://github.com/python-trio/trio>`_ + `WebSockets <https://github.com/HyperionGray/trio-websocket>`_ + `Falcon <https://github.com/falconry/falcon>`_ + Redis `async <https://github.com/Tronic/redio>`_ + Redis `sync <https://github.com/andymccurdy/redis-py>`_

Mobile application: `Flutter <https://flutter.dev/>`_/Dart

Web application: `Preact <https://preactjs.com/>`_ PWA

Educational project so don't expect much, not being broken is not a top priority, stability is even not on a table.

This repo contains backend code.

Requirements
------------

The code requires at least Python 3.7.

On Python < 3.8 ``cached_property`` `decorator <https://docs.python.org/3.8/library/functools.html#functools.cached_property>`_ is polyfilled from `Werkzeug <https://werkzeug.palletsprojects.com/en/1.0.x/utils/#werkzeug.utils.cached_property>`_.
