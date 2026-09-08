r"""
Fit a scattering instrument response
====================================

Scattering calibration first models the optical coupling of each calibration
standard using the selected Mie and detector settings. RosettaX then fits the
instrument response from measured peak values to those modeled couplings.

This compact example focuses on that final fitting step. It uses a
zero-intercept response, the default behaviour in RosettaX:

.. math::

   \mathrm{coupling} = m\,\mathrm{measured\ peak}.

In an actual workflow, do not invent the coupling values. Let RosettaX compute
them from the selected particle, medium, wavelength, and detector geometry.
"""

import matplotlib.pyplot as plt
import numpy as np

from RosettaX.workflow.scattering.calibration_services import (
    fit_linear_instrument_response,
)


# Illustrative table: the x values would normally be approved measured peaks,
# while the y values would be generated from the workflow's Mie model.
measured_peak_au = np.array([1_100.0, 2_600.0, 5_100.0, 10_800.0])
modeled_coupling = np.array([0.024, 0.058, 0.115, 0.239])

response = fit_linear_instrument_response(
    measured_peak_values=measured_peak_au,
    theoretical_coupling_values=modeled_coupling,
    measured_channel="SSC-A (illustrative)",
    force_zero_intercept=True,
)

print(f"Slope: {response.slope:.6g}")
print(f"Intercept: {response.intercept:.6g}")
print(f"R²: {response.r_squared:.4f}")

peak_range = np.linspace(0.0, measured_peak_au.max() * 1.1, 200)
predicted_coupling = response.measured_to_coupling(peak_range)

figure, axis = plt.subplots(figsize=(7, 4.5))
axis.scatter(
    measured_peak_au,
    modeled_coupling,
    color="#2d6df6",
    label="Illustrative calibration standards",
    zorder=3,
)
axis.plot(
    peak_range,
    predicted_coupling,
    color="#16a9ba",
    label=f"Zero-intercept response (R² = {response.r_squared:.4f})",
)
axis.set(
    xlabel="Measured peak intensity [a.u.]",
    ylabel="Modeled optical coupling [a.u.]",
    title="Illustrative scattering instrument response",
)
axis.grid(True, alpha=0.25)
axis.legend()
figure.tight_layout()
