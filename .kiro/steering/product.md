# BrainBridge — Product Overview

BrainBridge is an English vocabulary learning web app targeted at Uzbek-speaking users. It combines spaced repetition (Leitner box system + SM-2 algorithm) with AI-powered features to help users build and retain vocabulary.

## Core Features

- **Vocabulary management** — add English words with Uzbek translations, organized into 6 Leitner boxes (0 = new, 5 = mastered)
- **Spaced repetition review** — SM-2 algorithm drives `next_review` scheduling; words surface when due
- **Sentence writing** — users write two English sentences per word; AI grades them and advances/holds the word in a separate 5-box sentence track
- **AI Chat (BrainBot)** — Gemini-powered conversational assistant for language practice
- **Gamification** — XP, coins, daily streaks, achievements, leaderboard, levels, daily quests
- **Deck system** — pre-built vocabulary decks (IELTS, IT, etc.) users can import
- **Google OAuth** — sign-in via Google in addition to email/password
- **Admin panel** — user management, stats, moderation

## Target Users

Uzbek speakers learning English. UI text and error messages are written in Uzbek (`o'zbek tili`).

## Business Model

Freemium — some features (AI sentence checking, AI chat) are gated behind usage limits or a premium tier.
