from pydantic import BaseModel
class SurveyData(BaseModel):
    dream: str
    gender: str
    age: str
    mbti: str
    department: str