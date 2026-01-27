from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_current_week_start() -> str:
    """Get the start of the current week (Monday)"""
    today = datetime.now().date()
    # Monday is 0, Sunday is 6
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start.isoformat()


def get_week_days() -> list[str]:
    """Get all days of the current week (Monday to Sunday)"""
    week_start = get_current_week_start()
    start_date = datetime.fromisoformat(week_start).date()
    days = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        days.append(day.isoformat())
    return days


def is_cache_valid(synced_at_iso: str) -> bool:
    """Check if cache is still valid (same day)"""
    try:
        synced_date = datetime.fromisoformat(synced_at_iso).date()
        today = datetime.now().date()
        return synced_date == today
    except Exception as e:
        logger.error(f"Error checking cache validity: {e}")
        return False
