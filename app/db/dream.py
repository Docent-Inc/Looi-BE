from app.db.database import SessionLocal
from app.models.dream import Dream

def save_to_db(text, dream, dream_resolution, image_url):
    session = SessionLocal()
    new_dream = Dream(text=text, dream_name=dream, dream_resolution=dream_resolution, image_url=image_url)
    session.add(new_dream)
    session.commit()
    session.close()

def convert_to_binary_data(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binary_data = file.read()
    return binary_data
