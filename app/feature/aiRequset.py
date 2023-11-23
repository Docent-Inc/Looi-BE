import asyncio
import json
import openai
from fastapi import HTTPException, status
import datetime
import pytz
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import time_now
from app.db.models import ApiRequestLog, User

openai.api_key = settings.GPT_API_KEY

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

prompt1 = [
    {"role": "system", "content": "사용자의 텍스트가 꿈, 일기, 메모, 일정 중 어떤 카테고리인지 분류해서 숫자만 반환해줘. 꿈 = 1, 일기 = 2, 메모 = 3, 일정 = 4"},
    {"role": "system", "content": "내용이 짧으면 메모 또는 일정일 확률이 높고, 꿈이라는 단어가 포함되면 꿈, 오늘 내가 한 일들과 생각들이 포함되면 일기일 확률이 높다."},
    {"role": "system", "content": "날짜와 관련된 단어가 포함되면 일정일 확률이 높다."},
    {"role": "system", "content": "시간대가 오전이면 꿈일 확률이 높고 오후면 일기일 확률이 높다."},
    {"role": "system", "content": "나머지는 메모로 분류해줘."},
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
    {"role": "system", "content": "사용자의 스토리에 대한 제목을 만들어줘"},
    {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
    {"role": "system", "content": "수상한 강아지의 탈출 대작전"},
    {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
    {"role": "system", "content": "비둘기와 나의 특별한 우정"},
]

# prompt3 = [
#     {"role": "system", "content": "make just one scene a prompt for DALLE2 about this diary"},
#     {"role": "system", "content": "include the word illustration, digital art, vivid and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
#     {"role": "system", "content": "make just prompt only engilsh"},
#     {"role": "system", "content": "max_length=250"},
#     {"role": "user", "content": "학교 복도에서 친구랑 얘기하다가 갑자기 앞문쪽에서 좀비떼가 몰려와서 도망침. 근데 알고보니 우리반 애였음. 걔네 반 담임쌤한테 가서 말하니까 쌤이 괜찮다고 하심. 그래서 안심하고 있었는데 또다른 좀비가 와서 막 물어뜯음. 그러다가 깼는데 아직도 심장이 벌렁벌렁 거림.."},
#     {"role": "system", "content": "Create a vivid digital art illustration depicting a zombie apocalypse in a school hallway. Illuminate the scene with an eerie, greenish light and use a dull, muted color scheme, accentuated by splashes of blood-red. Capture the mood of shock and fear, and compose the artwork to emphasize the adrenaline-pumping chase and a sudden, terrifying zombie ambush."},
#     {"role": "user", "content": "학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다."},
#     {"role": "system", "content": "Create a digital art illustration that is vivid and lively, set during a school festival. Showcase a festival-goer receiving a tarot reading. Employ warm and inviting lighting to illuminate a vibrant and colorful scene. Convey mixed emotions of disappointment and relief on the protagonist's face as they react to their tarot reading."},
#     {"role": "user", "content": "적에게 계속 도망치면서 세상을 구할 목표를 향해 팀원들과 향해 나아간다. 모험중에서 새로운 사람도 만나며 나아가지만 결국 나 혼자서 해내야 하는 상황에 마주친다. 하지만 목표를 향한 문제 풀이 과정에서 답도 모르지만 안풀리는 상황에 놓이고 적에게 붙잡히지는 않았지만 따라잡히게 된다."},
#     {"role": "system", "content": "Create a vivid digital art illustration that captures the essence of a hero's journey. Set the scene in a fantastical world that's rich in color and illuminated by dramatic adventure lighting. The artwork should evoke feelings of determination and anxiety. Put the spotlight on the hero's solitary struggle and pursuit, as they face obstacles and enemies in their quest to save the world."},
# ]

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
    {"role": "system", "content": "꿈의 내용을 보고 오늘의 운세를 만들어줘, 꿈의 내용은 참고만 하고 직접적으로 언급하지 말아줘, 사자성어로 운세 총운을 만들어줘, 꿈의 내용이 없다면 그냥 오늘의 운세를 만들어줘, follow the format"},
    {"role": "user", "content": "ex) 나랑 친한 친구들이 다같이 모여서 놀다가 갑자기 한명씩 사라져서 마지막엔 나만 남았다. 그래서 혼자 울다가 깼다."},
    {"role": "system", "content": "ex) 오늘의 운세는 \"여어득수\" 입니다. 기대치 않았던 곳에서 큰 지원을 받게 되니 일을 더욱 잘 풀리고 몸과 마음 또한 더없이 기쁘고 편할 수 있을 것입니다. 당신에게 스트레스로 작용했던 일이 있다면 당신의 노력이 바탕이 되어 해결할 수 있는 기회도 잡을 수 있습니다. 또한 주변사람들로부터 도움이나 조언을 통해서 자신의 방향을 잡을 수도 있습니다. 그러나 자신의 의지를 잃지 않는 것도 중요한 부분입니다. 당신에게 닥친 이 기회를 잘 활용한다면 충분히 많은 성과와 발전이 있을 것이지요. 조금 더 분발하세요."},
    {"role": "user", "content": "ex) x"},
    {"role": "system", "content": "ex) 오늘의 운세는 \"박장대소\" 입니다. 좋은 운이 당신에게 많이 몰리는 날입니다. 당신이 목표하고 있는 일이 있다면 별 어려움 없이 일을 해결해 나갈 수 있을 것입니다. 또한 당신의 모든 능력이 사람들로 하여금 인정을 받을 수 있으니 당신의 운은 최상을 달리고 있습니다. 물론 당신의 노력이 함께 해야지만 더 멋진 의미를 가져올 수 있습니다. 특히 다른 사람과 경쟁을 벌이고 있거나 시험에 도전하고 있는 등의 경우라면 당신의 능력에 하늘의 힘이 곁들여져서 좋은 결과를 맛볼 수 있을 것이니 자신감 있게 나서 보시기 바랍니다."},
    {"role": "user", "content": "대중 목욕탕 방문해서 욕조 물에 오물이 있었음. 그리고 샤워꼭지에서 물이 촬촬 흘러넘치는 꿈"},
    {"role": "system", "content": "오늘의 운세는 \"일필휘지\" 입니다. 만사가 잘 풀리고 여러 곳에서 도움을 받을 수 있으니 더없이 좋은 날입니다. 당신에게 있어 어떠한 부족한 점이 있는지도 이런 기회를 이용해서 한번 생각해본다면 좋은 바탕이 될 것입니다. 또한 자신이 목표하고 있는 일이 생각대로 잘 풀려가기 때문에 주변사람들의 응원이 더욱 빛을 발할 것입니다. 그리고 어려움이 있을 땐 가까운 사람에게 주저 말고 도움을 청해 보도록 하십시오. 마치 자신의 일과 같이 성실하고 친절하게 잘 도와주려 할 것이니 말이지요. 고맙게 받고 잘 활용하도록 하세요"},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"금의환향\" 입니다. 여기저기서 좋은 소식이 들려오니 당신의 기분 또한 좋아질 것입니다. 오랫동안 못 보던 사람에게서 연락을 받을 수 있으며 이는 자신에게 있어 득이 되는 소식일 수 있습니다. 또한 형제 자매가 중요한 시험에 붙는다거나 부모님께서 경사를 맞는다는 일도 생길 수 있습니다. 이처럼 오늘은 당신에게 직접 행운이 따르기 보다는 주변 사람들이 더 많은 운을 누릴 수 있는 날입니다. 당신이 마음에서 우러나는 축하를 함께 건네줄 수 있다면 물론 당신에게도 좋은 영향이 많이 있을 것이지요."},
    {"role": "user", "content": "x"},
    {"role": "system", "content": "오늘의 운세는 \"무용지용\" 입니다. 어딘지 모르게 체력의 부족함을 느끼는 하루입니다. 기운 없이 무기력함을 느끼게 된다면 잠시 일에서 손을 떼고 밖으로 나가는 것도 좋은 방법입니다. 새로운 공기를 마시고 머릿속에 좋은 공기를 불어넣어 준다면 답답함을 이겨낼 수 있는 좋은 계기가 될 수 있습니다. 또한 이럴 때에는 잠을 자거나 휴식을 취하기보다는 오히려 운동을 가볍게 해보는 것이 더욱 좋을 듯 하군요. 몸을 일으켜서 밖으로 나가보시기 바랍니다. 기분 전환으로 인해 오늘 하루를 무리없이 마무리 할 수 있을 겁니다."},
    {"role": "user", "content": "제가 좋아하는 연예인이랑 사귀는 꿈 꿨어요! 완전 행복했어요ᄒᄒ"},
    {"role": "system", "content": "오늘의 운세는 \"이럴수가\" 입니다. 마음이 다소 들떠 있는 날이니 추스르되 긴장은 푸시기 바랍니다. 너무 무리하는 것은 오히려 당신에게 이로울 수 없는 것입니다. 또한 당신이 원하는 만큼의 목표에 가까워왔다고 하여 마음을 놓아버리거나 쉽게 생각하는 태도로 좋지 않습니다. 끝까지 마무리할 수 있도록 최선을 노력을 다하는 것이 좋고 마음을 좀 더 여유롭게 가지고 행동하는 것이 필요하겠습니다. 또한 그저 평소에 해왔던 것과 같이 행동하면 어려울 것이 없는 날이니 눈앞에 놓인 것에 충실해 보시기 바랍니다."},
]

