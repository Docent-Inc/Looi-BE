from sqlalchemy import Column, Integer, String, Text, BLOB
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/BMSM'
Base = declarative_base()
engine = create_engine(DB_URL, pool_recycle=500)

class Dream(Base):
    __tablename__ = "dreams"

    id = Column(Integer, primary_key=True)
    dream_name = Column(Text)
    dream_resolution = Column(Text)
    image_url = Column(LONGBLOB)

def create_table():
    connection = engine.connect()
    Base.metadata.create_all(connection)
    connection.close()

def save_to_db(dream, dream_resolution, image_url):
    Session = sessionmaker(bind=engine)
    session = Session()
    new_dream = Dream(dream_name=dream, dream_resolution=dream_resolution, image_url=image_url)
    session.add(new_dream)
    session.commit()
    session.close()

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData