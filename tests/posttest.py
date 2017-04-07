import requests
import json

j = """{"update_id": 410552012, "message": {"message_id": 4, "from": {"id": 227067835, 
"first_name": "Luca", "username": "Hixos"}, "chat": {"id": 227067835, "first_name": "Luca", "username": 
"Hixos", "type": "private"}, "date": 1491587800, "text": "sushi"}}"""

grr = json.loads(j)
r = requests.post('http://127.0.0.1:5000/370015750:AAFy9wyS0Zc8_u290z8NgMxNe944Z0iBZLo', json=grr)