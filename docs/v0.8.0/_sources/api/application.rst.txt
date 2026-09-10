Application API
===============

The application layer creates the Dash app, registers the page system, and connects shared callbacks and routes.


Main entry point
----------------

``RosettaX.application.main`` defines the main application object used to start the local web interface.

.. automodule:: RosettaX.application.main
    :members:
    :undoc-members:
    :show-inheritance:


Supporting registration modules
-------------------------------

The following modules are primarily used during application bootstrap:

.. automodule:: RosettaX.application.pages
    :members:
    :show-inheritance:

.. automodule:: RosettaX.application.routes
    :members:
    :show-inheritance:

.. automodule:: RosettaX.application.callbacks
    :members:
    :show-inheritance:

.. automodule:: RosettaX.application.layout
    :members:
    :show-inheritance:


Usage notes
-----------

- Use ``RosettaXApplication`` when launching RosettaX programmatically.
- Keep page-specific behavior inside the corresponding modules in ``RosettaX.pages``.
- Keep domain logic in ``RosettaX.workflow`` rather than in application bootstrap code.