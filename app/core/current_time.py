import pytz
from datetime import datetime
def get_current_time():
    korea_timezone = pytz.timezone("Asia/Seoul")
    korea_time = datetime.now(korea_timezone)
    formatted_time = korea_time.strftime("%Y%m%d%H%M%S")
    return formatted_time

def get_jp_time():
    jp_timezone = pytz.timezone("Asia/Tokyo")
    jp_time = datetime.now(jp_timezone)
    formatted_time = jp_time.strftime("%Y%m%d%H%M%S")
    return formatted_time
