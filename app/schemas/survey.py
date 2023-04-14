from pydantic import BaseModel
class SurveyData(BaseModel):
    dream: str
    dreamTime: str
    isRecordDream: str
    isShare: str
    isRecordPlatform: str
    sex: str
    mbti: str
    department: str