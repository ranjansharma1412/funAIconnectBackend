
from app import create_app, db
from app.models.user import User
from app.models.post import Post
import json

app = create_app()

def test_comment_flow():
    print("=" * 60)
    print("Testing FunAI Connect - Comment API (Integration)")
    print("=" * 60)

    # Ensure we are working with the app context
    with app.app_context():
        # Create a test user if it doesn't exist
        user = User.query.filter_by(username='comment_tester').first()
        if not user:
            user = User(
                username='comment_tester',
                email='tester@example.com',
                full_name='Comment Tester'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print(f"✓ Test User created/found with ID: {user.id}")
        else:
            print(f"✓ Test User found with ID: {user.id}")
        
        user_id = user.id

    # Start the test client
    with app.test_client() as client:
        
        # 1. Create a Post
        print("\n[1] Creating a new post...")
        post_data = {
            'userName': 'Comment Tester',
            'userHandle': '@comment_tester',
            'userImage': 'https://i.pravatar.cc/150',
            'description': 'This is a test post for comments.',
            'likes': 0
        }
        # Note: endpoint is /api/posts as per blueprint registration
        post_res = client.post('/api/posts', data=post_data)
        
        if post_res.status_code != 201:
            print(f"✗ Failed to create post: {post_res.status_code}")
            print(post_res.get_json())
            return
        
        post = post_res.get_json()
        post_id = post['id']
        print(f"✓ Post created with ID: {post_id}")

        # 2. Add a Comment
        print("\n[2] Adding a comment...")
        comment_data = {
            'content': 'This is a test comment from integration test!',
            'userId': user_id
        }
        comment_res = client.post(f'/api/posts/{post_id}/comments', json=comment_data)
        
        if comment_res.status_code == 201:
            comment = comment_res.get_json()
            comment_id = comment['id']
            print(f"✓ Comment added with ID: {comment_id}")
            print(f"  Content: {comment['content']}")
        else:
            print(f"✗ Failed to add comment: {comment_res.status_code}")
            print(comment_res.get_json())
            return

        # 3. Get Comments
        print("\n[3] Retrieving comments...")
        get_res = client.get(f'/api/posts/{post_id}/comments')
        if get_res.status_code == 200:
            comments = get_res.get_json()['comments']
            print(f"✓ Retrieved {len(comments)} comments")
            if len(comments) > 0:
                print(f"  First comment: {comments[0]['content']}")
        else:
            print(f"✗ Failed to get comments: {get_res.status_code}")

        # 4. Delete Comment
        print("\n[4] Deleting comment...")
        del_res = client.delete(f'/api/posts/{post_id}/comments/{comment_id}')
        if del_res.status_code == 200:
            print("✓ Comment deleted successfully")
        else:
            print(f"✗ Failed to delete comment: {del_res.status_code}")

        # 5. Verify Deletion
        print("\n[5] Verifying deletion...")
        get_res_2 = client.get(f'/api/posts/{post_id}/comments')
        comments_2 = get_res_2.get_json()['comments']
        if len(comments_2) == 0:
            print("✓ Verification successful: No comments found")
        else:
            print(f"✗ Verification failed: Found {len(comments_2)} comments")

if __name__ == "__main__":
    test_comment_flow()