prompt5 = [
    {"role": "system", "content": "꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. '이 꿈은'으로 시작해주고, mbti에 대한 언급은 직접적으로 하지 말아줘. max_length=180, json format"},
    {"role": "user", "content": "intp, 어젯밤 나는 처음 꿈을 꾸었다. 누군가 날 안아주는 꿈 포근한 가슴에 얼굴을 묻고 웃었다. 나 그 꿈에서 살수는 없었나"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 당신이 애틋한 정서와 친밀감에 대한 갈망을 나타내고 있을 수 있습니다. 포근한 가슴에 얼굴을 묻고 웃는 상황은 당신이 편안함과 사랑, 보호를 갈망하고 있음을 보여줍니다. 그리고 이것이 행복하고 안정적인 상태를 연상시키기도 합니다. 그러나 꿈에서 일어난 후의 물음은 당신이 현재의 생활 상황에서 이러한 감정을 찾는 데 어려움을 겪고 있음을 나타낼 수 있습니다. 당신이 그 꿈에서 살 수 없었다는 문구는 현실과 이상 사이의 괴리감을 나타낼 수 있으며, 이것은 일반적으로 현재의 생활 상황에 대한 불만족을 나타냅니다. 이 꿈은 당신에게 현재의 생활에서 원하는 감정과 상황을 찾기 위해 무엇을 할 수 있는지 고민해보라는 메시지를 전달하고 있을 수 있습니다.\", \"main_keywords\": [\"편안함\", \"안정적인 상태\"]}"},
    {"role": "user", "content": "entj, 난 운전하고 있었고 예람누나가 전화로 자기 도슨트 못하겠다고 얘기하고 있었는데, 옆으로 아이오닉5 한대가 ㅈㄴ빠르게 달려가더니 저 앞에가서 공중으러 날고 내려꽃혀서 터짐. 그뒤로 사람 세명이 바구니같은곳에 실려나오는데 두명은 산거같기는한데 한명이 의식이 없어"},
    {"role": "system", "content": "{\"resolution\":\"이 꿈은 주변 환경 변화에 따른 불안감이나 스트레스를 나타내는 것일 수 있습니다. 운전 중인 모습은 일상생활에서의 책임감 및 부담감을 상징하며, 이로 인해 발생한 사건들은 예상치 못한 일들로 인한 충격 또는 당황스러움을 표현합니다. 특히 마지막 부분에서 등장인물들이 사망하거나 부상당하는 장면은 실제로 그런 일이 일어날 가능성보다는 그러한 두려움을 반영한다고 볼 수 있습니다. 따라서 이 꿈은 당신이 최근 들어 직면하게 된 문제나 걱정거리 때문에 심리적 압박감을 느끼고 있다는 것을 암시하므로, 잠시 휴식을 취하면서 마음을 가다듬는 시간을 갖는 것이 필요하다는 조언을 담고 있다고 해석될 수 있습니다.\", \"main_keywords\": [\"예상치 못한 일\", \"심리적 압박감\"]}"},
]

