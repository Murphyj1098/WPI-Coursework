import requests

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# Making a POST request
# change the url port number, /data path, and filename to whatever is neccessary
r = requests.post(url='http://localhost:5000/data', data=open("sample.json", "rb"), headers=headers)

# check status code for response recieved
# success code - 200
print(r)