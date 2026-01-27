import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create meals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                synced_at TIMESTAMP NOT NULL
            )
        """)

        # Create user_meal_selections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_meal_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meal_id INTEGER NOT NULL,
                selected_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meal_id) REFERENCES meals(id),
                UNIQUE(user_id, meal_id, selected_date)
            )
        """)

        conn.commit()
        conn.close()

    def clear_meals(self):
        """Clear all cached meals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meals")
        conn.commit()
        conn.close()

    def insert_meals(self, meals: List[str]):
        """Insert meals into database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        for meal in meals:
            cursor.execute(
                "INSERT OR IGNORE INTO meals (name, synced_at) VALUES (?, ?)",
                (meal, now),
            )

        conn.commit()
        conn.close()

    def get_meals(self) -> List[tuple]:
        """Get all cached meals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM meals ORDER BY id")
        meals = cursor.fetchall()
        conn.close()
        return meals

    def select_meal(self, user_id: int, meal_id: int, selected_date: str) -> bool:
        """Select a meal for a user on a specific date"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO user_meal_selections (user_id, meal_id, selected_date)
                VALUES (?, ?, ?)
                """,
                (user_id, meal_id, selected_date),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Meal already selected for this date
            return False
        finally:
            conn.close()

    def get_user_selections(self, user_id: int, week_start: str) -> List[tuple]:
        """Get user's meal selections for a week"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.name, ums.selected_date
            FROM user_meal_selections ums
            JOIN meals m ON ums.meal_id = m.id
            WHERE ums.user_id = ? AND ums.selected_date >= ?
            AND ums.selected_date < date(?, '+7 days')
            ORDER BY ums.selected_date
            """,
            (user_id, week_start, week_start),
        )
        selections = cursor.fetchall()
        conn.close()
        return selections

    def meal_exists(self) -> bool:
        """Check if any meals are cached"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meals")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
