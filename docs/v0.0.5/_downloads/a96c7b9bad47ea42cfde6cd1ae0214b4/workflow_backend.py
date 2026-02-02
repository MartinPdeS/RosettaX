"""
Workflow example
================

Just a dummy example to illustrate the workflow examples gallery.

"""
from RosettaX.backend import BackEnd
from RosettaX.directories import fcs_data
file_path = fcs_data / "sample_0.fcs"

back_end = BackEnd(file_path=file_path)

data = {
    "column": "488Org(Peak)",
    "max_peaks": 4,
    "clustering_method": "hdb_scan",
    "number_of_points": 10_000,
    "threshold": 400,
    "min_cluster_size": 100,
    "debug": True,
}

result = back_end.find_fluorescence_peaks(data)