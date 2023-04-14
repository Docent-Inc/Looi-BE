from pydantic import BaseModel
class SurveyData(BaseModel):
    dream: str
    isRecord: str
    sex: str
    mbti: str
    department: str