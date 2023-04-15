from pydantic import BaseModel

'''
bmongsmong.com
pretotyping 설문조사 페이지 request body 구조
'''
class SurveyData(BaseModel):
    dream: str
    dreamTime: str
    isRecordDream: str
    isShare: str
    isRecordPlatform: str
    sex: str
    mbti: str
    department: str