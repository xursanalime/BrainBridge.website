"""
AI Service — Sentence Checker v3.1
=====================================
Yaxshilanishlar:
- Umumiy GeminiClient async ishlatiladi
- Logging kuchaytirildi
- Smart fallback saqlab qolindi
"""
import os
import json
import logging
import asyncio
from typing import Optional

import services.gemini_client as gemini

logger = logging.getLogger("brainbridge.ai_service")

_ERROR_LABELS = {
    "grammar": "Grammatik xato",
    "usage":   "Ishlatish xatosi",
    "meaning": "Ma'no xatosi",
}

ERROR_USER_MESSAGE = "AI vaqtincha ishlamayapti, keyinroq urinib ko'ring."

_SENTENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "correct":              {"type": "boolean"},
        "praise":               {"type": "string", "nullable": True},
        "error_type":           {"type": "string", "nullable": True},
        "explanation":          {"type": "string", "nullable": True},
        "examples":             {"type": "array", "items": {"type": "string"}},
        "example_translations": {"type": "array", "items": {"type": "string"}},
        "corrected":            {"type": "string", "nullable": True},
        "sentence_uz":          {"type": "string", "nullable": True},
    },
    "required": ["correct", "examples", "example_translations"],
}


def _build_prompt(word: str, translation: str, sentence: str) -> str:
    return (
        f"English teacher checking an Uzbek student's sentence.\n"
        f"Target word: '{word}' (Uzbek: {translation})\n"
        f"Student sentence: {sentence}\n\n"
        f"Check: 1) Grammar correctness  2) '{word}' used correctly  3) Meaning makes sense\n"
        f"Also provide 5 natural English examples with '{word}' "
        f"(statement, question, negative, past, future) + Uzbek translations.\n\n"
        "Return JSON with these exact keys:\n"
        "correct (bool), praise (Uzbek string or null), error_type (grammar|usage|meaning or null), "
        "explanation (Uzbek 2-4 sentences or null), examples (array of 5 strings), "
        "example_translations (array of 5 Uzbek strings), corrected (string or null), "
        "sentence_uz (Uzbek translation of student sentence)"
    )


