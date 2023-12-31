import asyncio
import json
import uuid
from io import BytesIO
import extcolors
import openai
import requests
from PIL import Image
from fastapi import HTTPException, status
import datetime
import pytz
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import time_now
from app.db.database import save_db
from app.db.models import ApiRequestLog, User, Prompt
import boto3

service_name = 's3'
endpoint_url = 'https://kr.object.ncloudstorage.com'
region_name = 'kr-standard'
access_key = settings.NAVER_CLOUD_ACCESS_KEY_ID
secret_key = settings.NAVER_CLOUD_SECRET_KEY
# boto3 클라이언트 생성
s3_client = boto3.client(
    service_name,
    endpoint_url=endpoint_url,
    region_name=region_name,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)
async def upload_image_to_naver_cloud(img):
    # 유니크한 파일 이름 생성
    unique_id = uuid.uuid4()
    destination_blob_name = str(unique_id) + ".png"
    bucket_name = "looi"  # 네이버 클라우드 버킷 이름

    # 이미지를 BytesIO 객체로 변환
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # 이미지 업로드
    s3_client.put_object(
        Bucket=bucket_name,
        Key=destination_blob_name,
        Body=buffer,
        ACL='public-read'  # public 접근 가능하도록 설정
    )

    # public URL 반환
    return f"{endpoint_url}/{bucket_name}/{destination_blob_name}"

SERVICE_ACCOUNT_INFO = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
openai.api_key = settings.GPT_API_KEY

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

prompt1 = [
    {"role": "system", "content": "사용자의 텍스트가 꿈, 일기, 메모, 일정 중 어떤 카테고리인지 분류해서 숫자만 반환해줘. 꿈 = 1, 일기 = 2, 메모 = 3, 일정 = 4"},
    {"role": "system", "content": "내용이 짧으면 메모 또는 일정일 확률이 높고, 꿈이라는 단어가 포함되면 꿈, 오늘 내가 한 일들과 생각들이 포함되면 일기일 확률이 높다."},
    {"role": "system", "content": "날짜와 관련된 단어가 포함되면 일정일 확률이 높다."},
    {"role": "system", "content": "시간대가 오전이면 꿈일 확률이 높고 오후면 일기일 확률이 높다."},
    {"role": "system", "content": "나머지는 메모로 분류해줘. return 1, 2, 3, 4"},
    {"role": "user", "content": "2023-08-20 07:00:00 엄청나게 맑고 깨끗한 낚시터에서 낚시했는데 어찌나 투명한지 물고기가 다 보이는 꿈"},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "2023-08-20 22:00:00 오늘은 하루종일 코딩을 했다. 내가 만든 코드는 잘 돌아가지 않고, 너무 고통받았다. 내일은 개발을 마무리해서 얼른 서비스를 출시하고 싶다"},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "2023-08-20 15:00:00 엘리스 세습 책 읽기, 56쪽"},
    {"role": "system", "content": "3"},
    {"role": "user", "content": "2023-08-20 15:00:00 8월25일 저녁6시 강남 약속"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "2023-08-20 19:00:00 오늘은 크리스마스다. 여자친구와 현대백화점에 가서 아웃백을 먹고 영화를 봤다. 오펜하이머를 봤는데 나는 사실 물리학과를 갔어야 될 것 같다. 너무 재미있었다."},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "2023-08-20 15:00:00 다음주 금요일 6시에 중앙도서관 앞에서 자동차 동아리 모임이 있어"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "2023-08-21 08:00:00 스키장에서 스키를 타고 있는데 뒤에서 곰이 갑자기 튀어나와서 도망가다가 넘어지고, 꿈에서 깼어"},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "2023-08-24 09:00:00 꿈에서 어떤 길에서 있었는데 하을을 올려보니 보름달이 구름에 가려져 빛나고 있었다. 구름에 가려졌지만 밝게 빛나고 있어서 보름달이 잘 보였다. 보름달은 이내 구름 위로 솟아 올라 밝게 빛났다."},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "2023-08-24 17:00:00 학교에서 계속 공부를했다. 너무 힘든 하루였지만 마무리가 깔끔해서 기분좋게 잠에 잘 수 있을 것 같다. 내일은 더 열심히 해야겠다."},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "2023-08-25 19:11:24 11월 20일부터 28일은 부산으로 여행갈거야"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "2023-11-22 19:24:24 오늘 내역서 작업하느라 매우 바빴는데 저녁에 회를 먹어서 호다닥 달려옴"},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "2023-11-22 20:12:51 아침마다 파업 그만했으면 좋겠다 한놈만 걸려라 다 패버린다"},
    {"role": "system", "content": "2"},
]


