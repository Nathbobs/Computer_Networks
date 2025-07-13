import requests
import os
from dotenv import load_dotenv

load_dotenv()
getGasOracle_apikey = os.getenv('getGasOracle_apikey')


def get_gasprice_info():
    url = " https://api.etherscan.io/api?module=stats&action=dailyavggaslimit&startdate=2019-02-01&enddate=2019-02-28&sort=asc&apikey={getGasOracle_apikey} "
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        return None