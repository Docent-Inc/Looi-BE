import asyncio
import openai
from aiohttp import ClientSession
from dotenv import load_dotenv
import os
from fastapi import HTTPException, status
import datetime
import pytz
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
stable_diffusion_api_key = os.getenv("STABLE_DIFFUSION")
hyperclova_api_key = os.getenv("HYPER_CLOVA_KEY")
hyperclova_api_gateway = os.getenv("HYPER_CLOVA_GATEWAY")
hyperclova_request_id = os.getenv("HYPER_CLOVA_REQUEST_ID")
kakao_api_key = os.getenv("KAKAO_API_KEY")

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
]


prompt2 = [
    {"role": "system", "content": "사용자의 스토리에대한 제목을 만들어줘"},
    {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
    {"role": "system", "content": "수상한 강아지의 탈출 대작전"},
    {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
    {"role": "system", "content": "비둘기와 나의 특별한 우정"},
]

prompt3 = [
    {"role": "system", "content": "make just one scene a prompt for DALLE2 about this diary"},
    {"role": "system", "content": "include the word illustration, digital art, vivid and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
    {"role": "system", "content": "make just prompt only engilsh"},
    {"role": "system", "content": "max_length=250"},
    {"role": "user", "content": "학교 복도에서 친구랑 얘기하다가 갑자기 앞문쪽에서 좀비떼가 몰려와서 도망침. 근데 알고보니 우리반 애였음. 걔네 반 담임쌤한테 가서 말하니까 쌤이 괜찮다고 하심. 그래서 안심하고 있었는데 또다른 좀비가 와서 막 물어뜯음. 그러다가 깼는데 아직도 심장이 벌렁벌렁 거림.."},
    {"role": "system", "content": "Create a vivid digital art illustration depicting a zombie apocalypse in a school hallway. Illuminate the scene with an eerie, greenish light and use a dull, muted color scheme, accentuated by splashes of blood-red. Capture the mood of shock and fear, and compose the artwork to emphasize the adrenaline-pumping chase and a sudden, terrifying zombie ambush."},
    {"role": "user", "content": "학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다."},
    {"role": "system", "content": "Create a digital art illustration that is vivid and lively, set during a school festival. Showcase a festival-goer receiving a tarot reading. Employ warm and inviting lighting to illuminate a vibrant and colorful scene. Convey mixed emotions of disappointment and relief on the protagonist's face as they react to their tarot reading."},
    {"role": "user", "content": "적에게 계속 도망치면서 세상을 구할 목표를 향해 팀원들과 향해 나아간다. 모험중에서 새로운 사람도 만나며 나아가지만 결국 나 혼자서 해내야 하는 상황에 마주친다. 하지만 목표를 향한 문제 풀이 과정에서 답도 모르지만 안풀리는 상황에 놓이고 적에게 붙잡히지는 않았지만 따라잡히게 된다."},
    {"role": "system", "content": "Craft a vivid digital art illustration that captures the essence of a hero's journey. Set the scene in a fantastical world that's rich in color and illuminated by dramatic adventure lighting. The artwork should evoke feelings of determination and anxiety. Put the spotlight on the hero's solitary struggle and pursuit, as they face obstacles and enemies in their quest to save the world."},
]

prompt4 = [
    {"role": "system", "content": "꿈의 내용을 보고 오늘의 운세를 만들어줘, 꿈의 내용은 참고만 하고 내용에 녹아들어가게 해주고, 사자성어로 운세 총운을 만들어줘, 꿈의 내용이 없다면 그냥 오늘의 운세를 만들어줘"},
    {"role": "user", "content": "나랑 친한 친구들이 다같이 모여서 놀다가 갑자기 한명씩 사라져서 마지막엔 나만 남았다. 그래서 혼자 울다가 깼다."},
    {"role": "system", "content": "오늘의 운세는 “여어득수” 입니다. 기대치 않았던 곳에서 큰 지원을 받게 되니 일을 더욱 잘 풀리고 몸과 마음 또한 더없이 기쁘고 편할 수 있을 것입니다. 당신에게 스트레스로 작용했던 일이 있다면 당신의 노력이 바탕이 되어 해결할 수 있는 기회도 잡을 수 있습니다. 또한 주변사람들로부터 도움이나 조언을 통해서 자신의 방향을 잡을 수도 있습니다. 그러나 자신의 의지를 잃지 않는 것도 중요한 부분입니다. 당신에게 닥친 이 기회를 잘 활용한다면 충분히 많은 성과와 발전이 있을 것이지요. 조금 더 분발하세요."},
    {"role": "user", "content": "제가 좋아하는 연예인이랑 사귀는 꿈 꿨어요! 완전 행복했어요ᄒᄒ"},
    {"role": "system", "content": "오늘의 운세는 “이럴수가” 입니다. 마음이 다소 들떠 있는 날이니 추스르되 긴장은 푸시기 바랍니다. 너무 무리하는 것은 오히려 당신에게 이로울 수 없는 것입니다. 또한 당신이 원하는 만큼의 목표에 가까워왔다고 하여 마음을 놓아버리거나 쉽게 생각하는 태도로 좋지 않습니다. 끝까지 마무리할 수 있도록 최선을 노력을 다하는 것이 좋고 마음을 좀 더 여유롭게 가지고 행동하는 것이 필요하겠습니다. 또한 그저 평소에 해왔던 것과 같이 행동하면 어려울 것이 없는 날이니 눈앞에 놓인 것에 충실해 보시기 바랍니다."},
]

prompt5 = [
    {"role": "system", "content": "꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. '이 꿈은'으로 시작해주고, 엠비티아이에 대한 언급은 직접적으로 하지 말아줘. max_length=200 "},
    {"role": "user", "content": "intp, 어젯밤 나는 처음 꿈을 꾸었다. 누군가 날 안아주는 꿈 포근한 가슴에 얼굴을 묻고 웃었다. 나 그 꿈에서 살수는 없었나"},
    {"role": "system", "content": "이 꿈은 당신이 애틋한 정서와 친밀감에 대한 갈망을 나타내고 있을 수 있습니다. 포근한 가슴에 얼굴을 묻고 웃는 상황은 당신이 편안함과 사랑, 보호를 갈망하고 있음을 보여줍니다. 그리고 이것이 행복하고 안정적인 상태를 연상시키기도 합니다. 그러나 꿈에서 일어난 후의 물음은 당신이 현재의 생활 상황에서 이러한 감정을 찾는 데 어려움을 겪고 있음을 시사할 수 있습니다. 당신이 그 꿈에서 살 수 없었다는 문구는 현실과 이상 사이의 괴리감을 나타낼 수 있으며, 이것은 일반적으로 현재의 생활 상황에 대한 불만족을 나타냅니다. 이 꿈은 당신에게 현재의 생활에서 원하는 감정과 상황을 찾기 위해 무엇을 할 수 있는지 고민해보라는 메시지를 전달하고 있을 수 있습니다. 이를 통해, 당신은 행복과 만족감을 추구하는 데 있어서 자신의 삶에서 무엇이 중요한지, 어떤 것들을 고려해야 하는지에 대해 생각해볼 수 있습니다."},
    {"role": "user", "content": "entj, 난 운전하고 있었고 예람누나가 전화로 자기 도슨트 못하겠다고 얘기하고 있었는데, 옆으로 아이오닉5 한대가 ㅈㄴ빠르게 달려가더니 저 앞에가서 공중으러 날고 내려꽃혀서 터짐. 그뒤로 사람 세명이 바구니같은곳에 실려나오는데 두명은 산거같기는한데 한명이 의식이 없어"},
    {"role": "system", "content": "이 꿈은 주변 환경 변화에 따른 불안감이나 스트레스를 나타내는 것일 수 있습니다. 운전 중인 모습은 일상생활에서의 책임감 및 부담감을 상징하며, 이로 인해 발생한 사건들은 예상치 못한 일들로 인한 충격 또는 당황스러움을 표현합니다. 특히 마지막 부분에서 등장인물들이 사망하거나 부상당하는 장면은 실제로 그런 일이 일어날 가능성보다는 그러한 두려움을 반영한다고 볼 수 있습니다. 따라서 이 꿈은 당신이 최근 들어 직면하게 된 문제나 걱정거리 때문에 심리적 압박감을 느끼고 있다는 것을 암시하므로, 잠시 휴식을 취하면서 마음을 가다듬는 시간을 갖는 것이 필요하다는 조언을 담고 있다고 해석될 수 있습니다."},
]

prompt6 = [
    {"role": "system", "content": "Translate the user's schedule into the appropriate format (start_time, end_time, title, description). 월요일부터 일요일까지 한 주고, 1, 3, 5, 7, 8, 10, 12월은 31일, 4, 6, 9, 11월은 30일, 2월은 28일로 가정한다."},
    {"role": "user", "content": "local time: 2023-08-19 13:28:42 Saturday, 내일 오후 3시에 네이버 그린하우스 팀과 미팅이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-20 15:00:00\", \"end_time\": \"2023-08-20 16:00:00\", \"title\": \"미팅\", \"description\": \"네이버 그린하우스 팀\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 화요일부터 목요일 부산 해운대로 여행가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-22 00:00:00\", \"end_time\": \"2023-08-24 00:00:00\", \"title\": \"여행\", \"description\": \"부산 해운대\"}"},
    {"role": "user", "content": "local time: 2023-08-20 13:28:42 Sunday, 다음주 금요일 오후 2시에 용산 아이맥스에서 친구랑 영화 미션임파서블 보러 가"},
    {"role": "system", "content": "{\"start_time\": \"2023-08-25 14:00:00\", \"end_time\": \"2023-08-25 16:00:00\", \"title\": \"영화 보기\", \"description\": \"용산 아이맥스에서 미션 임파서블\"}"},
    {"role": "user", "content": "local time: 2023-08-23 13:28:42 Wednesday, 다음주 금요일 6시에 중앙도서관 앞에서 자동차 동아리 모임이 있어"},
    {"role": "system", "content": "{\"start_time\": \"2023-09-01 18:00:00\", \"end_time\": \"2023-09-01 19:00:00\", \"title\": \"동아리 모임\", \"description\": \"중앙도서관 앞에서 자동차 동아리 모임\"}"},
]

prompt7 = [
    {"role": "system", "content": "Analyze the user's dreams, diary, and schedule to create a about 3000-character Concrete 'Mental State Report'. Please write korean but each title is Engilsh."},
    {"role": "system", "content": "1. Mental State 2. Extroverted Activities 3. Introverted Activities 4. Positives 5. Negatives 6. Recommendations 7. Statistics"},
    {"role": "system", "content": "Provide detailed analysis for 'Mental State'. For items 1, total coment about report and include user name with out last name(ex 서준님은 ~). For items 2-5, list 3 each. For item 6, list 5 recommendations."},
    {"role": "system", "content": "For item 7, provide a list 1 detail ratio dictionary for Extroversion, Introversion, and the five keyword list that you choose. The first ratio dictionary's total should add up to 100. In the second list . For example, [{\"외향\": 50, \"내향\": 50}, [\"열정\"]]"},
    {"role": "system", "content": "Return the only json format of the report with out number and Enter(ex {\"Mental State\":\"content(korean)\", \"Extroverted Activities\":\"[each conent]\"} ."},
    {"role": "system", "content": "공손한 말투로 만들어주세요."},
]

promt8 = [
    {"role": "system", "content": "Analyze the user's memo and create json format of the memo."},
    {"role": "system", "content": "{\"title\": \"메모에 대한 제목 생성\", \"content\":\"사용자 메모\"}"},
    {"role": "user", "content": "공손한 말투로 만들어주세요."},
]




async def send_gpt_request(prompt_num, messages_prompt, retries=3):
    '''
    주어진 프롬프트로 GPT API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.
    prompt_num: 2. 제목 만들기, 3. 프롬프트 만들기, 4. 일정 만들기
    '''
    if prompt_num == 2: # 제목 만들기
        prompt = prompt2.copy()
    elif prompt_num == 3: # 프롬프트 만들기
        prompt = prompt3.copy()
    elif prompt_num == 4: # 일정 만들기
        messages_prompt = f"local time: {datetime.datetime.now(pytz.timezone('Asia/Seoul'))} {days[datetime.datetime.now(pytz.timezone('Asia/Seoul')).weekday()]}, {messages_prompt}"
        prompt = prompt6.copy()
    elif prompt_num == 5: # 오늘의 운세 만들기
        prompt = prompt4.copy()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    prompt.append({"role": "user", "content": messages_prompt})
    for i in range(retries):
        try:
            chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
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
async def send_gpt4_request(prompt_num, messages_prompt, retries=3):
    '''
    주어진 프롬프트로 GPT4 API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.
    prompt_num: 1. 택스트 분류 2. 해몽 3. 마음상태 보고서
    '''
    if prompt_num == 1: # 택스트 분류
        prompt = prompt1.copy()
        messages_prompt = f"{datetime.datetime.now(pytz.timezone('Asia/Seoul'))}, {messages_prompt}"
    elif prompt_num == 2: # 해몽
        prompt = prompt5.copy()
    elif prompt_num == 3: # 마음상태 보고서
        prompt = prompt7.copy()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    prompt.append({"role": "user", "content": messages_prompt})
    for i in range(retries):
        try:
            chat = openai.ChatCompletion.create(model="gpt-4", messages=prompt)
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


# async def send_hyperclova_request(prompt_num, messages_prompt, retries=3):
#     '''
#     주어진 프롬프트로 Hyperclova API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.
#     '''
#     if prompt_num == 1: # 오늘의 운세
#         prompt = prompt4.format(messages_prompt)
#     for i in range(retries):
#         try:
#             url = "https://clovastudio.apigw.ntruss.com/serviceapp/v1/tasks/x56n5fyu/completions/LK-D2"
#
#             request_data = {
#                 'text': prompt,
#                 'maxTokens': 1000,
#                 'temperature': 0.75,
#                 'topK': 0,
#                 'topP': 0.8,
#                 'repeatPenalty': 6,
#                 'start': '###클로바:',
#                 'restart': '',
#                 'stopBefore': ['###꿈 내용:'],
#                 'includeTokens': True,
#                 'includeAiFilters': True,
#                 'includeProbs': False
#             }
#
#             headers = {
#                 'Content-Type': 'application/json; charset=utf-8',
#                 "X-NCP-CLOVASTUDIO-API-KEY": hyperclova_api_key,
#                 "X-NCP-APIGW-API-KEY": hyperclova_api_gateway,
#             }
#
#             async with ClientSession() as session:
#                 async with session.post(url, headers=headers, json=request_data) as response:
#                     result = await response.json()
#                     print(result)
#                     return result['result']['text'].replace("###클로바:", "").lstrip()
#         except Exception as e:
#             print(f"Hypercolva API Error: {e}")
#             if i < retries - 1:
#                 print(f"Retrying {i + 1} of {retries}...")
#             else:
#                 print("Failed to get response after maximum retries")
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail=4502,
#                 )
async def send_stable_deffusion_request(messages_prompt, retries=3):
    for i in range(retries):
        try:
            url = "https://stablediffusionapi.com/api/v3/text2img"

            data = {
                "key": stable_diffusion_api_key,
                "prompt": messages_prompt[:300],
                "negative_prompt": None,
                "width": "512",
                "height": "512",
                "samples": "1",
                "num_inference_steps": "20",
                "safety_checker": "yes",
                "enhance_prompt": "yes",
                "seed": None,
                "guidance_scale": 7.5,
                "webhook": None,
                "track_id": None
            }

            headers = {"Content-Type": "application/json"}

            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return result["output"][0]
        except Exception as e:
            print(f"Stable Diffusion API Error{e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=4503,
                )


async def send_karlo_request(messages_prompt, retries=3):
    for i in range(retries):
        try:
            url = "https://api.kakaobrain.com/v2/inference/karlo/t2i"

            data = {
                'prompt': messages_prompt[:255],
                'prior_guidance_scale': 5,
                'width': '512',
                'height': '512',
                'nsfw_checker': True,
            }

            headers = {
                'Authorization': f'KakaoAK {kakao_api_key}',
                'Content-Type': 'application/json'
            }

            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return result['images'][0]['image']
        except Exception as e:
            print(f"Karlo API Error{e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=4504,
                )

async def send_dalle2_request(messages_prompt, retries=3):
    for i in range(retries):
        try:
            response = await asyncio.to_thread(
                openai.Image.create,
                prompt=messages_prompt[:255],
                n=1,
                size="512x512",
                response_format="url"
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
