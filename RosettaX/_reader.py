# # -*- coding: utf-8 -*-
# """
# Created on Sat Jun  8 15:32:44 2024

# @author: Edwin van der Pol
# contact: e.vanderpol@exometry.com

# Description: Module to read FCS files
# """

# import os # functions related to the operating system, for example to check the file size
# import struct
# import numpy as np
# import pandas as pd

# # ==========================
# # Section: Small functions
# # ==========================

# # Check whether a variable contains an integer
# def is_integer(s):
#     try:
#         int(s)
#         return True
#     except ValueError:
#         return False

# # Define error messages that are called by multiple methods
# def error_message_file_does_not_exist(file_path):
#     return '"' + file_path[file_path.rfind('/') + len('/'):] + '" does not exist.'

# def error_message_file_is_too_small(file_path):
#     return '"' + file_path[file_path.rfind('/') + len('/'):] + '" is not a valid FCS file, because the file is smaller than allowed.'

# # Start of class read_fcs_file
# class read_fcs_file:

#     # ==============================================================
#     # Define the instances of the class and read the HEADER and TEXT
#     # ==============================================================

#     def __init__(self, file_path):

#         # ===================
#         # Method: Read HEADER
#         # ===================

#         def read_fcs_header(file_path):

#             # define empty return variables
#             fcs_header_parsed = {}
#             error_message = ''

#             # check whether the file exists
#             if not os.path.isfile(file_path):
#                 error_message_file_does_not_exist(file_path)
#                 return fcs_header_parsed, error_message

#             # stop processing FCS file if it is smaller than 257 characters
#             if os.path.getsize(file_path)<257:
#                 error_message = error_message_file_is_too_small(file_path)
#                 return fcs_header_parsed, error_message

#             with open(file_path, 'rb') as f:

#                 # Read the HEADER section
#                 header = f.read(256)

#                 # Extract version (first 6 bytes)
#                 fcs_version = header[:6].decode('ascii')

#                 # stop processing FCS file if the FCS version is not well-defined
#                 if not any(string == fcs_version for string in ["FCS2.0", "FCS3.0", "FCS3.1"]):
#                     error_message = '"' + file_path[file_path.rfind('/') + len('/'):] + '" is not a valid FCS file, because the FCS version is undefined.'
#                     return fcs_header_parsed, error_message

#                 try:
#                     # Extract text segment positions
#                     text_start = int(header[10:18].strip())
#                     text_end = int(header[18:26].strip())

#                     # Extract data segment positions
#                     data_start = int(header[26:34].strip())
#                     data_end = int(header[34:42].strip())
#                 except:
#                     error_message = '"' + file_path[file_path.rfind('/') + len('/'):] + '" is not a valid FCS file, because the file segments are undefined.'
#                     return fcs_header_parsed, error_message

#                 # Merge obtained variables
#                 fcs_header_parsed = {
#                     "FSC version": fcs_version,
#                     "Text start": text_start,
#                     "Text end": text_end,
#                     "Data start": data_start,
#                     "Data end": data_end,
#                 }

#                 return fcs_header_parsed, error_message

#         # ==================
#         # Section: Read TEXT
#         # ==================

#         def read_fcs_text(file_path, text_start, text_end):
#             with open(file_path, 'rb') as f:

#                 # Read the TEXT section
#                 f.seek(text_start)
#                 text_section = f.read(text_end - text_start + 1).decode('ascii')

#                 # Obtain the delimiting_character
#                 delimiting_character = text_section[0]
#                 # Remove first delimiting_character
#                 text_section = text_section[1:]

#                 # Parse text items into a dictionary
#                 fcs_text_parsed = {'Keywords':{},'Detectors':{}}
#                 text_items = text_section.strip().split(delimiting_character)
#                 # Loop over all text-itmes
#                 for text_item_id in range(0, len(text_items) - 1, 2):
#                     key = text_items[text_item_id].strip()
#                     value = text_items[text_item_id + 1].strip()
#                     # convert strings to integers when applicable
#                     if is_integer(value):
#                         value = int(value)
#                     fcs_text_parsed['Keywords'][key] = value

#                 # Merge detector parameters
#                 for detector_id in range(1, fcs_text_parsed['Keywords']['$PAR']+1):