prompt6 = [
    {"role": "system", "content": "Translate the user's schedule into the json format (start_time, end_time, title, description). 월요일부터 일요일까지 한 주고, 1, 3, 5, 7, 8, 10, 12월은 31일, 4, 6, 9, 11월은 30일, 2월은 28일로 가정한다."},
    {"role": "user", "content": "local time: 2023-08-19 13:28:42 Saturday, 내일 오후 3시에 네이버 그린하우스 팀과 미팅이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-20 15:00:00\", \"end_time\": \"2023-08-20 16:00:00\", \"title\": \"미팅\", \"description\": \"네이버 그린하우스 팀\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 화요일부터 목요일 부산 해운대로 여행가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-22 00:00:00\", \"end_time\": \"2023-08-24 00:00:00\", \"title\": \"여행\", \"description\": \"부산 해운대\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 금요일 오후 2시에 용산 아이맥스에서 친구랑 영화 미션임파서블 보러 가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-25 14:00:00\", \"end_time\": \"2023-08-25 16:00:00\", \"title\": \"영화 보기\", \"description\": \"용산 아이맥스에서 미션 임파서블\"}"},
    {"role": "user", "content": "local time: 2023-08-23 13:28:42 Wednesday, 다음주 금요일 6시에 중앙도서관 앞에서 자동차 동아리 모임이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-09-01 18:00:00\", \"end_time\": \"2023-09-01 19:00:00\", \"title\": \"동아리 모임\", \"description\": \"중앙도서관 앞에서 자동차 동아리 모임\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 다음주 토요일 8시에 친구랑 노래방 가"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-25 20:00:00\", \"end_time\": \"2023-11-25 22:00:00\", \"title\": \"노래방\", \"description\": \"친구랑 노래방\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 다음주 월요일에 서현이 누나랑 데이트!!"},
    {"role": "system", "content": "{\"start_time\": \"2023-11-20 09:00:00\", \"end_time\": \"2023-11-20 22:00:00\", \"title\": \"데이트\", \"description\": \"서현이 누나랑 데이트\"}"},
    {"role": "user", "content": "local time: 2023-11-16 15:23:26 Thursday, 12월 23일-25일 후쿠오카 여행"},
    {"role": "system", "content": "{\"start_time\": \"2023-12-23 09:00:00\", \"end_time\": \"2023-12-25 22:00:00\", \"title\": \"여행\", \"description\": \"후쿠오카\"}"},
    {"role": "user", "content": "local time: 2023-11-21 15:23:26 Tuesday, 1월 1일에 서현이 누나랑 데이트"},
    {"role": "system", "content": "{\"start_time\": \"2024-01-01 09:00:00\", \"end_time\": \"2024-01-01 22:00:00\", \"title\": \"데이트\", \"description\": \"서현이 누나랑 데이트\"}"},
]

