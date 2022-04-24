#!/usr/bin/python3

import base64
import sys

in_file = open(sys.argv[1],"rb")
in_data_binary = in_file.read()
in_data = (base64.b64encode(in_data_binary)).decode('ascii')

# print(in_data_binary)
print(in_data)