def check_sentence(word: str, translation: str, sentence: str) -> dict:
    """
    Sync wrapper — AI orqali gap tekshirish.
    Async context'da check_sentence_async ishlatilsin.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # FastAPI async context'da
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, check_sentence_async(word, translation, sentence))
                return future.result(timeout=40)
        else:
            return loop.run_until_complete(check_sentence_async(word, translation, sentence))
    except Exception as exc:
        logger.error("check_sentence wrapper error: %s", exc)
        return _error_response()


async def check_sentence_async(word: str, translation: str, sentence: str) -> dict:
    """Async AI gap tekshirish."""
    prompt = _build_prompt(word, translation, sentence)

    result = await gemini.generate_json(
        prompt=prompt,
        model="flash",
        temperature=0.3,
        max_tokens=8192,
        response_schema=_SENTENCE_SCHEMA,
    )

    if result:
        examples = result.get("examples", [])
        translations = result.get("example_translations", [])
        while len(examples) < 5:
            examples.append(f"She uses the word '{word}' every day.")
        while len(translations) < 5:
            translations.append("")

        logger.info("Sentence checked: word=%s correct=%s", word, result.get("correct"))
        return {
            "correct":              bool(result.get("correct", False)),
            "praise":               result.get("praise"),
            "error_type":           result.get("error_type"),
            "error_label":          _ERROR_LABELS.get(result.get("error_type", ""), None),
            "explanation":          result.get("explanation"),
            "examples":             examples[:5],
            "example_translations": translations[:5],
            "corrected":            result.get("corrected"),
            "sentence_uz":          result.get("sentence_uz"),
        }

    logger.warning("AI sentence check failed for word=%s, using fallback", word)
    return _smart_fallback(word, translation, sentence)


def _error_response() -> dict:
    return {
        "correct": False, "praise": None, "error_type": None, "error_label": None,
        "explanation": ERROR_USER_MESSAGE, "examples": [], "example_translations": [],
        "corrected": None, "sentence_uz": None,
    }


# ── Smart fallback ────────────────────────────────────────────────────────────

_COMMON_NOUNS = {
    "table", "chair", "book", "house", "car", "dog", "cat", "water", "food",
    "school", "work", "friend", "family", "city", "country", "day", "time",
    "year", "month", "week", "hand", "eye", "face", "door", "window", "room",
    "phone", "computer", "street", "park", "store", "market", "office",
}
_COMMON_VERBS = {
    "run", "eat", "sleep", "study", "work", "go", "come", "see", "know",
    "think", "make", "read", "write", "speak", "listen", "walk", "talk",
    "help", "love", "play", "sit", "stand", "finish", "start", "learn",
    "teach", "travel", "kick", "hit", "jump", "fly", "drive", "swim",
}


def _smart_fallback(word: str, translation: str, sentence: str) -> dict:
    s = sentence.strip()
    s_lower = s.lower()
    w = word.lower()

    if not s:
        return _make_error(word, translation, "usage",
                           "Gap bo'sh. Iltimos, so'zni ishlatib to'liq inglizcha gap tuzing.")

    stems = {w, w + "s", w + "ed", w + "ing", w.rstrip("e") + "ing",
              w.rstrip("e") + "ed", w + "er", w + "est", w + "ly",
              w + "tion", w + "ness", w + "ment"}
    word_found = any(
        stem in s_lower.split() or
        f" {stem} " in f" {s_lower} " or
        s_lower.startswith(stem + " ") or
        s_lower.endswith(" " + stem)
        for stem in stems
    )

    if not word_found:
        return _make_error(word, translation, "usage",
                           f'Gapda "{word}" so\'zi (yoki uning shakli) ishlatilmagan. '
                           f'So\'zni to\'g\'ri o\'rinda qo\'llang.')

    if len(s.split()) < 3:
        return _make_error(word, translation, "grammar",
                           "Gap juda qisqa. Kamida 3-4 so'zdan iborat to'liq gap yozing.")

    if w in _COMMON_NOUNS:
        verb_patterns = [f"i {w} ", f"i {w}.", f"to {w} ", f"can {w}",
                          f"will {w}", f"must {w}", f"should {w}"]
        if any(pat in f" {s_lower} " for pat in verb_patterns):
            examples = _generate_5_examples(word, translation, is_noun=True)
            return {
                "correct": False, "praise": None,
                "error_type": "meaning", "error_label": "Ma'no xatosi",
                "explanation": (
                    f'"{word}" — bu ot (noun), ya\'ni "{translation}" degan ma\'noni anglatadi. '
                    f'Uni fe\'l (verb) sifatida ishlatish to\'g\'ri emas.'
                ),
                "examples":             examples["examples"],
                "example_translations": examples["translations"],
                "corrected":            examples["corrected"],
                "sentence_uz":          f'[Bu gap ma\'nosiz: "{word}" ot, fe\'l emas]',
            }

    examples = _generate_5_examples(word, translation, is_noun=w in _COMMON_NOUNS)
    return {
        "correct": True,
        "praise":  f'Zo\'r! "{word}" so\'zini to\'g\'ri va mazmunli ishlatibsiz. 🎉',
        "error_type": None, "error_label": None, "explanation": None,
        "examples":             examples["examples"],
        "example_translations": examples["translations"],
        "corrected":            None,
        "sentence_uz":          f'"{translation}" so\'zidan foydalanib gap tuzgansiz.',
    }


def _make_error(word: str, translation: str, error_type: str, explanation: str) -> dict:
    examples = _generate_5_examples(word, translation, is_noun=word.lower() in _COMMON_NOUNS)
    return {
        "correct": False, "praise": None,
        "error_type":  error_type,
        "error_label": _ERROR_LABELS.get(error_type, "Xato"),
        "explanation": explanation,
        "examples":             examples["examples"],
        "example_translations": examples["translations"],
        "corrected":            examples["corrected"],
        "sentence_uz":          None,
    }


def _generate_5_examples(word: str, translation: str, is_noun: bool = False) -> dict:
    w  = word.lower()
    uz = translation.split(",")[0].strip()
    if is_noun:
        return {
            "examples": [
                f"There is a {w} in the room.",
                f"She bought a new {w} yesterday.",
                f"I need to fix the {w} in my office.",
                f"Have you seen my {w}? I can't find it.",
                f"The old {w} was replaced with a modern one.",
            ],
            "translations": [
                f"Xonada bir {uz} bor.",
                f"U kecha yangi {uz} sotib oldi.",
                f"Men ofisimdagi {uz}ni ta'mirlashim kerak.",
                f"{uz.capitalize()}imni ko'rdingizmi? Topa olmayapman.",
                f"Eski {uz} zamonaviysi bilan almashtirildi.",
            ],
            "corrected": f"I have a {w} in my room.",
        }
    return {
        "examples": [
            f"She tries to {w} every morning.",
            f"It is important to {w} regularly.",
            f"He didn't {w} yesterday because he was tired.",
            f"Can you {w} with me after school?",
            f"They have been learning how to {w} for months.",
        ],
        "translations": [
            f"U har kuni ertalab {uz}ga harakat qiladi.",
            f"Muntazam {uz} muhimdir.",
            f"U kecha charchagani uchun {uz}madi.",
            f"Maktabdan keyin men bilan {uz}a olasizmi?",
            f"Ular oylar davomida qanday {uz}ishni o'rganmoqda.",
        ],
        "corrected": f"I try to {w} every day.",
    }


# ── Mnemonics ─────────────────────────────────────────────────────────────────

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "mnemonics_cache.json")


def _load_cache() -> dict:
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_to_cache(mnemonics_list: list[dict]) -> None:
    cache = _load_cache()
    added = 0
    for m in mnemonics_list:
        key = m.get("word", "").lower().strip()
        if key and key not in cache:
            cache[key] = {
                "translation": m.get("translation", ""),
                "keyword":     m.get("keyword", ""),
                "mnemonic":    m.get("mnemonic", ""),
            }
            added += 1
    if added:
        try:
            with open(_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            logger.info("Mnemonics cache updated: +%d (total=%d)", added, len(cache))
        except OSError as exc:
            logger.warning("Cache save error: %s", exc)


def _build_story_from_cache(cached: list[dict]) -> str:
    parts = [m["mnemonic"] for m in cached]
    return "Bir kuni g'alati voqealar ketma-ket sodir bo'ldi: " + ". ".join(parts) + "."


def generate_mnemonics(words_chunk: list[dict]) -> dict | None:
    """Sync wrapper for async mnemonic generation."""
    try:
        return asyncio.run(generate_mnemonics_async(words_chunk))
    except RuntimeError:
        # Event loop already running
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(generate_mnemonics_async(words_chunk))


async def generate_mnemonics_async(words_chunk: list[dict]) -> dict | None:
    """Cache → API → partial cache fallback."""
    cache = _load_cache()
    cached, uncached = [], []

    for w in words_chunk:
        key = w["word"].lower().strip()
        if key in cache:
            entry = cache[key]
            cached.append({
                "word":        w["word"],
                "translation": entry.get("translation", w.get("translation", "")),
                "keyword":     entry["keyword"],
                "mnemonic":    entry["mnemonic"],
            })
        else:
            uncached.append(w)

    logger.info("Mnemonics: %d cached, %d uncached", len(cached), len(uncached))

    if not uncached:
        logger.info("100%% from cache — no API call needed")
        return {"story_uz": _build_story_from_cache(cached), "mnemonics": cached}

    if gemini.is_available:
        api_result = await _call_gemini_mnemonics(words_chunk)
        if api_result and "mnemonics" in api_result:
            for m in api_result["mnemonics"]:
                for w in words_chunk:
                    if w["word"].lower() == m.get("word", "").lower():
                        m["translation"] = w.get("translation", "")
            _save_to_cache(api_result["mnemonics"])
            return api_result

    if cached:
        logger.warning("API failed, returning %d from cache", len(cached))
        for w in uncached:
            cached.append({
                "word":        w["word"],
                "translation": w.get("translation", ""),
                "keyword":     "—",
                "mnemonic":    f"'{w['word']}' so'zining tarjimasi '{w.get('translation', '')}' ekanini eslab qoling.",
            })
        return {"story_uz": _build_story_from_cache(cached), "mnemonics": cached}

    return None


async def _call_gemini_mnemonics(words_chunk: list[dict]) -> dict | None:
    words_info = ", ".join([f"{w['word']} ({w.get('translation', '')})" for w in words_chunk])
    prompt = (
        f"You are a cognitive psychology expert specializing in the 'Keyword Method' for language learning.\n"
        f"English words and Uzbek translations: {words_info}\n\n"
        f"1. STORY: Create a short, highly bizarre, and memorable story in UZBEK connecting all these words. "
        f"Use English words directly inside the Uzbek story.\n"
        f"2. MNEMONICS (Keyword Method): For each word:\n"
        f"   - Find how the English word is PRONOUNCED (its sound, not spelling)\n"
        f"   - Find an Uzbek 'keyword' that sounds similar to that pronunciation\n"
        f"   - Examples: 'cow' (/kau/) → 'QOVUN', 'bag' (/beg/) → 'BEGEMOT'\n"
        f"   - Create a bizarre, vivid mental image linking the keyword to the actual meaning\n\n"
        "Return strictly JSON:\n"
        '{"story_uz": "story here", "mnemonics": [{"word": "english", "keyword": "uzbek sound", "mnemonic": "image"}]}'
    )

    result = await gemini.generate_json(
        prompt=prompt,
        model="flash",
        temperature=0.7,
        max_tokens=8192,
    )
    return result
