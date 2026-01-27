# Vita Telegram Bot - Meal Planner

A Telegram bot that integrates with Google Sheets to display meals and enable weekly meal planning with SQLite persistence.

## Features

- 🤖 Telegram bot interface using aiogram
- 📊 Google Sheets integration for meal data
- 💾 SQLite database for caching and user selections
- 📅 Weekly meal planning (Monday-Sunday)
- 🔄 Automatic daily cache refresh at midnight
- 👤 Per-user meal selections

## Project Structure

```
vita-tg-bot/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot logic and handlers
│   ├── config.py           # Configuration and environment variables
│   ├── database.py         # SQLite database operations
│   ├── sheets.py           # Google Sheets API integration
│   └── utils.py            # Utility functions
├── main.py                 # Entry point
├── pyproject.toml          # Project dependencies (uv)
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Setup

### 1. Install uv (dependency manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and navigate to project

```bash
cd ./vita-tg-bot
```

### 3. Create .env file

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `GOOGLE_SHEET_ID`: Your Google Sheet ID (from the URL)
- `GOOGLE_CREDENTIALS_PATH`: Path to your Google service account JSON (already provided)
- `TIMEZONE`: Your timezone (e.g., `Europe/London`, `America/New_York`, default: `UTC`)
- `DATABASE_PATH`: Path to SQLite database file (default: `./meals.db`)

### 4. Set up Google Sheets

1. Ensure your Google Sheet has meals listed in column A, starting from row 1
2. Each row should contain one meal name
3. Share the sheet with the service account email from your credentials JSON

### 5. Install dependencies

```bash
uv sync
```

### 6. Run the bot

```bash
uv run main.py
```

## Bot Commands

- `/start` - Welcome message and instructions
- `/meals` - Display available meals as interactive buttons
- `/view` - Show your selected meals for the current week

## How It Works

1. **Startup**: Bot fetches all meals from Google Sheet and caches them in SQLite
2. **Daily Cache**: Cache automatically refreshes at midnight (configurable timezone)
3. **User Interaction**: Users click meal buttons to select meals for today
4. **Selection Storage**: Selected meals are stored in SQLite with user ID and date
5. **View Week**: Users can view all their selected meals for the current week

## Database Schema

### meals table
- `id`: Primary key
- `name`: Meal name (unique)
- `synced_at`: Timestamp of last sync

### user_meal_selections table
- `id`: Primary key
- `user_id`: Telegram user ID
- `meal_id`: Reference to meals table
- `selected_date`: Date of selection (ISO format)
- `created_at`: Timestamp of selection

## Development Notes

- All database operations are synchronous for simplicity
- Bot uses aiogram 3.x (async framework)
- Meal cache expires at midnight and is refreshed automatically
- Each user maintains independent meal selections
- Week is always Monday-Sunday (configurable timezone)

## Troubleshooting

### Bot not starting
- Check `TELEGRAM_BOT_TOKEN` is valid
- Verify internet connection

### Google Sheets API errors
- Ensure credentials file path is correct
- Verify service account has access to the sheet
- Check sheet ID is correct in `.env`

### No meals fetched
- Verify meals are in column A of the sheet
- Check that service account email has Viewer access to sheet
- Ensure column A is not empty

## Future Enhancements

- [ ] Database persistence for multi-day planning
- [ ] User preferences and dietary restrictions
- [ ] Shopping list generation
- [ ] Nutrition information display
- [ ] Admin commands for sheet management
- [ ] Multiple meal selections per day
- [ ] Navigation to previous/future weeks
