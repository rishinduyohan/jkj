"""
Database Module for Budget Tracker App
Manages SQLite storage for expenses, categories, and budget settings with robust connection pooling.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple, Generator

DB_NAME = "budget_tracker.db"

class Database:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a connection with automatic commit and close."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Creates the necessary tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Expenses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,          -- YYYY-MM-DD
                    meal_type TEXT NOT NULL,     -- 'Breakfast', 'Lunch', 'Dinner', 'Other'
                    category TEXT NOT NULL,      -- 'Food & Dining', 'Groceries', 'Transportation', etc.
                    title TEXT NOT NULL,         -- Short title / description
                    amount REAL NOT NULL,        -- Spent amount
                    notes TEXT,                  -- Optional notes / details
                    created_at TEXT NOT NULL     -- ISO timestamp
                )
            """)

            # Budget Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Seed default settings if empty
            default_settings = {
                "monthly_budget": "500.0",
                "currency": "$",
                "breakfast_target": "5.0",
                "lunch_target": "10.0",
                "dinner_target": "12.0",
                "other_target": "10.0",
                "app_theme": "Dark"
            }
            for k, v in default_settings.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value)
                    VALUES (?, ?)
                """, (k, v))

    # --- Setting Operations ---
    def get_setting(self, key: str, default: str = "") -> str:
        with self.get_connection() as conn:
            row = conn.cursor().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))

    def get_all_settings(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            rows = conn.cursor().execute("SELECT key, value FROM settings").fetchall()
            return {row["key"]: row["value"] for row in rows}

    # --- Expense Operations ---
    def add_expense(self, date_str: str, meal_type: str, category: str, title: str, amount: float, notes: str = "") -> int:
        """Add a new expense entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (date, meal_type, category, title, amount, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str,
                meal_type,
                category,
                title.strip(),
                float(amount),
                notes.strip(),
                datetime.now().isoformat()
            ))
            return cursor.lastrowid

    def update_expense(self, expense_id: int, date_str: str, meal_type: str, category: str, title: str, amount: float, notes: str = "") -> bool:
        """Update an existing expense."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses
                SET date = ?, meal_type = ?, category = ?, title = ?, amount = ?, notes = ?
                WHERE id = ?
            """, (date_str, meal_type, category, title.strip(), float(amount), notes.strip(), expense_id))
            return cursor.rowcount > 0

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount > 0

    def get_expense_by_id(self, expense_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
            return dict(row) if row else None

    def get_expenses(self, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     meal_type: Optional[str] = None,
                     category: Optional[str] = None,
                     search: Optional[str] = None,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query expenses with optional filters and sorting."""
        query = "SELECT * FROM expenses WHERE 1=1"
        params: List[Any] = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if meal_type and meal_type != "All":
            query += " AND meal_type = ?"
            params.append(meal_type)
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (title LIKE ? OR notes LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        query += " ORDER BY date DESC, id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self.get_connection() as conn:
            rows = conn.cursor().execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_daily_meal_totals(self, target_date: str) -> Dict[str, float]:
        """Returns total amounts spent for Breakfast, Lunch, Dinner, and Other on a specific day."""
        totals = {"Breakfast": 0.0, "Lunch": 0.0, "Dinner": 0.0, "Other": 0.0}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT meal_type, SUM(amount) as total
                FROM expenses
                WHERE date = ?
                GROUP BY meal_type
            """, (target_date,)).fetchall()
            for row in rows:
                if row["meal_type"] in totals:
                    totals[row["meal_type"]] = float(row["total"] or 0.0)
                else:
                    totals["Other"] += float(row["total"] or 0.0)
        return totals

    def get_monthly_meal_totals(self, year_month: str) -> Dict[str, float]:
        """Returns total amount spent per meal type in a given month (format 'YYYY-MM')."""
        totals = {"Breakfast": 0.0, "Lunch": 0.0, "Dinner": 0.0, "Other": 0.0}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT meal_type, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY meal_type
            """, (f"{year_month}%",)).fetchall()
            for row in rows:
                if row["meal_type"] in totals:
                    totals[row["meal_type"]] = float(row["total"] or 0.0)
                else:
                    totals["Other"] += float(row["total"] or 0.0)
        return totals

    def get_monthly_category_totals(self, year_month: str) -> List[Tuple[str, float]]:
        """Returns list of (category, total_amount) for a given month, sorted descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY category
                ORDER BY total DESC
            """, (f"{year_month}%",)).fetchall()
            return [(row["category"], float(row["total"])) for row in rows]

    def get_monthly_daily_totals(self, year_month: str) -> List[Tuple[str, float]]:
        """Returns list of (date_str, daily_total) for each active day in the month."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT date, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY date
                ORDER BY date ASC
            """, (f"{year_month}%",)).fetchall()
            return [(row["date"], float(row["total"])) for row in rows]

    def get_yearly_monthly_totals(self, year_str: str) -> Dict[int, float]:
        """Returns map of month_int (1..12) -> total spend for that month."""
        res = {m: 0.0 for m in range(1, 13)}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT substr(date, 6, 2) as month_part, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY month_part
            """, (f"{year_str}%",)).fetchall()
            for row in rows:
                try:
                    m = int(row["month_part"])
                    res[m] = float(row["total"] or 0.0)
                except (ValueError, TypeError):
                    pass
        return res

    def get_yearly_meal_totals(self, year_str: str) -> Dict[str, float]:
        """Returns map of meal_type -> annual total for the given year."""
        totals = {"Breakfast": 0.0, "Lunch": 0.0, "Dinner": 0.0, "Other": 0.0}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT meal_type, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY meal_type
            """, (f"{year_str}%",)).fetchall()
            for row in rows:
                if row["meal_type"] in totals:
                    totals[row["meal_type"]] = float(row["total"] or 0.0)
                else:
                    totals["Other"] += float(row["total"] or 0.0)
        return totals

    def get_available_months_and_years(self) -> Tuple[List[str], List[str]]:
        """Returns sorted lists of distinct available years and YYYY-MM months in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT DISTINCT substr(date, 1, 7) as ym FROM expenses ORDER BY ym DESC").fetchall()
            months = [row["ym"] for row in rows if row["ym"]]
            
            y_rows = cursor.execute("SELECT DISTINCT substr(date, 1, 4) as y FROM expenses ORDER BY y DESC").fetchall()
            years = [row["y"] for row in y_rows if row["y"]]
            
            # Ensure current month and year are at least in list
            current_ym = date.today().strftime("%Y-%m")
            current_y = date.today().strftime("%Y")
            if current_ym not in months:
                months.insert(0, current_ym)
            if current_y not in years:
                years.insert(0, current_y)
                
            return months, years
