from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.ai_service import generate_mnemonics
from routes.auth import current_user
from sqlalchemy.orm import Session
from db import get_db
import math

router = APIRouter(prefix="/api/super-memory", tags=["Super Memory"])

class WordItem(BaseModel):
    word: str
    translation: str

class GenerateRequest(BaseModel):
    words: List[WordItem]
    chunk_size: int = 5

class MnemonicItem(BaseModel):
    word: str
    keyword: str = ""
    translation: str = ""
    mnemonic: str

class ChunkResponse(BaseModel):
    chunk_index: int
    story_uz: str
    mnemonics: List[MnemonicItem]
    words: List[WordItem]

@router.post("/generate-chunk", response_model=ChunkResponse)
async def generate_chunk(req: GenerateRequest, user=Depends(current_user), db: Session = Depends(get_db)):
    if not req.words:
        raise HTTPException(status_code=400, detail="No words provided")

    words_dict_list = [{"word": w.word, "translation": w.translation} for w in req.words]

    ai_result = generate_mnemonics(words_dict_list)

    if not ai_result:
        raise HTTPException(status_code=503, detail="AI Service unavailable or failed")

    return ChunkResponse(
        chunk_index=0,
        story_uz=ai_result.get("story_uz", ""),
        mnemonics=[MnemonicItem(**m) for m in ai_result.get("mnemonics", [])],
        words=req.words
    )