prompt2 = [
    {"role": "system", "content": "사용자의 스토리에 대한 제목을 만들어줘(only title)"},
    {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
    {"role": "system", "content": "수상한 강아지의 탈출 대작전"},
    {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
    {"role": "system", "content": "비둘기와 나의 특별한 우정"},
    {"role": "user", "content": "오늘은 크리스마스다. 여자친구와 현대백화점에 가서 아웃백을 먹고 영화를 봤다. 오펜하이머를 봤는데 나는 사실 물리학과를 갔어야 될 것 같다. 너무 재미있었다."},
    {"role": "system", "content": "크리스마스 데이트"},
    {"role": "user", "content": "학교에서 계속 공부를했다. 너무 힘든 하루였지만 마무리가 깔끔해서 기분좋게 잠에 잘 수 있을 것 같다. 내일은 더 열심히 해야겠다."},
    {"role": "system", "content": "학교에서 공부하는 나"},
    {"role": "user", "content": "하늘을 떠다니는 능력이 있어서 맘을 먹으면 하늘로 둥둥 뜨는 능력을 가지고 날면서 돌아다니는 꿈을 종종 꾸어요. 하늘을 날기 위해서는 집중을 해야 가능한데 꿈속에서도 간혹 잘 되기도 하고 잘 안 되는 경우도 있는데 대부분은 집중하면 하늘을 날 수 있더라고요. 이 꿈이 어떤 의미가 있을까요??"},
    {"role": "system", "content": "하늘을 날아다니는 꿈"},
    {"role": "user", "content": "개꿈을 꾸었어요 어떤 의미가 있을까요??"},
    {"role": "system", "content": "개꿈"},
    {"role": "user", "content": "높은 빌딩 내 통유리로 된 호텔 방 침대 위에 나랑 친한 지인이랑 잘 모르는 남자랑 셋이서 앉아있었어. 나랑 친한 지인이랑 대화를 하면서 난 정면에 야경이 보이는 유리창을 보고 있었는데, 갑자기 내 뒤에서 잘 모르는 남자가 날 끌어안은 거야. 당황해서 가만히 있었는데, 내 이상형이랑 정반대인 남자였지만 엄청 설레어했던 내용이었어."},
    {"role": "system", "content": "의문의 이상형"},
    {"role": "user", "content": "비행기나 기차를 놓치는 꿈"},
    {"role": "system", "content": "잃어버린 시간"},
]

prompt3 = [
    {"role": "system", "content": "make just one scene a prompt for DALLE2"},
    {"role": "system", "content": "include the word illustration, digital art, vivid and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
    {"role": "system", "content": "make just prompt only engilsh"},
    {"role": "system", "content": "max_length=250"},
    {"role": "user", "content": "학교 복도에서 친구랑 얘기하다가 갑자기 앞문쪽에서 좀비떼가 몰려와서 도망침. 근데 알고보니 우리반 애였음. 걔네 반 담임쌤한테 가서 말하니까 쌤이 괜찮다고 하심. 그래서 안심하고 있었는데 또다른 좀비가 와서 막 물어뜯음. 그러다가 깼는데 아직도 심장이 벌렁벌렁 거림.."},
    {"role": "system", "content": "Digital art of a zombie attack in a school corridor, with an eerie green glow and splatters of red, highlighting the tension of the chase and ambush."},
    {"role": "user", "content": "학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다."},
    {"role": "system", "content": "Lively digital illustration of a student getting a tarot reading at a school festival, with warm lighting and a mix of disappointment and relief on their face amidst vibrant colors."},
    {"role": "user", "content": "적에게 계속 도망치면서 세상을 구할 목표를 향해 팀원들과 향해 나아간다. 모험중에서 새로운 사람도 만나며 나아가지만 결국 나 혼자서 해내야 하는 상황에 마주친다. 하지만 목표를 향한 문제 풀이 과정에서 답도 모르지만 안풀리는 상황에 놓이고 적에게 붙잡히지는 않았지만 따라잡히게 된다."},
    {"role": "system", "content": "Digital illustration capturing a hero's solitary quest in a fantasy world, with rich colors and dramatic lighting that evoke determination amid anxiety."},
    {"role": "user", "content": "연락이 끊겼던 서현이 누나한테 연락이 왔다. 다시 연락이 안올줄 알았는데 연락이 와서 깜짝 놀랬다. 바로 전화를 걸어서 3시간동안 얘기를 했고, 다음주 토요일에 만날 약속을 잡았다. 썸인가? 사귀는 사이는 아닌데 아무것도 아닌 사이도 아닌 것 같다."},
    {"role": "system", "content": "Digital illustration of a surprising late-night phone call reuniting two people, with expressions of shock and joy, capturing the long, deep conversation and the anticipation of a planned meeting."},
    {"role": "user", "content": "이대형 대표님의 강의에서 큰 깨달음을 얻었다. 창업을 하는 과정에서 팀원을 구하는 것에 어려움을 느껴 지쳐가고 있었던 나에게 지금 내가 새로운 팀원에게 제공할 수 있는 것을 깨닫게 되었고 다시 힘을 얻을 수 있었다."},
    {"role": "system", "content": "Digital art of an entrepreneur's enlightening moment during a lecture, a look of realization dawning as they jot down notes, re-energized for team building."},
    {"role": "user", "content": "오늘부터 다이어트를 시작하기로 했는데, 배가 너무 고파서 저녁에 붕어빵을 먹어버렸어 ㅠㅠ. 내일은 저녁 약속이 있어서 치팅데이인데... 수요일부터는 진짜 식단 조절을 해야 해. "},
    {"role": "system", "content": "Digital illustration of a guilty late-night snack, with a character eyeing a half-eaten fish-shaped pastry, contemplating the upcoming cheat day and the resolve for a stricter diet plan starting Wednesday."},
    {"role": "user", "content": "안녕하세요, 곽서준 님. 지난 일주일 동안 꿈과 일기, 일정을 통해 분석된 정신 상태를 다음과 같이 보고드리겠습니다. 전반적으로 당신의 꿈과 동작이 활동적인 편이며, 친밀한 관계의 구축 위주로 이루어진 것으로 보아 외향적인 성향이 강하게 나타납니다. 또한 생소한 사람들과의 상호 작용에 신경을 썼다는 점이 눈에 띕니다."},
    {"role": "system", "content": "Digital illustration depicting a dynamic individual surrounded by a network of colorful, interconnected lines representing lively dreams and an extroverted personality, with symbols of new encounters and friendships emphasizing their social nature and focus on building close relationships."},
    {"role": "user", "content": "붉은 노을 아래 펼쳐진 광활한 바다에서 서핑을 하다가 물에 빠지는 꿈을 꿨어"},
    {"role": "system", "content": "Digital art of a surfer falling into the ocean during a dream, set against a vivid sunset, with a blend of warm colors and cool blues to capture the sense of dread and awe in the vast sea."},
]

prompt4 = [
    {"role": "system", "content": "오늘의 운세를 만들어줘,\"\" 안에 있는 글자는 4자로 만들어줘, follow the format"},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"여어득수\" 입니다. 기대치 않았던 곳에서 큰 지원을 받게 되니 일을 더욱 잘 풀리고 몸과 마음 또한 더없이 기쁘고 편할 수 있을 것입니다. 당신에게 스트레스로 작용했던 일이 있다면 당신의 노력이 바탕이 되어 해결할 수 있는 기회도 잡을 수 있습니다. 또한 주변사람들로부터 도움이나 조언을 통해서 자신의 방향을 잡을 수도 있습니다. 그러나 자신의 의지를 잃지 않는 것도 중요한 부분입니다. 당신에게 닥친 이 기회를 잘 활용한다면 충분히 많은 성과와 발전이 있을 것이지요. 조금 더 분발하세요."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"박장대소\" 입니다. 좋은 운이 당신에게 많이 몰리는 날입니다. 당신이 목표하고 있는 일이 있다면 별 어려움 없이 일을 해결해 나갈 수 있을 것입니다. 또한 당신의 모든 능력이 사람들로 하여금 인정을 받을 수 있으니 당신의 운은 최상을 달리고 있습니다. 물론 당신의 노력이 함께 해야지만 더 멋진 의미를 가져올 수 있습니다. 특히 다른 사람과 경쟁을 벌이고 있거나 시험에 도전하고 있는 등의 경우라면 당신의 능력에 하늘의 힘이 곁들여져서 좋은 결과를 맛볼 수 있을 것이니 자신감 있게 나서 보시기 바랍니다."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"일필휘지\" 입니다. 만사가 잘 풀리고 여러 곳에서 도움을 받을 수 있으니 더없이 좋은 날입니다. 당신에게 있어 어떠한 부족한 점이 있는지도 이런 기회를 이용해서 한번 생각해본다면 좋은 바탕이 될 것입니다. 또한 자신이 목표하고 있는 일이 생각대로 잘 풀려가기 때문에 주변사람들의 응원이 더욱 빛을 발할 것입니다. 그리고 어려움이 있을 땐 가까운 사람에게 주저 말고 도움을 청해 보도록 하십시오. 마치 자신의 일과 같이 성실하고 친절하게 잘 도와주려 할 것이니 말이지요. 고맙게 받고 잘 활용하도록 하세요"},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"금의환향\" 입니다. 여기저기서 좋은 소식이 들려오니 당신의 기분 또한 좋아질 것입니다. 오랫동안 못 보던 사람에게서 연락을 받을 수 있으며 이는 자신에게 있어 득이 되는 소식일 수 있습니다. 또한 형제 자매가 중요한 시험에 붙는다거나 부모님께서 경사를 맞는다는 일도 생길 수 있습니다. 이처럼 오늘은 당신에게 직접 행운이 따르기 보다는 주변 사람들이 더 많은 운을 누릴 수 있는 날입니다. 당신이 마음에서 우러나는 축하를 함께 건네줄 수 있다면 물론 당신에게도 좋은 영향이 많이 있을 것이지요."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"무용지용\" 입니다. 어딘지 모르게 체력의 부족함을 느끼는 하루입니다. 기운 없이 무기력함을 느끼게 된다면 잠시 일에서 손을 떼고 밖으로 나가는 것도 좋은 방법입니다. 새로운 공기를 마시고 머릿속에 좋은 공기를 불어넣어 준다면 답답함을 이겨낼 수 있는 좋은 계기가 될 수 있습니다. 또한 이럴 때에는 잠을 자거나 휴식을 취하기보다는 오히려 운동을 가볍게 해보는 것이 더욱 좋을 듯 하군요. 몸을 일으켜서 밖으로 나가보시기 바랍니다. 기분 전환으로 인해 오늘 하루를 무리없이 마무리 할 수 있을 겁니다."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"이럴수가\" 입니다. 마음이 다소 들떠 있는 날이니 추스르되 긴장은 푸시기 바랍니다. 너무 무리하는 것은 오히려 당신에게 이로울 수 없는 것입니다. 또한 당신이 원하는 만큼의 목표에 가까워왔다고 하여 마음을 놓아버리거나 쉽게 생각하는 태도로 좋지 않습니다. 끝까지 마무리할 수 있도록 최선을 노력을 다하는 것이 좋고 마음을 좀 더 여유롭게 가지고 행동하는 것이 필요하겠습니다. 또한 그저 평소에 해왔던 것과 같이 행동하면 어려울 것이 없는 날이니 눈앞에 놓인 것에 충실해 보시기 바랍니다."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"감지덕지\" 입니다. 밝게 웃는 자신의 모습을 보며 산뜻한 느낌을 받을 수 있는 날입니다. 당신 주변의 사람들도 이것은 마찬가지일 것이지요. 조금은 새로운 마음을 가지고 사람들을 대해 보십시오. 사람들도 당신으로 인해 기분이 좋아지는 것을 느낄 수 있고 그런 마음을 베푼 당신은 오히려 더 행복해 질 수 있는 것입니다. 혼자서 살수 없는 세상인 만큼 서로간의 조화를 이루는 것이 중요한 것은 당연합니다. 처음 만나는 사람에게도 좋은 인상을 남길 수 있을 것이니 인간 관계의 폭이 확대되는 날이 될 것입니다."}
]

prompt5 = [
    {"role": "system", "content": "꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. '이 꿈은'으로 시작해주고, mbti에 대한 언급은 직접적으로 하지 말아줘. max_length=180, json format"},
    {"role": "user", "content": "INTP, 어젯밤 나는 처음 꿈을 꾸었다. 누군가 날 안아주는 꿈 포근한 가슴에 얼굴을 묻고 웃었다. 나 그 꿈에서 살수는 없었나"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 당신이 애틋한 정서와 친밀감에 대한 갈망을 나타내고 있을 수 있습니다. 포근한 가슴에 얼굴을 묻고 웃는 상황은 당신이 편안함과 사랑, 보호를 갈망하고 있음을 보여줍니다. 그리고 이것이 행복하고 안정적인 상태를 연상시키기도 합니다. 그러나 꿈에서 일어난 후의 물음은 당신이 현재의 생활 상황에서 이러한 감정을 찾는 데 어려움을 겪고 있음을 나타낼 수 있습니다. 당신이 그 꿈에서 살 수 없었다는 문구는 현실과 이상 사이의 괴리감을 나타낼 수 있으며, 이것은 일반적으로 현재의 생활 상황에 대한 불만족을 나타냅니다. 이 꿈은 당신에게 현재의 생활에서 원하는 감정과 상황을 찾기 위해 무엇을 할 수 있는지 고민해보라는 메시지를 전달하고 있을 수 있습니다.\", \"main_keywords\": [\"사랑\", \"편안함\", \"안정적인 상태\", \"보호\", \"현실과 이상\"]}"},
    {"role": "user", "content": "ENTJ, 난 운전하고 있었고 예람누나가 전화로 자기 도슨트 못하겠다고 얘기하고 있었는데, 옆으로 아이오닉5 한대가 ㅈㄴ빠르게 달려가더니 저 앞에가서 공중으러 날고 내려꽃혀서 터짐. 그뒤로 사람 세명이 바구니같은곳에 실려나오는데 두명은 산거같기는한데 한명이 의식이 없어"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 주변 환경 변화에 따른 불안감이나 스트레스를 나타내는 것일 수 있습니다. 운전 중인 모습은 일상생활에서의 책임감 및 부담감을 상징하며, 이로 인해 발생한 사건들은 예상치 못한 일들로 인한 충격 또는 당황스러움을 표현합니다. 특히 마지막 부분에서 등장인물들이 사망하거나 부상당하는 장면은 실제로 그런 일이 일어날 가능성보다는 그러한 두려움을 반영한다고 볼 수 있습니다. 따라서 이 꿈은 당신이 최근 들어 직면하게 된 문제나 걱정거리 때문에 심리적 압박감을 느끼고 있다는 것을 암시하므로, 잠시 휴식을 취하면서 마음을 가다듬는 시간을 갖는 것이 필요하다는 조언을 담고 있다고 해석될 수 있습니다.\", \"main_keywords\": [\"예상치 못한 일\", \"심리적 압박감\", \"휴식\"]}"},
    {"role": "user", "content": "ISFP, 전남친한테 카톡 차단 해제 당해서 카톡 프로필 볼려고 한 순간에 다시 차단당하는 꿈꿨다 기분이 매~~~~~우 좋지않음"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 당신이 이전의 관계에 대한 해결되지 않은 감정이나 이슈들이 있을 수 있음을 나타낼 수 있습니다. 전 남자친구에게서의 카톡 차단 해제는 과거 관계의 재개나 그 관계에 대한 희망적인 기대감을 상징할 수 있습니다. 그러나 곧이어서 다시 차단되는 상황은 그 기대가 충족되지 않았음을 나타내며, 그로 인한 실망감이나 좌절감을 드러냅니다. 이 꿈은 아마도 미해결된 과거의 감정적 문제들을 처리하고, 그로부터 완전히 벗어나야 할 필요성을 나타낼 수 있습니다. 가끔은 우리의 무의식이 이러한 미해결의 문제를 꿈을 통해 우리에게 알려주려는 시도를 합니다. 이것은 이런 문제들을 정면으로 처리하고, 자신을 위해 긍정적인 방향으로 나아가기 위한 당신의 노력이 필요함을 시사하는 것일 수 있습니다.\", \"main_keywords\": [\"과거의 감정적 문제\", \"미해결의 문제\", \"긍정적인 방향\"]}"},
    {"role": "user", "content": "ESFJ, 꿈속에서 저는 계단을 계속 올랐어요. 하늘로 가는 계단을요. 그런데 오르고 오르고 오르다보면 바다가 흐르고, 섬이 떠있기도 해요."},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 당신의 삶에서의 도전과 성장, 그리고 그 과정에서 마주하는 불확실성을 반영하고 있습니다. 계단을 계속 오르는 모습은 당신이 지속적으로 개인적, 직업적 목표를 향해 노력하고 있음을 보여주며, 이는 당신의 적극적이고 긍정적인 성향을 반영합니다. 그러나 계단을 오르다가 보이는 바다와 떠있는 섬은 도전과 성장의 과정에서 마주할 수 있는 불확실성과 예상치 못한 변화를 나타내는 것일 수 있습니다. 바다는 감정의 깊이와 복잡성을, 섬은 독립성과 개성을 상징할 수 있습니다. 이 꿈은 당신이 자신의 길을 걷는 동안에도 불확실한 상황이나 감정적인 복잡성에 대처하는 능력을 가지고 있다는 것을 보여주는 것일 수 있습니다. 또한 이러한 상황을 극복하고 자신만의 섬, 즉 독립적인 자아를 찾아가는 과정을 표현하는 것일 수 있습니다.\", \"main_keywords\": [\"도전과 성장\", \"불확실성\", \"감정의 깊이와 복잡성\", \"독립성과 개성\"]}"},
    {"role": "user", "content": "INFP, 할머니댁으로 견학을 배를 타고 가는데 파도랑 바람이 심해서 도착은했지만 잠깐정도만 내릴 수 있어서 내렸더니 할머니랑 돌아가신 할아버지가 보였다 울고있는할아버지를 안고 울었다"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 당신의 대담함과 강인함을 반영하며, 그리고 그것이 어떻게 복잡하고 어려운 상황에 대처하는 데 도움이 될 수 있는지를 보여줍니다. 바다에서 큰 파도와 바람을 견디면서 배를 타고 가는 모습은, 당신이 어떤 도전이든 이겨내려는 결정력과 용기를 보여줍니다. 할머니 댁에 잠시 도착하여 할머니와 할아버지를 보는 것은, 가족이나 과거에 대한 회상이나 그리움을 나타낼 수 있습니다. 할아버지를 안고 울었다는 부분은 당신이 더 이상 무시하거나 회피할 수 없는 감정이나 상황에 직면했음을 나타낼 수 있습니다. 이것은 당신이 그 상황을 이해하고, 그것을 받아들이며, 그것을 해결하려는 노력을 보여주는 것일 수 있습니다. 이 꿈은 당신에게 직면한 상황을 받아들이고 이를 통해 성장하며, 당신의 강인함과 용기를 이용하여 어떤 도전이든 극복할 수 있음을 상기시켜 줍니다.\", \"main_keywords\": [\"대담함과 강인함\", \"복잡함\", \"회상이나 그리움\", \"극복\"]}"},
]

