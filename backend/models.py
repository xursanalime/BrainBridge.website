from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index, func, Boolean, Text, BigInteger, Float
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id                 = Column(Integer, primary_key=True, index=True)
    email              = Column(String, unique=True, index=True, nullable=False)
    full_name          = Column(String, nullable=True)
    password_hash      = Column(String, nullable=False)
    prev_password_hash = Column(String, nullable=True)
    streak             = Column(Integer, default=0)
    last_study         = Column(DateTime(timezone=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    # brute-force protection
    failed_logins      = Column(Integer, default=0, nullable=False)
    locked_until       = Column(DateTime(timezone=True), nullable=True)
    locked_permanent   = Column(Boolean, default=False, nullable=False)
    # monthly password change limit
    pw_change_count    = Column(Integer, default=0, nullable=False)
    pw_change_month    = Column(String(7), nullable=True)   # "YYYY-MM"
    # password reset
    reset_token        = Column(String, nullable=True)
    reset_token_exp    = Column(DateTime(timezone=True), nullable=True)
    # gamification
    total_xp           = Column(Integer, default=0, nullable=False)
    daily_xp           = Column(Integer, default=0, nullable=False)
    monthly_xp         = Column(Integer, default=0, nullable=False)
    last_xp_reset      = Column(DateTime(timezone=True), nullable=True)
    coins              = Column(Integer, default=0, nullable=False)
    streak_freezes     = Column(Integer, default=0, nullable=False)
    daily_reviews      = Column(Integer, default=0, nullable=False)
    avatar_url         = Column(String, nullable=True)
    avatar_data        = Column(Text, nullable=True)       # base64 encoded image
    # daily goals
    goal_reviews       = Column(Integer, default=10, nullable=False)
    # admin
    is_admin           = Column(Boolean, default=False, nullable=False)
    goal_xp            = Column(Integer, default=50, nullable=False)
    # tier (free/pro/premium)
    tier               = Column(String, default="free", nullable=False)
    # daily sentence counter
    daily_sentences    = Column(Integer, default=0, nullable=False)

    words               = relationship("Word", back_populates="user", cascade="all, delete-orphan")
    achievements        = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    chat_sessions       = relationship("AIChatSession", back_populates="user", cascade="all, delete-orphan")
    sentence_progress   = relationship("SentenceProgress", back_populates="user", cascade="all, delete-orphan")
    payment_records     = relationship("PaymentRecord", back_populates="user", cascade="all, delete-orphan")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String(50), nullable=False) # e.g. "first_word", "streak_7"
    unlocked_at    = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="achievements")

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )


class OAuthState(Base):
    """Temporary OAuth state tokens stored in DB (needed for serverless/Vercel)."""
    __tablename__ = "oauth_states"

    state      = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Deck(Base):
    """Tayyor lug'at to'plamlari (IELTS, IT, vs)."""
    __tablename__ = "decks"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon        = Column(String, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class DeckWord(Base):
    """To'plam ichidagi so'zlar."""
    __tablename__ = "deck_words"
    id          = Column(Integer, primary_key=True, index=True)
    deck_id     = Column(Integer, ForeignKey("decks.id"), nullable=False)
    word        = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    
    deck = relationship("Deck", backref="words")


class Word(Base):
    __tablename__ = "words"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    word        = Column(String, nullable=False)          # inglizcha
    translation = Column(String, nullable=False)          # o'zbekcha
    box         = Column(Integer, default=0, nullable=False)  # 0-5
    # SM-2 algoritm parametrlari
    ease_factor = Column(Float, default=2.5, nullable=False)
    interval    = Column(Integer, default=0, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    
    next_review = Column(DateTime(timezone=True), server_default=func.now())
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user              = relationship("User", back_populates="words")

    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_user_word"),
        Index("ix_words_user_box",    "user_id", "box"),
        Index("ix_words_user_review", "user_id", "next_review"),
    )


# ── Sentence Module ──────────────────────────────────────────────────────────

class SentenceProgress(Base):
    """Har bir so'z uchun gap tuzish bosqichi (Leitner sentence boxes)."""
    __tablename__ = "sentence_progress"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id        = Column(Integer, ForeignKey("words.id"), nullable=False)
    sentence_box   = Column(Integer, default=1, nullable=False)   # 1-5
    sentences_done = Column(Integer, default=0, nullable=False)   # 0, 1, or 2
    last_reviewed  = Column(DateTime(timezone=True), nullable=True)
    next_review    = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sentence_progress")
    word = relationship("Word")

    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_sentence_progress"),
        Index("ix_sp_user_review", "user_id", "next_review"),
    )


class UserSentence(Base):
    """Foydalanuvchi yozgan gaplar tarixi."""
    __tablename__ = "user_sentences"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id         = Column(Integer, ForeignKey("words.id"), nullable=False)
    sentence_text   = Column(Text, nullable=False)
    is_correct      = Column(Boolean, default=False, nullable=False)
    ai_feedback     = Column(Text, nullable=True)       # JSON string
    sentence_number = Column(Integer, default=1, nullable=False)  # 1 or 2
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    word = relationship("Word")


# ── AI Chat Module ───────────────────────────────────────────────────────────

class AIChatSession(Base):
    """AI chatbot suhbat sessiyalari."""
    __tablename__ = "ai_chat_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    name       = Column(String, default="Yangi suhbat", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user     = relationship("User", back_populates="chat_sessions")
    messages = relationship("AIChatMessage", back_populates="session",
                            cascade="all, delete-orphan",
                            order_by="AIChatMessage.id")


class AIChatMessage(Base):
    """AI chatbot xabarlari."""
    __tablename__ = "ai_chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role       = Column(String(20), nullable=False)    # "user" | "assistant"
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AIChatSession", back_populates="messages")


# ── Payment Module ───────────────────────────────────────────────────────────

class PaymentRecord(Base):
    """To'lov tarixi."""
    __tablename__ = "payment_records"

    id             = Column(Integer, primary_key=True, index=True)
    order_id       = Column(String, unique=True, nullable=False, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier           = Column(String, nullable=False)       # "pro" | "premium" | "free"
    amount         = Column(Integer, default=0, nullable=False)  # so'm
    method         = Column(String, nullable=False)       # "payme" | "click" | "card" | "cancel"
    status         = Column(String, nullable=False)       # "pending" | "success" | "failed" | "cancelled"
    transaction_id = Column(String, nullable=True)
    note           = Column(String, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="payment_records")

