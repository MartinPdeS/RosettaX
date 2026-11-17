"""Peak process definitions and their numerical implementations.

The registry discovers process classes defined in individual public modules.
Registered names remain stable because saved workflow state uses them.

Rosetta modes share detection in ``rosetta_mix``, settings and stage results
in ``rosetta_mix_models``, sizing in ``rosetta_mix_sizing``, and diagnostics
in ``rosetta_mix_diagnostics``. Gaussian and mixture fitters remain separate.
The ``rosetta_mix_v1`` module defines the editable diagnostics mode and retains
legacy sizing imports for callers; shared code imports its owning module.

Histogram and K-means processes share numerical operations in ``_numerics``.
"""
