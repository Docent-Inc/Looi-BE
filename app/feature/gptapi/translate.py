import asyncio
from sqlalchemy.orm import Session
from app.feature.gptapi.gptRequset import send_gpt_request
from app.db.models.diary_en import Diary_en
from app.db.models.diary_ko import Diary_ko

async def translate_ko_to_en(create: Diary_ko, diary_id: int, db: Session) -> str:
    dream_name = create.dream_name
    dream = create.dream
    resolution = create.resolution
    try:
        isDiary_en = db.query(Diary_en).filter(Diary_en.diary_id == diary_id).first()
        return "already translated"
    except:
        pass
    async def translate_text(text: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "translate this text to english"},
            {"role": "user", "content": text}
        ]
        return await send_gpt_request(messages_prompt)

    translated_dream_name, translated_dream, translated_resolution = await asyncio.gather(
        translate_text(dream_name),
        translate_text(dream),
        translate_text(resolution)
    )

    diary_entry = Diary_en(
        Diary_id=diary_id,
        dream_name=translated_dream_name,
        dream=translated_dream,
        resolution=translated_resolution
    )

    db.add(diary_entry)
    db.commit()

async def translate_en_to_ko(create: Diary_en, diary_id: int, db: Session) -> str:
    dream_name = create.dream_name
    dream = create.dream
    resolution = create.resolution
    try:
        isDiary_ko = db.query(Diary_ko).filter(Diary_ko.diary_id == diary_id).first()
        return "already translated"
    except:
        pass
    async def translate_text(text: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "translate this text to korean"},
            {"role": "user", "content": text}
        ]
        return await send_gpt_request(messages_prompt)

    translated_dream_name, translated_dream, translated_resolution = await asyncio.gather(
        translate_text(dream_name),
        translate_text(dream),
        translate_text(resolution)
    )

    diary_entry = Diary_ko(
        Diary_id=diary_id,
        dream_name=translated_dream_name,
        dream=translated_dream,
        resolution=translated_resolution
    )

    db.add(diary_entry)
    db.commit()