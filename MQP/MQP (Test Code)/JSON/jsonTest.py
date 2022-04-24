#! /usr/bin/python3

import json

time = "102722020-152531"
sample = 0
cmplx = True
data = "MQ=="

x = {
    "metadata" : [
        {
            "rx_time" : time,
            "rx_sample" : sample,
            "cplx" : cmplx
        }
    ],
    "payload" : data
}

with open('data.json', 'w') as outfile:
    json.dump(x, outfile, indent=4)