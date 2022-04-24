# Radio Data Encoding

This directory contains the files responsible for taking IQ binary files and translating them into JSON files to be sent to the central webserver

## Encoding Workflow
---
The input to this block is a binary file contaning I/Q Data and Metadata Information from GNU Radio

The output to this block is a JSON file containing the encoded I/Q data payload and the relevant metadata
(This output file is sent to the webserver using WebSockets)