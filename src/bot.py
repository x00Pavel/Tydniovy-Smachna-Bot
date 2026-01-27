import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.config import TELEGRAM_BOT_TOKEN, TIMEZONE
from src.database import Database
from src.sheets import SheetsClient
from src.utils import get_current_week_start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Initialize database and sheets client
db = Database()
sheets_client = SheetsClient()

# Scheduler
scheduler = BackgroundScheduler()


async def sync_meals():
    """Sync meals from Google Sheets to database"""
    try:
        logger.info("Syncing meals from Google Sheets...")
        meals = sheets_client.fetch_meals()

        # Clear old meals and insert new ones
        db.clear_meals()
        if meals:
            db.insert_meals(meals)
            logger.info(f"Successfully synced {len(meals)} meals")
        else:
            logger.warning("No meals fetched from sheet")
    except Exception as e:
        logger.error(f"Error syncing meals: {e}")


def schedule_midnight_sync():
    """Schedule daily meal sync at midnight"""
    trigger = CronTrigger(hour=0, minute=0, timezone=TIMEZONE)
    scheduler.add_job(sync_meals, trigger=trigger, id="midnight_sync")
    logger.info(f"Scheduled daily sync at midnight ({TIMEZONE})")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    try:
        await message.answer(
            "Welcome to Meal Planner Bot! 🍽️\n\n"
            "Use /meals to see available meals and plan your week.\n"
            "Use /view to see your selected meals for this week.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /start command: {e}")


@dp.message(Command("meals"))
async def cmd_meals(message: types.Message):
    """Handle /meals command - display available meals as buttons"""
    try:
        meals = db.get_meals()

        if not meals:
            await message.answer("No meals available at the moment. Please try again later.")
            return

        # Create inline keyboard with meal buttons
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=meal[1], callback_data=f"meal_{meal[0]}")]
                for meal in meals
            ]
        )

        await message.answer(
            "Select a meal to plan for this week:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /meals command: {e}")
        await message.answer("An error occurred while fetching meals.")


@dp.message(Command("view"))
async def cmd_view(message: types.Message):
    """Handle /view command - show user's selected meals for the week"""
    try:
        week_start = get_current_week_start()
        selections = db.get_user_selections(message.from_user.id, week_start)

        if not selections:
            await message.answer("You haven't selected any meals for this week yet.")
            return

        # Format selections by date
        selections_text = "<b>Your meals for this week:</b>\n\n"
        for meal_name, selected_date in selections:
            selections_text += f"<b>{selected_date}:</b> {meal_name}\n"

        await message.answer(selections_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /view command: {e}")
        await message.answer("An error occurred while retrieving your selections.")


@dp.callback_query(F.data.startswith("meal_"))
async def process_meal_selection(callback_query: types.CallbackQuery):
    """Handle meal button clicks"""
    try:
        meal_id = int(callback_query.data.split("_")[1])
        user_id = callback_query.from_user.id
        today = datetime.now().date().isoformat()

        # Select the meal
        success = db.select_meal(user_id, meal_id, today)

        if success:
            await callback_query.answer("✅ Meal selected for today!", show_alert=False)
            await callback_query.message.edit_text(
                "Meal selected for today! Use /view to see all your selections."
            )
        else:
            await callback_query.answer(
                "⚠️ You already selected a meal for today!", show_alert=True
            )
    except Exception as e:
        logger.error(f"Error processing meal selection: {e}")
        await callback_query.answer("An error occurred while selecting the meal.", show_alert=True)


async def main():
    """Start the bot"""
    try:
        # Initial sync on startup
        logger.info("Starting bot...")
        await sync_meals()

        # Start scheduler
        if not scheduler.running:
            scheduler.start()
            schedule_midnight_sync()
            logger.info("Scheduler started")

        # Start polling
        logger.info("Bot is running. Polling for messages...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await bot.session.close()
        if scheduler.running:
            scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
