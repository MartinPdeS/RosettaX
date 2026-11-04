Utilities API
=============

The utility layer contains reusable helpers for runtime configuration, file parsing, FCS metadata handling, and common transformations.


Runtime configuration
---------------------

``RosettaX.utils.runtime_config`` is the canonical configuration container used across callbacks and workflow services.

.. automodule:: RosettaX.utils.runtime_config
    :members:
    :show-inheritance:


FCS file handling
-----------------

These modules are responsible for loading raw FCS content and exposing metadata in a workflow-friendly form.

.. automodule:: RosettaX.utils.reader
    :members:
    :show-inheritance:

.. automodule:: RosettaX.utils.fcs_metadata
    :members:
    :show-inheritance:


Parsing and serialization helpers
---------------------------------

.. automodule:: RosettaX.utils.parser
    :members:
    :show-inheritance:

.. automodule:: RosettaX.utils.io
    :members:
    :show-inheritance:

.. automodule:: RosettaX.utils.service
    :members:
    :show-inheritance:

.. automodule:: RosettaX.utils.casting
    :members:
    :show-inheritance:


Related helper modules
----------------------

The following modules contain UI styling or validation support used by higher-level components:

.. automodule:: RosettaX.utils.checks
    :members:
    :show-inheritance:

.. automodule:: RosettaX.utils.styling
    :members:
    :show-inheritance: