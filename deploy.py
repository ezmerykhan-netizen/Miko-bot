import requests
from config import Config

class Deploy:
    def railway_restart(self):
        url = f"https://backboard.railway.app/project/{Config.RAILWAY_PROJECT_ID}/restart"
        requests.post(url)

    def koyeb_restart(self):
        url = "https://app.koyeb.com/v1/services/restart"
        headers = {"Authorization": f"Bearer {Config.KOYEB_API_TOKEN}"}
        requests.post(url, headers=headers)
