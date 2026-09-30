# SMS Panel Bot (Vercel + Firebase)

Telegram bot that enqueues SMS jobs across online devices found in multiple Firebase RTDBs.
Vercel-ready (webhook mode). State in Firebase.

## Features
- 📝 Template with `{code}` / `{link}` placeholders
- 🔥 Scans all Firebase URLs in `data/firebase_urls.txt`
- 📱 Upload numbers.txt (10-digit, +91 auto-added)
- 🔢 Upload codes.txt (cycled into messages)
- 🔗 Attach a link
- 📊 Status
- 🚀 Send — round-robin across online devices, 500ms stagger (2/sec)

## Deploy

1. Push to GitHub