#                     # add nested library
#                     fcs_text_parsed['Detectors'][detector_id] = {}

#                     # Function that merges detector parameters
#                     def merge_detector_parameters(detector_id,keyword_end,fcs_text_parsed):

#                         if '$P' + str(detector_id) + keyword_end in fcs_text_parsed['Keywords']:

#                             # group required detector parameters
#                             fcs_text_parsed['Detectors'][detector_id][keyword_end] = fcs_text_parsed['Keywords']['$P' + str(detector_id) + keyword_end]

#                             # delete required detector parameters from Keywords
#                             del fcs_text_parsed['Keywords']['$P' + str(detector_id) + keyword_end]

#                         return fcs_text_parsed

#                     detector_keyword_ends = list({'B','E','N','R','D','F','G','L','O','P','S','T','V','TYPE'})

#                     # loop over all possible detector parameter keyword endings
#                     for detector_keyword_ends_id in range(0, len(detector_keyword_ends)):

#                         fcs_text_parsed = merge_detector_parameters(detector_id,detector_keyword_ends[detector_keyword_ends_id],fcs_text_parsed)

#                 return fcs_text_parsed, delimiting_character

#         # ==============================================================
#         # Define the instances of the class and read the HEADER and TEXT
#         # ==============================================================

#         # define instances
#         self.error_message = ''
#         self.file_path = file_path

#         # read the HEADER, which is the first line of the FCS file
#         self.fcs_header_parsed, self.error_message = read_fcs_header(file_path)

#         # the header was not appropriately parsed: stop processing this FCS file
#         if not self.fcs_header_parsed:
#             return

#         try:
#             # read the TEXT, which contains general information and channel information
#             self.fcs_text_parsed, self.delimiting_character = read_fcs_text(file_path, self.fcs_header_parsed["Text start"], self.fcs_header_parsed["Text end"])
#         except Exception as e:
#             self.error_message = 'An error occurred while reading file "' + file_path[file_path.rfind('/') + len('/'):] + '": {str(e)}'


#     # ==================
#     # Section: Read DATA
#     # ==================

#     def read_all_data(self):

#         # To keep the code readable, get the keywords required for reading the DATA section
#         data_start = self.fcs_header_parsed["Data start"]
#         data_end = self.fcs_header_parsed["Data end"]
#         num_events = self.fcs_text_parsed['Keywords']['$TOT']
#         num_parameters = self.fcs_text_parsed['Keywords']['$PAR']
#         datatype = self.fcs_text_parsed['Keywords']['$DATATYPE']

#         # Check whether data-end if defined. If not, this is a large file and data-start and -end need to be obtained from the TEXT segment instead of form the HEADER segment
#         if data_end == 0:
#             data_start = self.fcs_text_parsed['Keywords']['$BEGINDATA']
#             data_end = self.fcs_text_parsed['Keywords']['$ENDDATA']

#         # check whether the file exists
#         if not os.path.isfile(self.file_path):
#             self.error_message = error_message_file_does_not_exist(self.file_path)

#         # stop processing FCS file if it is smaller than length of HEADER+TEXT+DATA from the TEXT section
#         if os.path.getsize(self.file_path)<data_end:
#             self.error_message = error_message_file_is_too_small(self.file_path)

#         # Mapping between FCS data type codes and NumPy data types
#         dtype_mapping = {
#             'F': 'float32',  # Floating point
#             'D': 'float64',  # Double precision floating point
#             'I': 'int32',    # Signed integer
#             'L': 'uint32'    # Unsigned integer
#         }

#         # Determine the dtype based on the $DATATYPE keyword
#         dtype = dtype_mapping.get(datatype)

#         # Calculate the total number of elements
#         total_elements = num_events * num_parameters

#         # Define headings for the columns of fcs_data
#         parsed_detector_properties = self.fcs_text_parsed['Detectors']
#         column_headings = [detector_property['N'] for detector_property in parsed_detector_properties.values()]

#         with open(self.file_path, 'rb') as f:
#             # Seek to the start of data and read the segment
#             f.seek(data_start)

#             # Unpack data_segment directly into self.fcs_data
#             self.fcs_data = pd.DataFrame(np.frombuffer(f.read(data_end - data_start + 1), dtype=dtype, count=total_elements).reshape((num_events, num_parameters)), columns=column_headings)
