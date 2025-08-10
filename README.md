# BoulderCoach
BoulderCoach
AI voice-first coach for bouldering practice (MVP)

Smarter Training

Overview
BoulderCoach is a hackathon-ready MVP that guides bouldering sessions with:

Voice cues pre/post attempt and silent attempts with beep cues.

Video Playback + grid overlay to mark High Point (0–100).

Under-10-second logging per attempt: success, High Point, RPE, notes.

Simple adaptive plan (rest & next action) based on Success / RPE / HP.

Session KPIs and CSV export—no backend required.

Optimized for reliability and UX: runs locally, no video uploads, and demos cleanly in 90–120 seconds.

Features
Core loop: PRE (voice) → ATTEMPT (video+grid, beeps) → POST (log) → REST (timer+suggestion) → SUMMARY (KPIs + CSV).

Playback mode: use existing clips; no live filming required.

Local persistence: localStorage (or SQLite in React Native).

Privacy-first: local by default; explicit CSV export.

Tech Stack
Frontend: React + TypeScript (PWA).

Audio: Web Audio (beeps), Web Speech (TTS) pre/post attempt.

Data: localStorage (MVP) with CSV export.

Optional analysis: Python + MediaPipe script for pose heuristics.
