import requests

# 1. Login as admin
resp = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'admin@university.edu',
    'password': 'admin123'
})
print("Login status:", resp.status_code)
data = resp.json()
print("Login response:", data)

if 'access_token' in data:
    token = data['access_token']
    # 2. Fetch admin analytics
    resp2 = requests.get('http://localhost:8000/api/admin/analytics', headers={
        'Authorization': f'Bearer {token}'
    })
    print("\nAnalytics status:", resp2.status_code)
    try:
        print("Analytics response:", resp2.json())
    except:
        print("Analytics text:", resp2.text)
