"""
Workflow example
================

Just a dummy example to illustrate the workflow examples gallery.

"""
from RosettaX.reader import FCSFile
from RosettaX.directories import fcs_data


file_dir = fcs_data / "sample.fcs"

print(file_dir)

data = FCSFile(fcs_data / "sample.fcs")

data.read_all_data()
print(data.data)

