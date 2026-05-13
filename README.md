# Telegram AI Assistant Bot

Simple Telegram bot powered by the OpenAI Responses API.

## Live Demo

Try the bot on Telegram: [@ZillmanBOTbot](https://t.me/@ZillmanBOTbot)

## Features

- AI replies in Telegram
- Per-user conversation context
- `/start`, `/help`, and `/reset` commands
- Environment variables for secrets
- Typing indicator while the bot thinks
- Basic protection from overlapping requests by the same user

## Tech Stack

- Python
- python-telegram-bot
- OpenAI Python SDK
- python-dotenv

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and get your Telegram token.
2. Create an OpenAI API key.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:

```env
OPENAI_API_KEY=sk-your-openai-api-key
TELEGRAM_BOT_TOKEN=123456789:your-telegram-bot-token
OPENAI_MODEL=gpt-4.1-mini
MAX_OUTPUT_TOKENS=700
```

5. Run the bot:

```bash
python bot.py
```
## Deployment

This bot is deployed on Railway and runs as a background Python service.

The project uses environment variables for all private values:

```env
OPENAI_API_KEY=your-openai-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_MODEL=gpt-4.1-nano
MAX_OUTPUT_TOKENS=700
```

Railway automatically redeploys the bot after every push to the main branch.

## Security

Do not commit `.env` to GitHub. It contains private API keys and tokens.