prompt6 = [
    {"role": "system", "content": "Translate the user's schedule into the json format (start_time, end_time, title). 월요일부터 일요일까지 한 주고, 1, 3, 5, 7, 8, 10, 12월은 31일, 4, 6, 9, 11월은 30일, 2월은 28일로 가정한다."},
    {"role": "user", "content": "local time: 2023-08-19 13:28:42 Saturday, 내일 오후 3시에 네이버 그린하우스 팀과 미팅이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-20 15:00:00\", \"end_time\": \"2023-08-20 16:00:00\", \"title\": \"네이버 그린하우스 팀 미팅\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 화요일부터 목요일 부산 해운대로 여행가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-22 00:00:00\", \"end_time\": \"2023-08-24 00:00:00\", \"title\": \"부산 해운대 여행\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 금요일 오후 2시에 용산 아이맥스에서 친구랑 영화 미션임파서블 보러 가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-25 14:00:00\", \"end_time\": \"2023-08-25 16:00:00\", \"title\": \"용산 아이맥스에서 미션 임파서블 영화 보기\"}"},
    {"role": "user", "content": "local time: 2023-08-23 13:28:42 Wednesday, 다음주 금요일 6시에 중앙도서관 앞에서 자동차 동아리 모임이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-09-01 18:00:00\", \"end_time\": \"2023-09-01 19:00:00\", \"title\": \"중앙도서관 앞에서 자동차 동아리 모임\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 다음주 토요일 8시에 친구랑 노래방 가"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-25 20:00:00\", \"end_time\": \"2023-11-25 22:00:00\", \"title\": \"친구랑 노래방 가기\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 다음주 월요일에 서현이 누나랑 데이트!!"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-20 09:00:00\", \"end_time\": \"2023-11-20 22:00:00\", \"title\": \"서현이 누나랑 데이트\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 12월 23일-25일 후쿠오카"},
    {"role": "system", "content": "{\"start_time\": \"2023-12-23 09:00:00\", \"end_time\": \"2023-12-25 22:00:00\", \"title\": \"후쿠오카 여행\"}"},
    {"role": "user", "content": "local time: 2023-11-21 15:23:26 Tuesday, 1월 1일에 서현이 누나랑 데이트"},
    {"role": "system", "content": "{\"start_time\": \"2024-01-01 09:00:00\", \"end_time\": \"2024-01-01 22:00:00\", \"title\": \"서현이 누나랑 데이트\"}"},
    {"role": "user", "content": "local time: 2023-11-24 10:21:46 Friday, 다음주 수요일부터 금요일까지 일본 여행"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-29 09:00:00\", \"end_time\": \"2023-12-01 22:00:00\", \"title\": \"일본 여행\"}"},
    {"role": "user", "content": "local time: 2023-11-27 10:07:01 Monday, 12시에 일정 등록해줘"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-27 12:00:00\", \"end_time\": \"2023-11-27 13:00:00\", \"title\": \"일정\"}"},
    {"role": "user", "content": "local time: 2023-12-24 01:05:01 Sunday, 다음주 목요일 아침 8시반에 자동차 정기점검"},
    {"role": "system", "content": "{\"start_time\": \"2023-12-28 08:30:00\", \"end_time\": \"2023-12-28 09:30:00\", \"title\": \"자동차 정기점검\"}"},
    {"role": "user", "content": "local time: 2023-12-26 11:08:01 Thursday, 다음주 금요일 저녁약속"},
    {"role": "system", "content": "{\"start_time\": \"2024-01-05 18:00:00\", \"end_time\": \"2024-01-05 19:00:00\", \"title\": \"저녁 약속\"}"},
]

