import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src.config import TELEGRAM_BOT_TOKEN, TIMEZONE, WEBHOOK_URL, WEBHOOK_PORT, WEBHOOK_PATH, WEBHOOK_SECRET
from src.database import Database
from src.sheets import SheetsClient
from src.utils import get_current_week_start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Define states for conversation
class AddMealState(StatesGroup):
    """States for adding a new meal"""
    waiting_for_meal_name = State()

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


@dp.startup
async def on_startup():
    """Handle bot startup"""
    logger.info("Bot starting up...")
    await sync_meals()

    if not scheduler.running:
        scheduler.start()
        schedule_midnight_sync()
        logger.info("Scheduler started")

    if WEBHOOK_URL:
        # Set webhook on Telegram servers
        webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)
        logger.info(f"Webhook set to: {webhook_url}")


@dp.shutdown
async def on_shutdown():
    """Handle bot shutdown"""
    logger.info("Bot shutting down...")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    try:
        await message.answer(
            "Welcome to Meal Planner Bot! 🍽️\n\n"
            "Use /meals to see available meals and plan your week.\n"
            "Use /view to see your selected meals for this week.\n"
            "Use /addmeal to add a new meal to the sheet.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /start command: {e}")


@dp.message(Command("addmeal"))
async def cmd_addmeal(message: types.Message, state: FSMContext):
    """Handle /addmeal command - start conversation to add a new meal"""
    try:
        await state.set_state(AddMealState.waiting_for_meal_name)
        await message.answer(
            "What meal would you like to add? Please enter the meal name:",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /addmeal command: {e}")
        await message.answer("An error occurred. Please try again.")


@dp.message(AddMealState.waiting_for_meal_name)
async def process_meal_name(message: types.Message, state: FSMContext):
    """Handle meal name input and add to sheet"""
    try:
        meal_name = message.text.strip()
        
        if not meal_name or len(meal_name) < 2:
            await message.answer("Please enter a valid meal name (at least 2 characters).")
            return
        
        # Add meal to Google Sheet
        success = sheets_client.add_meal(meal_name)
        
        if success:
            await message.answer(
                f"✅ Meal '<b>{meal_name}</b>' has been added to the sheet!",
                parse_mode="HTML",
            )
            logger.info(f"User {message.from_user.id} added meal: {meal_name}")
        else:
            await message.answer(
                "❌ Failed to add meal to the sheet. Please try again later.",
                parse_mode="HTML",
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error processing meal name: {e}")
        await message.answer("An error occurred while adding the meal. Please try again.")
        await state.clear()



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


def main() -> None:
    """Start the bot with webhook or polling based on configuration"""
    if WEBHOOK_URL:
        start_webhook()
    else:
        asyncio.run(start_polling())


def start_webhook() -> None:
    """Start bot using webhook mode (behind reverse proxy)"""
    logger.info("Starting bot in WEBHOOK mode")
    logger.info(f"Webhook URL: {WEBHOOK_URL}")
    logger.info(f"Webhook PORT: {WEBHOOK_PORT}")
    logger.info(f"Webhook PATH: {WEBHOOK_PATH}")

    # Create aiohttp web app
    app = web.Application()

    # Create webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )

    # Register webhook handler on app
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to app
    setup_application(app, dp, bot=bot)

    # Run web app (blocks forever)
    web.run_app(app, host="0.0.0.0", port=WEBHOOK_PORT)


async def start_polling() -> None:
    """Start bot using polling mode (fallback)"""
    logger.info("Starting bot in POLLING mode")
    logger.info("Bot is running. Polling for messages...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    main()

