import requests

res = requests.post('http://localhost:5000/eval', json={'url':'https://www.ruvilla.com/'})
