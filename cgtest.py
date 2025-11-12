import requests

API_BASE = "https://api.coingecko.com/api/v3"
headers = {"x-cg-demo-api-key": "CG-H2mM3QvKvydn1huRAYVG2dMw"}

coin_id = "bitcoin"
r = requests.get(f"{API_BASE}/coins/{coin_id}", headers=headers)
data = r.json()
print(data["categories"])

