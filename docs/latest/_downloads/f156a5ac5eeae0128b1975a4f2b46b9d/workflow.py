"""
Workflow example
================

Just a dummy example to illustrate the workflow examples gallery.

"""
from RosettaX.reader import FCSFile
from RosettaX.directories import fcs_data
import matplotlib.pyplot as plt

file_dir = fcs_data / "sample.fcs"

print(file_dir)

data = FCSFile(fcs_data / "sample.fcs")

data.read_all_data()

figure, ax = plt.subplots()
ax.plot(data.data["FSC-A"], data.data["SSC-A"], ".")
ax.set_xlabel("FSC-A")
ax.set_ylabel("SSC-A")
plt.show()

