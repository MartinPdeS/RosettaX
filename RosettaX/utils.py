import os

def generate_file_list_for_sidebar():
    paths_of_files = {}
    for root, _, files in os.walk("RosettaX/SavedCalibrations"):
        for fname in files:
            name = os.path.normpath(os.path.join(root, fname))
            name = name.replace("\\", "/")
            name = name.replace("RosettaX/SavedCalibrations/", "")
            name = name.split("/")
            if name[0] not in paths_of_files:
                paths_of_files[name[0]] = []
            paths_of_files[name[0]].append("/".join(name[1:]))
    paths_of_files = dict(sorted(paths_of_files.items()))
    return paths_of_files
