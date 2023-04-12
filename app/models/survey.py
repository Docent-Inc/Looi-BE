from pydantic import BaseModel
class SurveyData(BaseModel):
    gender: str
    age: str
    mbti: str
    department: str