prompt7 = [
    {"role": "system", "content": "Analyze the user's dreams, diary, and schedule to create a about 4000-character Concrete 'Mental State Report'. Please write korean but each title is Engilsh."},
    {"role": "system", "content": "1. mental_state 2. positives  3. negatives  4. extroverted_activities 5. introverted_activities  6. recommendations 7. statistics 8. keywords"},
    {"role": "system", "content": "Provide detailed analysis for 'Mental State'. For items 1, total summary about report and include user nickname. about 400-character" },
    {"role": "system", "content": "For item 2-3, provide some comments about the user's extroverted and introverted activities. about 300-character. main_keyword in 2-3 is phrase or word that you choose."},
    {"role": "system", "content": "For item 7, provide a list 1 detail ratio dictionary for Extroversion, Introversion and for item 8 provide 5 keywords"},
    {"role": "system", "content": "공손한 말투로 만들어주세요. follow my example json format. must fill all items."},
    {"role": "system", "content": "ex) if user nickname: 뀨뀨, return = {\"mental_state\":\"뀨뀨님의 최근 꿈과 일기는 복잡한 감정과 생각의 교차점을 보여줍니다. 꿈에서의 경쟁과 화해 시도는 일상 생활에서의 스트레스, 대인 관계의 어려움, 그리고 자신의 업적에 대한 내적인 기준과 기대를 반영하고 있습니다. 이는 뀨뀨님의 열정과 성취에 대한 갈망, 동시에 관계와 업무에서의 불안정성과 불확실성에 대한 고민을 나타냅니다.\", \"positives\": {\"comment\": \"학회 수료와 상 수상은 뀨뀨님의 성취감을 대표하는 중요한 사건입니다. 남자친구와의 즐거운 시간, 동료들과의 식사는 일상 속에서 즐거움과 안정감을 제공합니다. 이러한 순간들은 뀨뀨님의 긍정적인 에너지를 증폭시키며, 성공과 행복을 추구하는 데 동기를 부여합니다. \", \"main_keyword\": \"성취감과 행복\"}, \"negatives\": {\"comment\": \"일상에서 느끼는 지루함과 스트레스, 내적 갈등이 뀨뀨님의 정신적 부담을 가중시키고 있습니다. 특히, 싫어하는 사람과의 관계에서 느끼는 스트레스와 업무에서의 난감함이 부각됩니다. 이러한 부담감은 뀨뀨님의 삶에서 균형을 찾는 데 방해가 될 수 있습니다.\", \"main_keyword\": \"스트레스와 불안정성\"}, \"extroverted_activities\": [\"동료들과의 저녁식사\", \"남자친구와의 데이트\", \"가족, 친구들과의 저녁 약속\"], \"introverted_activities\": [\"독서실에서의 개별 작업\", \"일기 쓰기\", \"학회에서의 성취\"], \"recommendations\": [\"스트레스 관리를 위한 취미 활동 찾기\", \"자기계발 및 경력 계획 세우기\", \"대인 관계에서의 긴장 완화를 위한 커뮤니케이션 기술 향상\", \"규칙적인 수면 스케줄 유지\", \"필요시 전문가의 상담 고려\"], \"statistics\": {\"extrovert\": 60, \"introvert\": 40}, \"keywords\": [\"성취감\", \"행복\", \"스트레스\", \"불안정성\", \"자기 성찰\"]}"},
]

