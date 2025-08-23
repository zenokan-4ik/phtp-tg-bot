import requests

class Api:
    def __init__(self, base_url: str):
        self.url = base_url
        
    def post(self, endpoint: str, data: dict):
        response = requests.post(self.url+endpoint, data)
        return response.content.decode()
    
    def get(self, endpoint: str, data: dict):
        response = requests.get(self.url+endpoint, data)
        return response.content.decode()
    
api = Api('http://127.0.0.1:8000/api/')
print(api.get('getrequests', {}))