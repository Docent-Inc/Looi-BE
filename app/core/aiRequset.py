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

class ClovaService:
    def __init__(self):
        self._host = 'https://clovastudio.apigw.ntruss.com/testapp/v1/chat-completions/HCX-003'
        self.headers = {
            'X-NCP-CLOVASTUDIO-API-KEY': settings.NAVER_API_KEY,
            "X-NCP-APIGW-API-KEY": settings.NAVER_GATEWAY_KEY,
            'Content-Type': 'application/json; charset=utf-8',
        }
        self.completion_request = {
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 2500,
            'temperature': 0.5,
            'repeatPenalty': 5.0,
            'stopBefore': [],
            'includeAiFilters': False,
            'seed': 0
        }

    def execute(self, prompt):
        headers = self.headers
        completion_request = self.completion_request
        completion_request['messages'] = prompt
        result = requests.post(self._host, headers=headers, json=completion_request).text
        result = json.loads(result)
        message_content = result["result"]["message"]["content"]
        return message_content


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
    {"role": "system", "content": "나머지는 메모로 분류해줘. return 1, 2, 3, 4"},
    {"role": "user", "content": "엄청나게 맑고 깨끗한 낚시터에서 낚시했는데 어찌나 투명한지 물고기가 다 보이는 꿈"},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "오늘은 하루종일 코딩을 했다. 내가 만든 코드는 잘 돌아가지 않고, 너무 고통받았다. 내일은 개발을 마무리해서 얼른 서비스를 출시하고 싶다"},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "엘리스 세습 책 읽기, 56쪽"},
    {"role": "system", "content": "3"},
    {"role": "user", "content": "8월25일 저녁6시 강남 약속"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "오늘은 크리스마스다. 여자친구와 현대백화점에 가서 아웃백을 먹고 영화를 봤다. 오펜하이머를 봤는데 나는 사실 물리학과를 갔어야 될 것 같다. 너무 재미있었다."},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "다음주 금요일 6시에 중앙도서관 앞에서 자동차 동아리 모임이 있어"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "스키장에서 스키를 타고 있는데 뒤에서 곰이 갑자기 튀어나와서 도망가다가 넘어지고, 꿈에서 깼어"},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "꿈에서 어떤 길에서 있었는데 하을을 올려보니 보름달이 구름에 가려져 빛나고 있었다. 구름에 가려졌지만 밝게 빛나고 있어서 보름달이 잘 보였다. 보름달은 이내 구름 위로 솟아 올라 밝게 빛났다."},
    {"role": "system", "content": "1"},
    {"role": "user", "content": "학교에서 계속 공부를했다. 너무 힘든 하루였지만 마무리가 깔끔해서 기분좋게 잠에 잘 수 있을 것 같다. 내일은 더 열심히 해야겠다."},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "11월 20일부터 28일은 부산으로 여행갈거야"},
    {"role": "system", "content": "4"},
    {"role": "user", "content": "오늘 내역서 작업하느라 매우 바빴는데 저녁에 회를 먹어서 호다닥 달려옴"},
    {"role": "system", "content": "2"},
    {"role": "user", "content": "아침마다 파업 그만했으면 좋겠다 한놈만 걸려라 다 패버린다"},
    {"role": "system", "content": "2"},
]