prompt8 = [
    {"role": "system", "content": "Analyze the user's memo and create json format of the memo. please write korean and return only json format, fill all the contents."},
    {"role": "system", "content": "{\"title\": \"메모에 대한 제목 생성\", \"tags\":[\"??\", \"??\"]}"},
    {"role": "user", "content": "곽서준, 01046306320"},
    {"role": "system", "content": "{\"title\": \"곽서준님의 전화번호\", \"tags\":[\"곽서준\", \"전화번호\"]}"},
    {"role": "user", "content": "컴퓨터 구조 책 다 읽고 정리하기"},
    {"role": "system", "content": "{\"title\": \"해야될 일\", \"tags\":[\"컴퓨터 구조\", \"책\", \"정리\"]}"},
    {"role": "user", "content": "title = 아이유(IU)의 킬링보이스를 라이브로! - 하루 끝, 너의 의미, 스물셋, 밤편지, 팔레트, 가을 아침, 삐삐, Blueming, 에잇, Coin, 라일락 ㅣ 딩고뮤직 - YouTube, content = https://www.youtube.com/watch?v=wDfqXR_5yyQ"},
    {"role": "system", "content": "{\"title\": \아이유(IU)의 킬링보이스를 라이브로!\", \"tags\": [\"아이유\", \"킬링보이스\", \"라이브\", \"딩고 뮤직\", \"유튜브 링크\"]}"},
    {"role": "user", "content": "애덤 그랜트 오리지널스"},
    {"role": "system", "content": "{\"title\": \"읽을 책\", \"tags\": [\"애덤 그랜트\", \"오리지널스\"]}"},
    {"role": "user", "content": "안녕"},
    {"role": "system", "content": "{\"title\": \"안녕\", \"tags\": [\"안녕\"]}"},
    {"role": "user", "content": "《기브앤테이크》\n느낌이 아닌 생각에 감정이입하라~\n정에 이끌린 감정이입 ※호구로 전락\n"},
    {"role": "system", "content": "{\"title\": \"《기브앤테이크》\", \"tags\": [\"감정이입\", \"생각\", \"감정\", \"호구\"]}"},
]