prompt7 = [
    {"role": "system", "content": "Analyze the user's dreams, diary, and schedule to create a about 3500-character Concrete 'Mental State Report'. Please write korean but each title is Engilsh."},
    {"role": "system", "content": "1. mental_state 2. positives  3. negatives  4. extroverted_activities 5. introverted_activities  6. recommendations 7. statistics 8. keywords"},
    {"role": "system", "content": "Provide detailed analysis for 'Mental State'. For items 1, total summary about report and include user nickname. about 200-character" },
    {"role": "system", "content": "For item 2-3, provide some comments about the user's extroverted and introverted activities. about 120-character. main_keyword in 2-3 is phrase or word that you choose."},
    {"role": "system", "content": "For item 7, provide a list 1 detail ratio dictionary for Extroversion, Introversion and for item 8 provide 5 keywords"},
    {"role": "system", "content": "공손한 말투로 만들어주세요. follow my example json format"},
    {"role": "system", "content": "ex) if user nickname: 태완, return = {\"mental_state\":\"태완님의 최근 삶에서는 다양한 마음의 상태가 복합적으로 드러납니다. 꿈이나 일기니에서 압박, 좌절, 갈망, 열정 등의 감정이 교차하고 있으며, 일상에서는 스타트업 활동에 전념하는 열정과 동시에 간혹 불안과 고민이 느껴집니다.\", \"positives\": {\"comment\": \"태완님의 열정이 가장 두드러집니다. 그 분야에 대한 사랑과 우리 서비스에 대한 확신, 미래에 대한 기대감 모두 당신의 열정을 드러냅니다.\", \"main_keyword\": \"서비스 대한 확신\"}, \"negatives\": {\"comment\": \"꿈에서 보여지는 불안과 좌절감이 삶에서도 다소 나타나고 있는 것으로 보입니다. 투자심사와 경쟁, 고민 등에 대한 부담감도 있을 것으로 보입니다.\", \"main_keyword\": \"부담감\"}, \"extroverted_activities\": [\"스타트업 홍보\", \"미팅 참석\", \"백화점에서 여자친구와 연말 데이트\"], \"introverted_activities\": [\"영화 관람\", \"개인적인 고민 및 생각 정리\", \"가천코코네스쿨의 첫번째 아웃풋이 되기 위한 노력\"], \"recommendations\": [\"스트레스 해소를 위한 취미활동 찾기\", \"진로에 대한 명확한 계획 수립\", \"자신감을 유지하되 현실을 직시\", \"주변 사람들과의 소통과 네트워킹 꾸준히\", \"마음의 안정을 위한 심리 치료 고려\"], \"statistics\": {\"extrovert\": 60, \"introvert\": 40}, \"keywords\": [\"열정\", \"불안\", \"확신\", \"현실감\", \"자기성찰\"]}"},
]