prompt2 = [
    {"role": "system", "content": "Create a title for story, only title, do not other work, must follow example"},
    {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
    {"role": "system", "content": "사라진 강아지"},
    {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
    {"role": "system", "content": "비둘기와 친해지기"},
    {"role": "user", "content": "오늘은 크리스마스다. 여자친구와 현대백화점에 가서 아웃백을 먹고 영화를 봤다. 오펜하이머를 봤는데 나는 사실 물리학과를 갔어야 될 것 같다. 너무 재미있었다."},
    {"role": "system", "content": "크리스마스 데이트"},
    {"role": "user", "content": "학교에서 계속 공부를했다. 너무 힘든 하루였지만 마무리가 깔끔해서 기분좋게 잠에 잘 수 있을 것 같다. 내일은 더 열심히 해야겠다."},
    {"role": "system", "content": "깔끔한 하루"},
    {"role": "user", "content": "하늘을 떠다니는 능력이 있어서 맘을 먹으면 하늘로 둥둥 뜨는 능력을 가지고 날면서 돌아다니는 꿈을 종종 꾸어요. 하늘을 날기 위해서는 집중을 해야 가능한데 꿈속에서도 간혹 잘 되기도 하고 잘 안 되는 경우도 있는데 대부분은 집중하면 하늘을 날 수 있더라고요. 이 꿈이 어떤 의미가 있을까요??"},
    {"role": "system", "content": "하늘을 떠다니는 능력"},
    {"role": "user", "content": "개꿈을 꾸었어요 어떤 의미가 있을까요??"},
    {"role": "system", "content": "개꿈"},
    {"role": "user", "content": "높은 빌딩 내 통유리로 된 호텔 방 침대 위에 나랑 친한 지인이랑 잘 모르는 남자랑 셋이서 앉아있었어. 나랑 친한 지인이랑 대화를 하면서 난 정면에 야경이 보이는 유리창을 보고 있었는데, 갑자기 내 뒤에서 잘 모르는 남자가 날 끌어안은 거야. 당황해서 가만히 있었는데, 내 이상형이랑 정반대인 남자였지만 엄청 설레어했던 내용이었어."},
    {"role": "system", "content": "의문의 이상형"},
    {"role": "user", "content": "비행기나 기차를 놓치는 꿈"},
    {"role": "system", "content": "잃어버린 시간"},
    {"role": "user", "content": "누군가를 죽이는 꿈"},
    {"role": "system", "content": "죽음의 예감"},
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
    {"role": "system", "content": "꿈을 mbti맞춤 해몽 해주고, mbti에 대한 언급은 직접적으로 하지 말아줘. json format, must follow my example(format and length), incloude emoji"},
    {"role": "user", "content": "nickname: 뀨뀨, mbti: INTP, dream: 어젯밤 나는 처음 꿈을 꾸었다. 누군가 날 안아주는 꿈 포근한 가슴에 얼굴을 묻고 웃었다. 나 그 꿈에서 살수는 없었나"},
    {"role": "system", "content": "{\"resolution\":\"뀨뀨님, 어젯밤 꾸신 꿈은 마음속 깊은 곳에서 따뜻함과 안정을 찾고자 하는 욕구를 반영하는 것 같아요. 누군가에게 안겨 포근한 가슴에 얼굴을 묻고 웃는 장면은 현재 삶에서 보호와 이해를 갈망하고 있음을 나타내요. 이러한 꿈은 종종 우리가 일상에서 놓치기 쉬운 감정적 만족과 안정감을 찾고자 하는 마음을 드러내죠. 💫 꿈에서 느낀 행복과 평온은 삶 속에서도 이러한 감정을 찾고 경험할 수 있다는 희망의 메시지일지도 모릅니다. 마음의 소리에 귀 기울이며, 그 따뜻함을 현실에서도 찾아보세요. 🌼\", \"main_keywords\": [\"사랑\", \"편안함\", \"안정적인 상태\", \"보호\", \"현실과 이상\"]}"},
    {"role": "user", "content": "nickname: 태완, mbti: ENTJ, dream: 난 운전하고 있었고 예람누나가 전화로 자기 도슨트 못하겠다고 얘기하고 있었는데, 옆으로 아이오닉5 한대가 ㅈㄴ빠르게 달려가더니 저 앞에가서 공중으러 날고 내려꽃혀서 터짐. 그뒤로 사람 세명이 바구니같은곳에 실려나오는데 두명은 산거같기는한데 한명이 의식이 없어"},
    {"role": "system", "content": "{\"resolution\":\"태완님, 이 꿈은 일상의 책임감과 예상치 못한 변화로 인한 스트레스를 나타내는 것 같아요. 🚘 운전하는 상황은 태완님의 삶에서의 역할과 책임을 상징하고, 사고 장면은 불안정한 상황에 대한 두려움을 드러내요. 🤞사람들이 구조되는 모습은 어려운 상황 속에서도 회복과 희망을 찾을 수 있다는 메시지를 전달하고 있어요. 이 꿈은 현재의 부담감과 스트레스에 대한 반응으로, 잠시 휴식을 취하며 마음의 안정을 찾는 것이 어떨까요?\", \"main_keywords\": [\"예상치 못한 일\", \"심리적 압박감\", \"휴식\"]}"},
    {"role": "user", "content": "nickname: 서준, mbti: ISFP, dream: 전남친한테 카톡 차단 해제 당해서 카톡 프로필 볼려고 한 순간에 다시 차단당하는 꿈꿨다 기분이 매~~~~~우 좋지않음"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 과거 관계에 대한 미련이나 현재의 갈등된 감정 상태를 반영하고 있을 수 있어요. 😥 전남친에게 카톡 차단 해제 후 다시 차단당하는 상황은 서준님의 내면에서 불확실성과 예기치 못한 변화에 대한 두려움을 상징해요. 이는 서준님의 마음속에 아직 해결되지 않은 감정이나 그 관계에 대한 미련을 드러내는 것일 수 있어요. 꿈에서 느낀 불쾌함과 불안은, 이러한 감정들을 잘 이해하고 해결하려는 내면의 시도를 나타내는 것일지도 몰라요. 🤔 이 꿈을 통해 서준님은 과거의 관계를 정리하고 현재의 감정을 잘 다루어 나가는 것은 어떨까요?\", \"main_keywords\": [\"과거의 감정적 문제\", \"미해결의 문제\", \"긍정적인 방향\", \"불쾌함과 불안\"]}"},
    {"role": "user", "content": "nickname: 소망, mbti: ESFJ, dream: 꿈속에서 저는 계단을 계속 올랐어요. 하늘로 가는 계단을요. 그런데 오르고 오르고 오르다보면 바다가 흐르고, 섬이 떠있기도 해요."},
    {"role": "system", "content": "{\"resolution\":\"소망님, 꿈속에서 하늘로 향하는 계단을 오르는 꿈은 삶에서 높은 목표나 이상을 향한 여정을 상징할 수 있어요. 🪜 계단을 오르는 과정은 목표 달성을 향한 꾸준한 노력과 진전을 나타내며, 도중에 보이는 바다와 떠 있는 섬은 삶의 여정에서 만나는 예기치 못한 변화와 새로운 기회를 상징해요. 🌊 바다는 무한한 가능성을 의미하며, 섬은 새로운 발견과 모험을 나타내요. 이 꿈은 소망님이 삶에서 끊임없이 나아가며 새로운 가능성을 탐색하는 과정에 있다는 것을 보여주는 것 같아요. 계속해서 앞으로 나아가며 삶의 새로운 경험과 기회를 포용하는 것이 어떨까요? 🌟\", \"main_keywords\": [\"도전과 성장\", \"불확실성\", \"감정의 깊이와 복잡성\", \"독립성과 개성\"]}"},
    {"role": "user", "content": "nickname: 은정, mbti: INFP, dream: 할머니댁으로 견학을 배를 타고 가는데 파도랑 바람이 심해서 도착은했지만 잠깐정도만 내릴 수 있어서 내렸더니 할머니랑 돌아가신 할아버지가 보였다 울고있는할아버지를 안고 울었다"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 은정님이 현재 겪고 있는 삶의 도전과 감정적인 문제들을 반영하는 것 같아요. 🌊 배를 타고 견학을 가는 과정에서의 파도와 바람은 삶의 어려움과 장애물을 상징해요. 할머니와 돌아가신 할아버지를 만나는 장면은 가족에 대한 그리움과 상실감을 나타내며, 은정님의 감정적인 안정과 지지를 찾고자 하는 마음을 드러내요. 😭 할아버지를 안고 우는 모습은 은정님 내면의 깊은 감정과 대면하는 것을 보여주며, 이는 삶에서 감정적 균형과 치유를 추구하는 과정을 나타낼 수 있어요.\", \"main_keywords\": [\"삶의 도전\", \"장애물\", \"감정적 균형과 치유\", \"파도와 바람\"]}"},
    {"role": "user", "content": "nickname: 서현, mbti: ISTJ, dream: 합숙시설인데 넓은 공용화장실에 위생이 불량했다. 좌변기에 앉고 싶어도 바닥에 똥이 조금씩 남아있어서 똥을 피해 다섯 번째 좌변기에 앉아 볼일을 봤다."},
    {"role": "system", "content": "{\"resolution\":\"서현님, 이 꿈은 현재 직면하고 있는 상황에 대한 서현님의 감정적 반응을 반영하는 것 같아요. 🏩 합숙시설에서의 불청결한 상황은 서현님이 직면한 상황이나 공동체에 대한 부정적인 인식을 나타낼 수 있어요. 즉, 통제할 수 없는 상황이나 다루기 힘든 문제의 상징일 수 있어요. 😣 똥을 피해 다섯 번째 좌변기에 앉는 부분은 문제를 해결하려는 태완님의 전략적 사고를 보여줘요. 볼일을 봄으로써 문제 해결을 시도하는 서현님의 모습은 앞으로 어려운 상황에도 체계적이고 전략적인 사고로 해결책을 찾아갈 것을 암시해요. 💡\", \"main_keywords\": [\"체계적인 사고\", \"문제 해결\", \"대처 능력\", \"부정적인 상황\"]}"},
]

prompt6 = [
    {"role": "system", "content": "Translate the user's schedule into the json format (start_time, end_time, title). 월요일부터 일요일까지 한 주고, 1, 3, 5, 7, 8, 10, 12월은 31일, 4, 6, 9, 11월은 30일, 2월은 28일로 가정한다."},
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
    {"role": "user", "content": "local time: 2024-01-02 11:01:23 Thursday, 목요일에 저녁약속 있어"},
    {"role": "system", "content": "{\"start_time\": \"2024-01-04 18:00:00\", \"end_time\": \"2024-01-04 19:00:00\", \"title\": \"저녁 약속\"}"},
]

prompt7 = [
    {"role": "system", "content": "Analyze the user's diary and schedule to create '마음 상태 보고서'. Please write korean but each title is Engilsh. json format, must follow my example(format and length), 모든 문단에 이모지를 포함해줘!"},
    {"role": "system", "content": "{\"positives\": {\"comment\": \"2024년의 밝은 시작, 가족과 보낸 시간, 그리고 새로운 학습 목표에 대한 열정은 태완님에게 큰 행복과 만족감을 안겨주고 있습니다.🚀 이러한 순간들이 태완님의 삶을 더욱 풍요롭게 하며, 매일을 의미 있고 긍정적으로 만들어가는 데 기여하고 있어요. 태완님, 매 순간을 소중히 여기며 성장해 나가는 여정이 정말로 감동적입니다. 계속해서 이 길을 걸으며 더 많은 성취를 이루시길 응원합니다!🌟\", \"main_keyword\": \"긍정적 성장과 도전\"}, \"negatives\": {\"comment\": \"일상의 분주함과 새로운 시작의 부담감이 태완님을 압박할 수 있습니다. 이 중 상담 약속, 건강 관리, 그리고 새로운 목표에 대한 노력은 때로는 많은 에너지를 요구하죠. ⚡️이러한 도전들이 가끔은 벅찰 수 있음에도, 태완님은 이를 긍정적인 방향으로 이끌고자 하는 강한 의지를 보여주고 있어요. 태완님, 어려움을 마주할 때마다 여러분의 노력과 헌신이 결국에는 큰 성장으로 이어질 것임을 믿습니다. 언제나 태완님의 편에서 응원할게요.📣\", \"main_keyword\": \"도전의 부담과 극복\"}, \"recommendations\": [\"새로운 학습 목표를 설정할 때는 현실적이고 달성 가능한 목표를 세우세요. 🎯\", \"가족과의 시간을 소중히 하며, 이를 통해 받은 긍정적인 에너지를 일상에 적극적으로 활용하세요. ❤️\", \"바쁜 일상 속에서도 자기 관리에 시간을 할애하여, 정신적, 신체적 건강을 돌보세요. 🥗\", \"새로운 도전에 직면했을 때는 스트레스 관리 방법을 찾아 실천하며, 필요하다면 친구나 가족, 전문가와 대화를 나누세요. 🗣️\", \"자신이 세운 목표를 위해 꾸준히 노력하되, 과정을 즐기려는 마음가짐을 가지세요. 🌈\"], \"keywords\": [\"새해 목표\", \"가족과 시간\", \"자기 관리\", \"긍정적 도전\", \"스트레스 관리\"], \"personal_questions\": [\"새로 시작한 영어 공부를 재밌게 하고 계신가요? 📚\", \"가족과 보낸 시간이 여러분에게 어떤 긍정적인 영향을 주었나요? 👨‍👩‍👧‍👦\", \"바쁜 일상 속에서도 어떻게 자기 관리에 시간을 할애하고 계신가요? 🧘‍♂️\", \"새해의 목표를 세우며 가진 기대감과 그 목표를 향한 계획은 무엇인가요? 🎯\", \"도전을 겪으며 느낀 가장 큰 교훈은 무엇이었나요? 🤔\"]}"},
    {"role": "system", "content": "{\"positives\":{\"comment\": \"업무에서의 성공적 해결책 찾기, 가족과의 시간, 그리고 운동을 통한 신체 건강의 개선은 소망님에게 큰 성취감을 가져다주었어요. 이러한 순간들은 소망님에게 새로운 에너지를 주며, 어려움을 극복할 수 있는 힘을 실어주고 있습니다.👏 소망님, 이렇게 스스로를 돌보며 긍정적인 변화를 만들어가는 모습이 매우 인상적입니다. 앞으로도 계속해서 좋은 일들이 일어나길 바랍니다! 🌟\",\"main_keyword\":\"회복력과 성취\"},\"negatives\":{\"comment\":\"업무 스트레스와 사업의 불확실성, 대인 관계에서의 갈등은 소망님을 상당히 힘들게 하고 있어요. 이러한 상황들이 소망님의 마음에 큰 무게를 더하고 있지만, 소망님은 이를 극복하기 위해 끊임없이 노력하고 있습니다.💪 소망님, 이런 어려운 시기를 겪으시는 것을 보며 깊은 위로와 격려의 말씀을 드리고 싶어요. 소망님의 노력과 강인함이 결국 모든 어려움을 이겨낼 것입니다. 🤗\",\"main_keyword\":\"스트레스와 회복\"},\"recommendations\":[\"업무 스트레스를 줄이기 위해 업무 시간과 휴식 시간을 명확히 구분하고, 일정 관리를 철저히 하세요. 📅\",\"사업과 관련된 도전에 직면했을 때, 전략적으로 문제를 해결할 수 있는 방안을 모색하세요. 💡\",\"대인 관계에서의 갈등을 해소하기 위해 의사소통 기술을 개선하고, 상호 이해를 도모할 수 있는 기회를 마련하세요. 🤝\",\"정신적, 신체적 건강을 위해 규칙적인 운동과 취미 생활을 유지하세요. 🏋️‍♂️\",\"스트레스가 과도하게 쌓였을 때는 전문가의 도움을 받는 것을 고려하세요. 👩‍⚕️\"],\"keywords\":[\"업무 스트레스\",\"사업 도전\",\"대인 관계\",\"회복력\",\"자기 관리\"],\"personal_questions\":[\"업무와 사업에서의 스트레스를 관리하기 위해 어떤 전략을 사용하고 계신가요? 🤔\",\"가족과의 시간이나 운동이 일상에 어떤 긍정적인 영향을 주었나요? 👨‍👩‍👧‍👦\",\"사업에서의 불확실성을 어떻게 극복하려고 하시나요? 💼\",\"대인 관계의 갈등을 해결하기 위한 노력이 있나요? 🤝\",\"정신적으로 힘든 시기를 어떻게 극복하고 계신가요? 🧘‍♂️\"}]"},
    # {"role": "system", "content": "{\"positives\": {\"comment\": \"최근 금전 문제 해결, 리쿠르팅 면담의 성공, 그리고 친구들과의 만남이 큰 성취감과 행복을 가져다주었어요. 🎉이런 경험들이 긍정적인 영향을 주며, 앞으로의 성공을 위한 기반을 마련했네요. 서준님, 자신에게 좋은 영향을 주기 위한 노력이 정말 멋져요. 👏\", \"main_keyword\": \"성취감과 행복\"}, \"negatives\": {\"comment\": \"현재 서준님의 일기에서는 부정적인 상황이 거의 언급되지 않아요. 😄 이는 긍정적인 사건들에 집중하고 계시다는 뜻이겠죠. 일상에서 마주치는 작은 도전들도 있겠지만, 현재 서준님은 매우 긍정적인 상태로 보여요.🙌\", \"main_keyword\": \"긍정적 변화\"}, \"recommendations\": [\"금전 문제 해결 경험을 바탕으로 재정 계획을 재검토하고, 예산 관리 방법을 개선해 보세요. 💰\", \"탁구 실력을 키울 수 있는 정기 연습 일정을 만들거나, 탁구 클럽에 가입해 보세요. 🏓\", \"하루와 함께 새로운 산책 코스를 탐색하거나, 함께할 수 있는 야외 활동을 찾아보세요. 🚶‍♂️🌳\", \"리쿠르팅 면담의 성공 경험을 분석하여 효율적인 리쿠르팅 전략을 세우세요. 💼\", \"동호회 활동을 통해 얻은 긍정적 에너지로 사회적 관계를 더 발전시켜 보세요. 🤝\"], \"keywords\": [\"성취감\", \"행복\", \"긍정적 에너지\", \"사회적 관계\", \"목표 설정\"], \"personal_questions\": [\"재정 계획을 세우고 난 후, 어떤 변화를 느꼈나요? 🤔\", \"탁구 연습을 통해 어떤 목표를 세우고 싶나요? 🏆\", \"하루와의 산책이나 야외 활동에서 특별한 순간이 있었나요? 🌄\", \"리쿠르팅 전략을 적용해 본 결과 어떤 점이 효과적이었나요? 📊\", \"사회적 관계를 확장하기 위해 시도한 새로운 활동이 있나요? 🤗\"]}"},
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
    {"role": "system", "content": "일기에 대한 답장을 해줘. json format, must follow my example"},
    {"role": "user", "content": "nickname: 서준, diary: 학원갔다왔다. 나때문에 크리스마스 당일에 집에있는 관규한테 미안하기도하고 동시에 학교에서 친구들이랑 있는 관규가 부럽기도했다. 어제 같이 술먹고 어어엄청 취했는데 난 오늘 7시에 일어나고 관규는 하루종일 자고 일찍 집와서 낮잠까지 잤다. 부럽기도하고 얄밉기도한데 이런 감정을 느끼는게 미안하기도하다. 어떤 시험이든 수험생이된다는건 참 사람을  작아지게 만드는 것 같다. 오늘 김인배변리사님의 강의를 듣다가 들은 말이 기억난다. 비록 공부가 미흡하더라도 운좋게 붙겠다는 마음가짐으로라도 마지막까지 포기하지말라는 말.. 두달 열심히 달리자"},
    {"role": "system", "content": "{\"reply\": \"서준님, 크리스마스에 학원 가시느라 정말 수고하셨어요. 🎄 관규와의 상황, 친구들과의 시간이 부럽고 미안한 감정이 드는 건 자연스러워요. 감정에 솔직해져도 괜찮아요. 🤗 시험 준비의 부담감이 클 테지만, 끝까지 포기하지 않는 건 중요해요. 김인배 변리사님의 조언을 기억하세요. 남은 두 달 동안 서준님을 돌보면서 최선을 다하세요. 💪 어떤 고민이든, 언제든지 이야기해 주세요. 항상 여기 있을게요. 내일의 이야기도 기대하고 있어요! 🌟\", \"main_keywords\": [\"중요한건 꺾이지 않는 마음\", \"힘들어도 괜찮아\", \"휴식도 필요해\", \"자기 관리\"]}"},
    {"role": "user", "content": "nickname: 소망, diary: 2023년의 시작! 해돋이를 보러 갔다. 무려 밤새 버스를 타고 정동진으로 이동하는 루트! 괴로웠던 것은 뒤의 남자의 코골이 소리가 정말 심각하게 커서 내가 2022년의 마지막 날에 남의 코골이에 이렇게 고통스러워야 하나.. 라는 회의감도 들긴 했다. 하지만, 결과적으로는 눈부시게 올라오는 23년 첫 해를 맞이했고, 새롭게 다가올 나날들에 대한 다짐을 한 날이었다!"},
    {"role": "system", "content": "{\"reply\": \"새해 첫 해돋이를 보셨군요, 멋진 시작이네요! 🌅 밤새 버스 여정과 남의 코골이는 힘들었겠지만, 2023년 첫 해를 맞이하는 순간은 정말 특별했을 거예요. 새해의 다짐을 한 것도 멋지네요. 💫 앞으로의 시간들에 대한 기대와 희망을 갖고, 언제든지 고민이 있으면 말씀해 주세요. 소망님의 내일을 기다리며, 항상 지지하고 있을게요! 🌟\", \"main_keywords\": [\"새해 다짐\", \"좋은 일들이 많이 일어나길\", \"행복한 한 해\", \"힘찬 발걸음\"]}"},
    {"role": "user", "content": "nickname: 뀨뀨, diary: 오늘 코로나 걸렸다 ㅋ 나진짜 억울하다 사실 안억울할지도? 면역력 떨어져있는데 그렇게 싸돌아다녔으니ㅜㅠㅠㅠ엄마가 또 고생이다.. 나는야 불효녀.., 인생~ 슬프다 슬퍼 내일 고모부랑 고모 오셔서 양고기 먹는다그랬는데 너무 기대했는데. 아쉽다ㅠㅠ 하ㅜㅜㅜㅠㅠ"},
    {"role": "system", "content": "{\"reply\": \"코로나로 힘드시겠어요. 🤒 지금은 몸과 마음을 잘 돌보는 것이 중요해요. 엄마가 걱정하시는 것도 당연하고, 스스로를 불효녀라고 생각하시는 것도 이해돼요. 하지만, 병에 걸리는 것은 뀨뀨님 잘못이 아니에요. 건강 회복에 집중하시고, 고모부, 고모와의 양고기 식사는 다음 기회에 즐기시길 바래요. 빠른 쾌유를 기원하며, 힘내세요! 🌷\", \"main_keywords\": [\"양고기 식사\", \"건강이 최우선\", \"빠른 쾌유\", \"휴식을 취하는 것도 중요\"]}"},
    {"role": "user", "content": "nickname: 태완, diary: 오늘 당근마켓 개발자랑 개발자 미팅을 했다. 많은 인사이트도 얻고 동기부여도 얻었다. 빨리 훌륭한 개발자로 성장해서 돈 엄청 많이 벌고 싶다.. ㅎㅎ"},
    {"role": "system", "content": "{\"reply\": \"당근마켓 개발자와의 미팅이 유익한 시간이었군요! 인사이트와 동기부여를 얻은 것은 정말 좋은 경험입니다. 훌륭한 개발자로 성장하고 싶다는 태완님의 꿈을 응원해요. 💪 이 여정의 모든 순간들을 일기로 기록하며, 태완님의 성장을 함께 나누고 싶어요. 앞으로도 계속 훌륭한 개발자로 성장하실 것을 기대하며 응원할게요! 🌟\", \"main_keywords\": [\"훌륭한 개발자로 성장\", \"훌륭한 목표\", \"열정과 노력\", \"당신 근처의 마켓\"]}"},
]

prompt11 = [
    {"role": "system", "content": "create a question for the user's diary. please write only korean, and return only question, includ imoji."},
    {"role": "user", "content": "[태완], [곽대표님과 서비스 관련 미팅}, [디캠프 6시]"},
    {"role": "system", "content": "오늘 미팅에서 가장 인상 깊었던 순간은 무엇이었고, 그 순간이 태완님에게 어떤 의미를 가졌나요? 🌟"},
    {"role": "user", "content": "[서준], [강원도청 방문 (정보화 정책과, 감사원 회의)], [강원도청 오전에 방문(정보화 정책과. 감사워원회)]"},
    {"role": "system", "content": "강원도청에 잘 다녀오셨나요? 강원도청에서의 회의에서 특별한 순간이 있었다면 공유해 주실 수 있을까요? 🏞️"},
    {"role": "user", "content": "[수아], [해돋이 보기], []"},
    {"role": "system", "content": "오늘 해돋이를 보면서 수아님이 하신 다짐이 있나요? 그 순간이 어떤 영감을 주었나요? 🌅"},
    {"role": "user", "content": "[화민], [홍콩 여행], [With 이해민, 이해영]"},
    {"role": "system", "content": "친구들과의 홍콩 여행은 어떠셨나요? 홍콩에서의 잊을 수 없는 경험이나 특별한 순간들에 대해 이야기해 주실 수 있나요? 🏝️"},
    {"role": "user", "content": "[지훈], [공항], [부모님 모셔다 드리기]"},
    {"role": "system", "content": "지훈님, 부모님을 공항에 잘 모셔다드리셨나요? 그 과정에서 특별한 순간이나 감정이 있었다면 공유해 주실 수 있을까요? 🛫"},
    {"role": "user", "content": "[예람], [생일선물 챙기기], [휘수형, 미주, 미즈 생일선물로 나이키양말 챙기기]"},
    {"role": "system", "content": "오늘 생일선물은 잘 전해드렸나요? 선물을 받으신 분의 반응이 어땠는지 궁금해요! 🎁"},
    {"role": "user", "content": "[지혜], [혜진이 결혼식], []"},
    {"role": "system", "content": "혜진이 결혼식에서의 특별한 순간 중, 지혜님이 가장 기억에 남는 에피소드가 있나요? 💒"},
    {"role": "user", "content": "[도유망망], [저녁 약속], []"},
    {"role": "system", "content": "오늘 저녁 약속은 어떠셨나요? 그 자리에서 특히 인상 깊었던 대화나 사건이 있었다면 공유해 주실 수 있을까요? 🍽️"},
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
            1: (prompt1, "텍스트 분류", "gpt-4-1106-preview", None), # 사용 x
            2: (prompt2, "제목", "gpt-3.5-turbo", None), # 사용 x
            3: (prompt3, "이미지 프롬프트", "gpt-3.5-turbo", None), # 사용 x
            4: (prompt4, "오늘의 운세", "gpt-3.5-turbo", None), # 사용 x
            5: (prompt5, "해몽", "gpt-4-1106-preview", {"type": "json_object"}),
            6: (prompt6, "일정", "gpt-3.5-turbo-1106", {"type": "json_object"}), # 사용 x
            7: (prompt7, "한 주 돌아보기", "gpt-4-1106-preview", {"type": "json_object"}), # HCX-003
            8: (prompt8, "메모", "gpt-3.5-turbo-1106", {"type": "json_object"}),
            9: (prompt9, "일정 제목", "gpt-3.5-turbo", None), # 사용 x
            10: (prompt10, "일기 답장", "gpt-4", None), # -1106-preview", {"type": "json_object"}),
            11: (prompt11, "일기 유도 질문 생성", "gpt-4-1106-preview", None),
        }
        if prompt_num == 7:
            messages_prompt = messages_prompt[:1500]
        else:
            messages_prompt = messages_prompt[:500]
        if prompt_num == 6:
            messages_prompt = f"{datetime.datetime.now(pytz.timezone('Asia/Seoul'))}, {messages_prompt}"
        prompt = prompt_dict[prompt_num][0].copy()
        prompt.append({"role": "user", "content": messages_prompt})
        for i in range(retries):
            try:
                start_time = await time_now()
                if prompt_num == 7:
                    # 마음 상태 보고서 HCX-003 버전으로 생성
                    cloava_service = ClovaService()
                    response = await asyncio.to_thread(
                        cloava_service.execute,
                        prompt=prompt,
                    )
                    return response
                else:
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
                return
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