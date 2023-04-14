from app.db.database import SessionLocal
from app.models.dream import Dream
from app.schemas.survey import SurveyData
def save_to_db(text, dream, dream_resolution, survey_data: SurveyData):
    session = SessionLocal()
    new_dream = Dream(
        dreamTime=survey_data.dreamTime,
        isRecordDream=survey_data.isRecordDream,
        isShare=survey_data.isShare,
        isRecordPlatform=survey_data.isRecordPlatform,
        sex=survey_data.sex,
        mbti=survey_data.mbti,
        department=survey_data.department,
        text=text,
        dream_name=dream,
        dream_resolution=dream_resolution
    ) # image_url=image_url)
    session.add(new_dream)
    session.commit()
    session.close()

def convert_to_binary_data(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binary_data = file.read()
    return binary_data
