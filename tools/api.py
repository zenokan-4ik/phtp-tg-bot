import requests

class Api:
    def __init__(self, base_url: str):
        self.url = base_url
        
    def post(self, endpoint: str, data: dict, files: dict = None):
        if files:
            response = requests.post(self.url + endpoint, data=data, files=files)
        else:
            response = requests.post(self.url + endpoint, data=data)
        print('request status code ', response.status_code)
        return response.content.decode()
    
    def get(self, endpoint: str, data: dict):
        response = requests.get(self.url + endpoint, data=data)
        print('request status code ', response.status_code)
        return response.content.decode()