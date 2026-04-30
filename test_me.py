import requests

login_data = {
    "username": "test1234@gmail.com",
    "password": "password123"
}
r1 = requests.post("http://localhost:5000/api/auth/login", data=login_data)
if r1.status_code == 200:
    token = r1.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r2 = requests.get("http://localhost:5000/api/stats/me", headers=headers)
    print(r2.status_code)
    print(r2.text)
else:
    print("Login failed", r1.text)
