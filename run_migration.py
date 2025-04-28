from flask import Flask
from sqlalchemy import text
import os

# Import from database
from backend.database import db

app = Flask(__name__)

# Get database URL
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Add place_name column
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE experience ADD COLUMN IF NOT EXISTS place_name TEXT'))
            conn.commit()
        print("Successfully added place_name column to experience table")
    except Exception as e:
        print(f"Error during migration: {e}") 