prompt8 = [
    {"role": "system", "content": "Analyze the user's memo and create json format of the memo. please write korean and return only json format, fill all the contents."},
    {"role": "system", "content": "{\"title\": \"메모에 대한 제목 생성\", \"content\":\"사용자 메모\", \"tags\":[\"??\", \"??\"]}"},
    {"role": "user", "content": "곽서준, 01046306320"},
    {"role": "system", "content": "{\"title\": \"곽서준님의 전화번호\", \"content\":\"01046306320\", \"tags\":[\"곽서준\", \"전화번호\"]}"},
    {"role": "user", "content": "컴퓨터 구조 책 다 읽고 정리하기"},
    {"role": "system", "content": "{\"title\": \"해야될 일\", \"content\":\"컴퓨터 구조 책 다 읽고 정리하기\", \"tags\":[\"컴퓨터 구조\", \"책\", \"정리\"]}"},
    {"role": "user", "content": "title = 아이유(IU)의 킬링보이스를 라이브로! - 하루 끝, 너의 의미, 스물셋, 밤편지, 팔레트, 가을 아침, 삐삐, Blueming, 에잇, Coin, 라일락 ㅣ 딩고뮤직 - YouTube, content = https://www.youtube.com/watch?v=wDfqXR_5yyQ"},
    {"role": "system", "content": "{\"title\": \아이유(IU)의 킬링보이스를 라이브로!\", \"content\":\"https://www.youtube.com/watch?v=K4yY5aVarhA\", \"tags\": [\"아이유\", \"킬링보이스\", \"라이브\"]}"},
    {"role": "user", "content": "애덤 그랜트 오리지널스"},
    {"role": "system", "content": "{\"title\": \"읽을 책\", \"content\":\"오리지널스 - Adam Grant\", \"tags\": [\"애덤 그랜트\", \"오리지널스\"]}"},
]

