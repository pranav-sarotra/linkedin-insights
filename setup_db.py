"""
Database setup script.
Run this before starting the application.
"""
import pymysql
from app.config import Config


def create_database():
    """Create the database if it doesn't exist"""
    print(f"Connecting to MySQL at {Config.DB_HOST}...")
    
    connection = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            print(f"Database '{Config.DB_NAME}' created or already exists.")
    finally:
        connection.close()


def create_tables():
    """Create all tables"""
    from app import create_app
    from app.models import db
    
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("All tables created successfully.")


if __name__ == '__main__':
    print("=" * 50)
    print("Setting up database...")
    print("=" * 50)
    
    try:
        create_database()
        create_tables()
        print("=" * 50)
        print("Database setup complete!")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. MySQL is running")
        print("2. Your .env file has the correct password")
        print("3. The DB_USER has permission to create databases")