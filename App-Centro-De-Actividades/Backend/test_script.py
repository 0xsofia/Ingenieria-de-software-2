import requests

res = requests.get('http://127.0.0.1:5000/api/cambiar-contrasena/dummy_token')
print(res.status_code, res.text)