async def api_log(request_type: str, request_token: int, response_token: int, response_time_ms: int, model: str, user_id: int, db: Session):
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
    db.add(api_request_log)
    db.commit()
    db.refresh(api_request_log)

async def send_gpt_request(prompt_num: int , messages_prompt: str, current_user: User, db: Session, retries=3):
    prompt_dict = {2: "제목", 3: "이미지 프롬프트", 4: "일정", 5: "오늘의 운세", 6: "메모"}
    if prompt_num == 2:
        prompt = prompt2.copy()
    elif prompt_num == 3:
        prompt = prompt3.copy()
    elif prompt_num == 4:
        messages_prompt = f"local time: {datetime.datetime.now(pytz.timezone('Asia/Seoul'))} {days[datetime.datetime.now(pytz.timezone('Asia/Seoul')).weekday()]}, {messages_prompt}"
        prompt = prompt6.copy()
    elif prompt_num == 5:
        prompt = prompt4.copy()
    elif prompt_num == 6:
        prompt = prompt8.copy()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    prompt.append({"role": "user", "content": messages_prompt})
    for i in range(retries):
        try:
            start_time = await time_now()
            if prompt_num == 4 or prompt_num == 6:
                chat = openai.ChatCompletion.create(model="gpt-3.5-turbo-1106", messages=prompt, response_format={"type":"json_object"})
            else:
                chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
            end_time = await time_now()
            await api_log(
                user_id=current_user.id,
                request_type=prompt_dict[prompt_num],
                request_token=chat.usage.prompt_tokens,
                response_token=chat.usage.completion_tokens,
                response_time_ms=int((end_time - start_time).total_seconds() * 1000),
                model=chat.model,
                db=db
            )
            if prompt_num == 4 or prompt_num == 6:
                return json.loads(chat.choices[0].message.content)
            else:
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
async def send_gpt4_request(prompt_num: int, messages_prompt: str, current_user: User, db: Session, retries=3):
    prompt_dict = {1: "텍스트 분류", 2: "해몽", 3: "한 주 돌아보기"}
    if prompt_num == 1:
        prompt = prompt1.copy()
        messages_prompt = f"{datetime.datetime.now(pytz.timezone('Asia/Seoul'))}, {messages_prompt}"
    elif prompt_num == 2:
        prompt = prompt5.copy()
    elif prompt_num == 3:
        prompt = prompt7.copy()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    prompt.append({"role": "user", "content": messages_prompt})

    for i in range(retries):
        try:
            start_time = await time_now()
            if prompt_num == 2 or prompt_num == 3:
                chat = openai.ChatCompletion.create(model="gpt-4-1106-preview", messages=prompt, response_format={"type":"json_object"})
            # # chat = openai.ChatCompletion.create(model="gpt-4-1106-preview", messages=prompt, response_format={"type":"json_object"})
            else:
                chat = openai.ChatCompletion.create(model="gpt-4-1106-preview", messages=prompt)
            end_time = await time_now()
            await api_log(
                user_id=current_user.id,
                request_type=prompt_dict[prompt_num],
                request_token=chat.usage.prompt_tokens,
                response_token=chat.usage.completion_tokens,
                response_time_ms=int((end_time - start_time).total_seconds() * 1000),
                model=chat.model,
                db=db
            )
            content = chat.choices[0].message.content
            return content
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

async def send_dalle2_request(messages_prompt: str, user: User, db: Session, retries=3):
    for i in range(retries):
        try:
            start_time = await time_now()
            response = await asyncio.to_thread(
                openai.Image.create,
                model="dall-e-3",
                prompt=f"{messages_prompt[:255]}",
                n=1,
                size="1024x1024",
                response_format="url"
            )
            end_time = await time_now()
            await api_log(
                user_id=user.id,
                request_type="이미지 생성",
                request_token=0,
                response_token=0,
                response_time_ms=int((end_time - start_time).total_seconds() * 1000),
                model="DaLLE-3",
                db=db
            )
            return response['data'][0]['url']
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
