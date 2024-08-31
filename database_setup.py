# database_setup.py

from app import app, db, User

with app.app_context():
    # Create all tables
    db.create_all()

    # Optionally, add a test user
    test_user = User(username='testuser', email='test@example.com')
    db.session.add(test_user)
    db.session.commit()

    print("Database initialized!")