prompt9 = [
    {"role": "system", "content": "create date's title. please write only korean, and return only title. if cant find title, return same content."},
    {"role": "user", "content": "크리솔 10기 팀원들과 회식"},
    {"role": "system", "content": "회식"},
    {"role": "user", "content": "1주년 기념 데이트"},
    {"role": "system", "content": "데이트"},
    {"role": "user", "content": "이대 엄주용 졸업 연주회"},
    {"role": "system", "content": "연주회"},
    {"role": "user", "content": "학생 연구센터에서 빌린 자료 반납"},
    {"role": "system", "content": "자료 반납"},
    {"role": "user", "content": "컴퓨터 구조 책 다 읽고 정리하기"},
    {"role": "system", "content": "책 내용 정리하기"},
    {"role": "user", "content": "테스트"},
    {"role": "system", "content": "테스트"},
    {"role": "user", "content": "하루단백바 치즈베리맛 또는 솔직단백 쿠키앤크림맛"},
    {"role": "system", "content": "식단"},
]

prompt10 = [
    {"role": "system", "content": "사용자의 일기에 대한 답장을 해줘. json format"},
    {"role": "user", "content": "학원갔다왔다. 나때문에 크리스마스 당일에 집에있는 관규한테 미안하기도하고 동시에 학교에서 친구들이랑 있는 관규가 부럽기도했다. 어제 같이 술먹고 어어엄청 취했는데 난 오늘 7시에 일어나고 관규는 하루종일 자고 일찍 집와서 낮잠까지 잤다. 부럽기도하고 얄밉기도한데 이런 감정을 느끼는게 미안하기도하다. 어떤 시험이든 수험생이된다는건 참 사람을  작아지게 만드는 것 같다. 오늘 김인배변리사님의 강의를 듣다가 들은 말이 기억난다. 비록 공부가 미흡하더라도 운좋게 붙겠다는 마음가짐으로라도 마지막까지 포기하지말라는 말.. 두달 열심히 달리자"},
    {"role": "system", "content": "{\"reply\": \"학원 다녀오신 것과 시험 준비로 바쁜 나날을 보내고 계시는군요. 친구 관규에 대한 복잡한 감정들도 매우 이해가 갑니다. 크리스마스에 친구가 휴식을 취하는 동안 학원에 가야 하는 상황이 당연히 부러움과 어느 정도의 애증을 불러일으킬 수 있어요. 하지만, 이런 감정은 자연스러운 것입니다. 누구나 자신과 다른 상황에 처한 사람들을 보며 다양한 감정을 느끼기 마련이니까요. 시험 준비는 정말 힘든 과정이지만, 김인배 변리사님의 말씀처럼, 끝까지 포기하지 않는 태도가 중요합니다. 비록 공부가 완벽하지 않더라도, 긍정적인 마음가짐으로 최선을 다하면 예상치 못한 좋은 결과를 얻을 수 있습니다. 남은 두 달 동안 열심히 달리시면서도 자신을 너무 몰아세우지 말고, 적절한 휴식과 자기 관리를 잊지 마세요. 당신의 노력과 인내가 좋은 결과로 이어지기를 진심으로 바랍니다!\", \"main_keywords\": [\"중요한건 꺾이지 않는 마음\", \"힘들어도 괜찮아\", \"휴식도 필요해\", \"자기 관리\"]}"},
    {"role": "user", "content": "2023년의 시작! 해돋이를 보러 갔다. 무려 밤새 버스를 타고 정동진으로 이동하는 루트! 괴로웠던 것은 뒤의 남자의 코골이 소리가 정말 심각하게 커서 내가 2022년의 마지막 날에 남의 코골이에 이렇게 고통스러워야 하나.. 라는 회의감도 들긴 했다. 하지만, 결과적으로는 눈부시게 올라오는 23년 첫 해를 맞이했고, 새롭게 다가올 나날들에 대한 다짐을 한 날이었다!"},
    {"role": "system", "content": "{\"reply\": \"새해 첫날을 멋진 해돋이와 함께 시작하셨군요! 밤새 버스를 타고 정동진까지 가는 긴 여정과 남의 코골이 소리에 시달리는 것은 분명 쉽지 않은 경험이었겠지만, 그럼에도 불구하고 2023년의 첫 해를 눈부시게 맞이한 것은 정말 특별한 경험이었을 것 같습니다. 그런 힘든 상황 속에서도 새로운 해의 시작을 감상하고, 새해에 대한 다짐을 하는 것은 매우 의미 있는 일입니다. 이런 경험들이 새해에 대한 여러분의 기대와 희망을 더욱 강하게 만들어 줄 것 같아요. 이 새해가 여러분에게 행복과 성취가 가득한 한 해가 되기를 진심으로 바랍니다. 새로운 시작에 힘찬 발걸음을 내딛으시길 기원합니다!\", \"main_keywords\": [\"새해 다짐\", \"좋은 일들이 많이 일어나길\", \"행복한 한 해\", \"힘찬 발걸음\"]}"},
    {"role": "user", "content": "오늘 코로나 걸렸다 ㅋ 나진짜 억울하다 사실 안억울할지도? 면역력 떨어져있는데 그렇게 싸돌아다녔으니ㅜㅠㅠㅠ엄마가 또 고생이다.. 나는야 불효녀.., 인생~ 슬프다 슬퍼 내일 고모부랑 고모 오셔서 양고기 먹는다그랬는데 너무 기대했는데. 아쉽다ㅠㅠ 하ㅜㅜㅜㅠㅠ"},
    {"role": "system", "content": "{\"reply\": \"코로나19에 걸리셨다니, 정말 힘든 상황이네요. 건강이 약해져 있을 때 바깥 활동을 하다가 아프게 되는 것은 정말 불행한 일입니다. 이런 상황에서 엄마가 걱정하시는 것도 이해가 되고, 자신을 불효녀라고 생각하시는 마음도 충분히 이해할 수 있어요. 하지만, 병에 걸리는 것은 누구에게나 일어날 수 있는 일이고, 잘못이나 부끄러운 일이 아닙니다. 지금은 몸과 마음을 잘 돌보며 빨리 회복하는 것이 가장 중요해요. 고모부와 고모와의 양고기 식사를 기대했던 것도 안타까운 일이지만, 건강이 회복된 후에 더 좋은 시간을 보낼 수 있을 거예요. 자신을 탓하지 말고, 이 시간을 통해 몸과 마음의 휴식을 취하는 것도 중요합니다. 무엇보다 건강이 최우선이니, 충분한 휴식을 취하시고, 빠른 쾌유를 기원합니다. 앞으로 더 좋은 날들이 기다리고 있을 거예요!\", \"main_keywords\": [\"양고기 식사\", \"건강이 최우선\", \"빠른 쾌유\", \"휴식을 취하는 것도 중요\"]}"},
    {"role": "user", "content": "오늘 당근마켓 개발자랑 개발자 미팅을 했다. 많은 인사이트도 얻고 동기부여도 얻었다. 빨리 훌륭한 개발자로 성장해서 돈 엄청 많이 벌고 싶다.. ㅎㅎ"},
    {"role": "system", "content": "{\"reply\": \"오늘 당근마켓 개발자분과의 미팅이 매우 유익하고 영감을 주는 시간이었던 것 같네요! 인사이트와 동기부여를 얻을 수 있는 만남은 정말 값진 경험입니다. 이런 만남은 여러분의 전문성을 더욱 키우고, 목표에 한 걸음 더 다가서게 하는 소중한 기회가 되죠. 훌륭한 개발자로 성장하여 많은 돈을 벌고 싶다는 꿈은 훌륭한 목표입니다. 그 꿈을 향해 열심히 노력하고 계신 당신의 모습이 정말 멋집니다. 열정과 노력으로 목표를 향해 나아가는 과정 자체가 이미 여러분을 성공으로 이끌고 있는 것입니다. 앞으로도 계속해서 자신의 꿈과 목표를 향해 나아가시길 응원하겠습니다. 훌륭한 개발자로 성장하시는 여정이 계속해서 보람차고 성공적이기를 바랍니다!\", \"main_keywords\": [\"훌륭한 개발자로 성장\", \"훌륭한 목표\", \"열정과 노력\", \"당신 근처의 마켓\"]}"},
]

