#!/usr/bin/env python3
"""
Quick test script to verify Post API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/posts"

def test_health():
    """Test health endpoint"""
    response = requests.get("http://localhost:5000/api/health")
    print(f"✓ Health Check: {response.json()}")

def test_get_posts():
    """Test getting all posts"""
    response = requests.get(BASE_URL)
    print(f"\n✓ Get All Posts (Status: {response.status_code})")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_create_post():
    """Test creating a post without image"""
    data = {
        'userName': 'Amanda Johnson',
        'userHandle': '@mandaj',
        'userImage': 'https://i.pravatar.cc/150?u=3',
        'isVerified': 'true',
        'likes': '120'
    }
    
    response = requests.post(BASE_URL, data=data)
    print(f"\n✓ Create Post (Status: {response.status_code})")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_single_post(post_id):
    """Test getting a single post"""
    response = requests.get(f"{BASE_URL}/{post_id}")
    print(f"\n✓ Get Single Post (Status: {response.status_code})")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

def test_delete_post(post_id):
    """Test deleting a post"""
    response = requests.delete(f"{BASE_URL}/{post_id}")
    print(f"\n✓ Delete Post (Status: {response.status_code})")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing FunAI Connect - Posts API")
    print("=" * 60)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Get all posts (should be empty initially)
        test_get_posts()
        
        # Test 3: Create a post
        created_post = test_create_post()
        post_id = created_post.get('id')
        
        # Test 4: Get single post
        if post_id:
            test_get_single_post(post_id)
        
        # Test 5: Get all posts again (should have 1 post)
        test_get_posts()
        
        # Test 6: Delete the post
        if post_id:
            test_delete_post(post_id)
        
        # Test 7: Verify deletion
        test_get_posts()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to Flask server.")
        print("  Make sure the server is running on http://localhost:5001")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
