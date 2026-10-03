Workflow API
============

The workflow layer contains the domain logic that powers RosettaX. These modules are the main internal API for calibration generation, parameter normalization, file upload, peak selection, and result export.


Upload workflow
---------------

.. automodule:: RosettaX.workflow.upload.models
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.upload.services
    :members:
    :show-inheritance:


Parameter workflow
------------------

These modules normalize scattering model inputs and the editable calibration standard table.

.. automodule:: RosettaX.workflow.parameters.table
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.parameters.model
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.parameters.refractive_index
    :members:
    :show-inheritance:


Calibration workflow
--------------------

The calibration modules define optical parameter models and the fitted relationships used for fluorescence and scattering calibration.

.. automodule:: RosettaX.workflow.scattering.mie_relation
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.scattering.calibration_services
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.scattering.model
    :members:
    :show-inheritance:


Apply-calibration workflow
--------------------------

.. automodule:: RosettaX.workflow.apply_calibration.services
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.apply_calibration.fluorescence
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.apply_calibration.scattering
    :members:
    :show-inheritance:


Peak workflow
-------------

Peak detection and annotation are distributed across adapters, registry helpers, plotting helpers, and lower-level scripts.

.. automodule:: RosettaX.workflow.peak.adapters.base
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.peak.core.graphing
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.peak.core.detectors
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.peak.registry
    :members:
    :show-inheritance:


Save and export workflow
------------------------

.. automodule:: RosettaX.workflow.save.services
    :members:
    :show-inheritance:

.. automodule:: RosettaX.workflow.save.models
    :members:
    :show-inheritance: