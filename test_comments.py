import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_comment_flow():
    print("=" * 60)
    print("Testing FunAI Connect - Comment API")
    print("=" * 60)

    try:
        # 1. Create a User (if not exists, or just pick ID 1. Let's assume ID 1 exists from previous usage or we pick one)
        # For simplicity, we'll try to use a hardcoded user ID 1. If it fails, we might need to create one.
        user_id = 1
        
        # 2. Create a Post
        print("\n[1] Creating a new post...")
        post_data = {
            'userName': 'Test User',
            'userHandle': '@testuser',
            'userImage': 'https://i.pravatar.cc/150',
            'description': 'This is a test post for comments.',
            'likes': 0
        }
        post_res = requests.post(f"{BASE_URL}/posts", data=post_data)
        if post_res.status_code != 201:
            print(f"Failed to create post: {post_res.text}")
            return
        
        post = post_res.json()
        post_id = post['id']
        print(f"✓ Post created with ID: {post_id}")

        # 3. Add a Comment
        print("\n[2] Adding a comment...")
        comment_data = {
            'content': 'This is a test comment!',
            'userId': user_id
        }
        comment_res = requests.post(f"{BASE_URL}/posts/{post_id}/comments", json=comment_data)
        
        if comment_res.status_code == 201:
            comment = comment_res.json()
            comment_id = comment['id']
            print(f"✓ Comment added with ID: {comment_id}")
            print(f"  Content: {comment['content']}")
        else:
            print(f"✗ Failed to add comment: {comment_res.status_code} - {comment_res.text}")
            # Try to see if it's because user doesn't exist
            if "User ID" in comment_res.text or "IntegrityError" in comment_res.text: # simplistic check
                 print("  (Make sure User with ID 1 exists)")
            return

        # 4. Get Comments
        print("\n[3] Retrieving comments...")
        get_res = requests.get(f"{BASE_URL}/posts/{post_id}/comments")
        if get_res.status_code == 200:
            comments = get_res.json()
            print(f"✓ Retrieved {len(comments)} comments")
            print(f"  First comment: {comments[0]['content']}")
        else:
            print(f"✗ Failed to get comments: {get_res.status_code}")

        # 5. Delete Comment
        print("\n[4] Deleting comment...")
        del_res = requests.delete(f"{BASE_URL}/posts/{post_id}/comments/{comment_id}")
        if del_res.status_code == 200:
            print("✓ Comment deleted successfully")
        else:
            print(f"✗ Failed to delete comment: {del_res.status_code}")

        # 6. Verify Deletion
        print("\n[5] Verifying deletion...")
        get_res_2 = requests.get(f"{BASE_URL}/posts/{post_id}/comments")
        comments_2 = get_res_2.json()
        if len(comments_2) == 0:
            print("✓ Verification successful: No comments found")
        else:
            print(f"✗ Verification failed: Found {len(comments_2)} comments")

    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    test_comment_flow()
