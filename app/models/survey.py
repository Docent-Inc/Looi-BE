from pydantic import BaseModel
class SurveyData(BaseModel):
    text: str
    gender: str
    age: str
    mbti: str
    department: str