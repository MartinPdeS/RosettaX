Supported cytometers
====================

The Rosetta cross-device validation suite includes recordings from these
cytometers. Some recordings verify warning behavior when available peaks
cannot support automatic sizing.

.. include:: ../../../README.rst
   :start-after: .. supported-cytometers-start
   :end-before: .. supported-cytometers-end

Detector geometry
-----------------

These previews show the geometry of the packaged scattering presets.
The FACSLyric and FACSymphony A1 figures show assumed optical geometry.
Other supported models may have channel auto-selection without a dedicated
geometry preview.

Apogee A50-Micro, A60-Micro and MicroPLUS each have Standard and Modified
layouts. An FCS MALS channel identifies the Modified layout. For a partial
export, select the installed layout in the cytometer selector.

The workbook specifies a shared 405 nm objective with NA 1.3 at 28.8 degrees.
The model places a straight mirror boundary at 12.5 degrees in the objective
tilt plane, the midpoint of the overlapping SALS and LALS limits. Standard
SALS collects below that boundary and LALS collects the remaining clear
aperture. Modified LALS ends at 60 degrees (midpoint of 50–70 degrees) and
MALS collects above it, including the boundary. The rectangular bar spans the
aperture and uses a nominal width of 9% of its diameter (range 4–14%).

.. container:: rx-system-grid

   .. container:: rx-system-card

      **Apogee A60-Micro Standard**

      .. image:: /_static/detector_figures/apogee_a60_forward.png
         :alt: Apogee A60-Micro Standard SALS detector geometry.
         :class: rx-system-image

      .. image:: /_static/detector_figures/apogee_a60_side.png
         :alt: Apogee A60-Micro Standard LALS detector geometry.
         :class: rx-system-image

   .. container:: rx-system-card

      **BD FACSLyric**

      .. image:: /_static/detector_figures/bd_facslyric_fsc.png
         :alt: BD FACSLyric FSC detector geometry.
         :class: rx-system-image

      .. image:: /_static/detector_figures/bd_facslyric_ssc.png
         :alt: BD FACSLyric SSC detector geometry.
         :class: rx-system-image

   .. container:: rx-system-card

      **BD FACSymphony A1**

      .. image:: /_static/detector_figures/bd_facsymphony_a1_ssc.png
         :alt: BD FACSymphony A1 SSC detector geometry.
         :class: rx-system-image

   .. container:: rx-system-card

      **Cytek Aurora**

      .. image:: /_static/detector_figures/cytek_aurora_fsc.png
         :alt: Cytek Aurora FSC detector geometry.
         :class: rx-system-image

      .. image:: /_static/detector_figures/cytek_aurora_ssc.png
         :alt: Cytek Aurora SSC detector geometry.
         :class: rx-system-image
