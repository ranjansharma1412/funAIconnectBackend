import requests

BASE_URL = "http://127.0.0.1:5001"

def test_friends():
    print("Testing Friends API...")

    # 1. Register test users
    u1_data = {
        'username': 'testuserA',
        'email': 'testuserA@example.com',
        'password': 'password123',
        'fullName': 'Test User A'
    }
    u2_data = {
        'username': 'testuserB',
        'email': 'testuserB@example.com',
        'password': 'password123',
        'fullName': 'Test User B'
    }

    print("\nRegistering users...")
    r1 = requests.post(f"{BASE_URL}/api/auth/register", json=u1_data)
    r2 = requests.post(f"{BASE_URL}/api/auth/register", json=u2_data)

    if r1.status_code == 201:
        u1_id = r1.json()['user']['id']
    else:
        # User A probably exists, log them in
        r1 = requests.post(f"{BASE_URL}/api/auth/login", json={'email': 'testuserA@example.com', 'password': 'password123'})
        u1_id = r1.json()['user']['id']
        
    if r2.status_code == 201:
        u2_id = r2.json()['user']['id']
    else:
        # User B probably exists, log them in
        r2 = requests.post(f"{BASE_URL}/api/auth/login", json={'email': 'testuserB@example.com', 'password': 'password123'})
        u2_id = r2.json()['user']['id']

    print(f"User A ID: {u1_id}, User B ID: {u2_id}")

    # 2. Test Suggestions
    print("\nFetching suggestions for User A...")
    r = requests.get(f"{BASE_URL}/api/friends/suggestions?user_id={u1_id}")
    print(r.status_code, r.json())
    
    # 3. Send Request A -> B
    print("\nUser A sends friend request to User B...")
    r = requests.post(f"{BASE_URL}/api/friends/request", json={'userId': u1_id, 'friendId': u2_id})
    print(r.status_code, r.json())

    # 4. Fetch Requests for User B
    print("\nFetching requests for User B...")
    r = requests.get(f"{BASE_URL}/api/friends/requests?user_id={u2_id}")
    print(r.status_code, r.json())
    requests_data = r.json()
    
    request_id = None
    if requests_data.get('requests') and len(requests_data['requests']) > 0:
        request_id = requests_data['requests'][-1]['id']
    
    # 5. Accept Request
    if request_id:
        print(f"\nUser B accepts request {request_id} from User A...")
        r = requests.post(f"{BASE_URL}/api/friends/accept", json={'userId': u2_id, 'requestId': request_id})
        print(r.status_code, r.json())
    
    # 6. Test Suggestions again (Should not contain each other)
    print("\nFetching suggestions for User A again...")
    r = requests.get(f"{BASE_URL}/api/friends/suggestions?user_id={u1_id}")
    print(r.status_code, r.json())

if __name__ == '__main__':
    test_friends()