class GPTService:
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db

    async def api_log(self, request_type: str, request_token: int, response_token: int, response_time_ms: int, model: str, user_id: int, db: Session):
        api_request_log = ApiRequestLog(
            request_type=request_type,
            request_token=request_token,
            response_token=response_token,
            response_time_ms=response_time_ms,
            model=model,
            is_success=True,
            create_date=await time_now(),
            User_id=user_id
        )
        save_db(api_request_log, db)

    async def send_gpt_request(self, prompt_num: int, messages_prompt: str, retries=3):

        prompt_dict = {
            1: (prompt1, "텍스트 분류", "gpt-4-1106-preview", None),
            2: (prompt2, "제목", "gpt-3.5-turbo", None),
            3: (prompt3, "이미지 프롬프트", "gpt-3.5-turbo", None),
            4: (prompt4, "오늘의 운세", "gpt-3.5-turbo", None),
            5: (prompt5, "해몽", "gpt-4-1106-preview", {"type": "json_object"}),
            6: (prompt6, "일정", "gpt-3.5-turbo-1106", {"type": "json_object"}),
            7: (prompt7, "한 주 돌아보기", "gpt-4-1106-preview", {"type": "json_object"}),
            8: (prompt8, "메모", "gpt-3.5-turbo-1106", {"type": "json_object"}),
            9: (prompt9, "일정 제목", "gpt-3.5-turbo", None),
            10: (prompt10, "일기 답장", "gpt-4-1106-preview", {"type": "json_object"}),
        }
        if prompt_num == 7:
            messages_prompt = messages_prompt[:1000]
        else:
            messages_prompt = messages_prompt[:300]
        if prompt_num == 1 or prompt_num == 6:
            messages_prompt = f"{datetime.datetime.now(pytz.timezone('Asia/Seoul'))}, {messages_prompt}"
        prompt = prompt_dict[prompt_num][0].copy()
        prompt.append({"role": "user", "content": messages_prompt})
        for i in range(retries):
            try:
                start_time = await time_now()
                chat = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model=prompt_dict[prompt_num][2],
                    messages=prompt,
                    response_format=prompt_dict[prompt_num][3]
                )
                end_time = await time_now()
                await self.api_log(
                    user_id=self.user.id,
                    request_type=prompt_dict[prompt_num][1],
                    request_token=chat.usage.prompt_tokens,
                    response_token=chat.usage.completion_tokens,
                    response_time_ms=int((end_time - start_time).total_seconds() * 1000),
                    model=chat.model,
                    db=self.db
                )
                return chat.choices[0].message.content
            except Exception as e:
                print(f"GPT API Error {e}")
                if i < retries - 1:
                    print(f"Retrying {i + 1} of {retries}...")
                else:
                    print("Failed to get response after maximum retries")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=4501,
                    )

    async def send_dalle_request(self, messages_prompt: str, retries=3):
        messages_prompt = messages_prompt[:300]
        for i in range(retries):
            try:
                start_time = await time_now()
                response = await asyncio.to_thread(
                    openai.Image.create,
                    model="dall-e-3",
                    prompt=messages_prompt,
                    n=1,
                    size="1024x1024",
                    response_format="url"
                )
                end_time = await time_now()
                await self.api_log(
                    user_id=self.user.id,
                    request_type="이미지 생성",
                    request_token=0,
                    response_token=0,
                    response_time_ms=int((end_time - start_time).total_seconds() * 1000),
                    model="DaLLE-3",
                    db=self.db
                )

                # 이미지 생성 프롬프트 저장
                save_promt = Prompt(
                    text=messages_prompt[:300],
                    prompt=response['data'][0]['revised_prompt'],
                )
                save_db(save_promt, self.db)

                # 클라우드 버킷에 이미지 저장
                response = await asyncio.to_thread(requests.get, response['data'][0]['url'])
                img = Image.open(BytesIO(response.content))
                img = img.resize((512, 512), Image.ANTIALIAS)

                # 유니크한 파일 이름 생성
                unique_id = uuid.uuid4()
                destination_blob_name = f"{self.user.id}/{unique_id}.png"
                bucket_name = "looi"  # 네이버 클라우드 버킷 이름

                # 이미지를 BytesIO 객체로 변환
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                # 이미지 업로드
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=destination_blob_name,
                    Body=buffer,
                    ACL='public-read'  # public 접근 가능하도록 설정
                )

                # public URL 반환
                public_url = f"{endpoint_url}/{bucket_name}/{destination_blob_name}"

                # public url 반환
                return public_url
            except Exception as e:
                print(f"DALL-E API Error{e}")
                if i < retries - 1:
                    print(f"Retrying {i + 1} of {retries}...")
                else:
                    print("Failed to get response after maximum retries")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=4505,
                    )