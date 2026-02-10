from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print("Existing Users:")
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Name: {user.name}")
