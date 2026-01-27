from contextlib import contextmanager
from datetime import datetime
from typing import List, Generator
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging

from src.config import DATABASE_URL

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit/rollback"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


class Meal(Base):
    """SQLAlchemy model for meals"""
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    synced_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Meal(id={self.id}, name='{self.name}')>"


class UserMealSelection(Base):
    """SQLAlchemy model for user meal selections"""
    __tablename__ = "user_meal_selections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    selected_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "meal_id", "selected_date", name="unique_user_meal_date"),
    )

    def __repr__(self):
        return f"<UserMealSelection(user_id={self.user_id}, meal_id={self.meal_id}, date={self.selected_date})>"


class Database:
    """Database operations using SQLAlchemy"""

    def __init__(self):
        self.init_db()

    def init_db(self):
        """Initialize database schema"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def clear_meals(self):
        """Clear all cached meals"""
        try:
            with get_db_session() as session:
                session.query(Meal).delete()
            logger.info("Cleared all cached meals")
        except Exception as e:
            logger.error(f"Error clearing meals: {e}")
            raise

    def insert_meals(self, meals: List[str]):
        """Insert meals into database"""
        try:
            with get_db_session() as session:
                now = datetime.now()
                for meal_name in meals:
                    meal = Meal(name=meal_name, synced_at=now)
                    session.merge(meal)  # Use merge to handle duplicates gracefully
            logger.info(f"Inserted {len(meals)} meals")
        except Exception as e:
            logger.error(f"Error inserting meals: {e}")
            raise

    def get_meals(self) -> List[tuple]:
        """Get all cached meals"""
        try:
            with get_db_session() as session:
                meals = session.query(Meal.id, Meal.name).order_by(Meal.id).all()
                return meals
        except Exception as e:
            logger.error(f"Error fetching meals: {e}")
            raise

    def select_meal(self, user_id: int, meal_id: int, selected_date: str) -> bool:
        """Select a meal for a user on a specific date"""
        try:
            # Parse date string to date object
            from datetime import datetime as dt
            date_obj = dt.fromisoformat(selected_date).date()
            
            with get_db_session() as session:
                selection = UserMealSelection(
                    user_id=user_id,
                    meal_id=meal_id,
                    selected_date=date_obj,
                )
                session.add(selection)
            logger.info(f"Meal {meal_id} selected by user {user_id} for {selected_date}")
            return True
        except IntegrityError as e:
            logger.warning(f"Meal already selected: {e}")
            return False
        except Exception as e:
            logger.error(f"Error selecting meal: {e}")
            raise

    def get_user_selections(self, user_id: int, week_start: str) -> List[tuple]:
        """Get user's meal selections for a week"""
        try:
            # Parse date string
            from datetime import datetime as dt, timedelta
            week_start_date = dt.fromisoformat(week_start).date()
            week_end_date = week_start_date + timedelta(days=7)
            
            with get_db_session() as session:
                selections = (
                    session.query(Meal.name, UserMealSelection.selected_date)
                    .join(UserMealSelection, Meal.id == UserMealSelection.meal_id)
                    .filter(
                        UserMealSelection.user_id == user_id,
                        UserMealSelection.selected_date >= week_start_date,
                        UserMealSelection.selected_date < week_end_date,
                    )
                    .order_by(UserMealSelection.selected_date)
                    .all()
                )
                # Convert date objects to isoformat strings for consistency
                return [(meal_name, selected_date.isoformat()) for meal_name, selected_date in selections]
        except Exception as e:
            logger.error(f"Error fetching user selections: {e}")
            raise

    def meal_exists(self) -> bool:
        """Check if any meals are cached"""
        try:
            with get_db_session() as session:
                count = session.query(Meal).count()
                return count > 0
        except Exception as e:
            logger.error(f"Error checking meal existence: {e}")
            raise
