"""
Workflow example
================

Just a dummy example to illustrate the workflow examples gallery.

"""
import matplotlib.pyplot as plt
from RosettaX.utils.reader import FCSFile
from RosettaX.directories import fcs_data
from RosettaX.utils.clusterings import SigmaThresholdHDBSCAN

file_dir = fcs_data / "sample_0.fcs"

x = "488Org(Peak)"
y = "405LALS(Peak)"


with FCSFile(file_dir, writable=False) as fcs_file:
    x_values = fcs_file.column_copy(x, dtype=float, n=100_000)
    y_values = fcs_file.column_copy(y, dtype=float, n=100_000)

figure, ax = plt.subplots(figsize=(6, 6))
ax.scatter(x_values, y_values)
ax.set_xlabel(x)
ax.set_ylabel(y)
plt.tight_layout()
plt.show()


model = SigmaThresholdHDBSCAN()

labels, means, modes, clean_data, mask = model.fit(
    x=x_values,
    n_clusters=3,          # ask for two merged clusters
    threshold_x=4000,      # tweak according to data
    min_cluster_size=100,  # you can tweak; start not too high
    debug=True,
)
