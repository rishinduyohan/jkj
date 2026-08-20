"""
Unit and Integration Tests for Budget Tracker Backend & Analytics
"""

import unittest
import os
import tempfile
from datetime import date
from database import Database
from analytics import AnalyticsEngine

class TestBudgetTrackerBackend(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)  # Close file descriptor immediately so SQLite can own it
        self.db = Database(self.temp_db_path)
        self.analytics = AnalyticsEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    def test_settings(self):
        self.assertEqual(self.db.get_setting("monthly_budget"), "500.0")
        self.assertEqual(self.db.get_setting("currency"), "$")
        
        self.db.set_setting("monthly_budget", "800.0")
        self.db.set_setting("currency", "€")
        self.assertEqual(self.db.get_setting("monthly_budget"), "800.0")
        self.assertEqual(self.db.get_setting("currency"), "€")
        self.assertEqual(self.analytics.get_currency(), "€")

    def test_expense_crud(self):
        # Add Breakfast
        id1 = self.db.add_expense("2026-08-20", "Breakfast", "Food & Dining", "Egg Sandwich", 5.50, "Morning cafe")
        self.assertGreater(id1, 0)

        # Add Lunch
        id2 = self.db.add_expense("2026-08-20", "Lunch", "Food & Dining", "Salad Bowl", 12.00)
        self.assertGreater(id2, 0)

        # Add Dinner
        id3 = self.db.add_expense("2026-08-20", "Dinner", "Food & Dining", "Pasta Dinner", 15.75)
        self.assertGreater(id3, 0)

        # Add Other
        id4 = self.db.add_expense("2026-08-20", "Other", "Transportation", "Bus Ticket", 2.50)
        self.assertGreater(id4, 0)

        # Verify daily totals
        daily_meals = self.db.get_daily_meal_totals("2026-08-20")
        self.assertAlmostEqual(daily_meals["Breakfast"], 5.50)
        self.assertAlmostEqual(daily_meals["Lunch"], 12.00)
        self.assertAlmostEqual(daily_meals["Dinner"], 15.75)
        self.assertAlmostEqual(daily_meals["Other"], 2.50)

        # Update expense
        self.db.update_expense(id1, "2026-08-20", "Breakfast", "Food & Dining", "Egg Sandwich + Coffee", 7.00, "With latte")
        exp = self.db.get_expense_by_id(id1)
        self.assertEqual(exp["title"], "Egg Sandwich + Coffee")
        self.assertAlmostEqual(exp["amount"], 7.00)

        # Delete expense
        self.assertTrue(self.db.delete_expense(id4))
        self.assertIsNone(self.db.get_expense_by_id(id4))

    def test_analytics_projection(self):
        # Insert known expenses for current month
        self.db.add_expense("2026-08-01", "Breakfast", "Food & Dining", "Meal", 10.00)
        self.db.add_expense("2026-08-01", "Lunch", "Food & Dining", "Meal", 15.00)
        self.db.add_expense("2026-08-01", "Dinner", "Food & Dining", "Meal", 20.00)

        proj = self.analytics.get_monthly_budget_projection("2026-08")
        self.assertEqual(proj["year_month"], "2026-08")
        self.assertEqual(proj["days_in_month"], 31)
        self.assertGreaterEqual(proj["current_spend"], 45.00)
        self.assertGreaterEqual(proj["proj_expected"], proj["proj_min"])
        self.assertGreaterEqual(proj["proj_max"], proj["proj_expected"])

    def test_monthly_and_yearly_reports(self):
        self.db.add_expense("2026-08-05", "Breakfast", "Food & Dining", "Pancakes", 8.00)
        self.db.add_expense("2026-08-05", "Lunch", "Food & Dining", "Burger", 14.00)
        self.db.add_expense("2026-08-05", "Other", "Groceries", "Snacks", 25.00)

        # Monthly report
        m_report = self.analytics.get_monthly_report_data("2026-08")
        self.assertEqual(m_report["transaction_count"], 3)
        self.assertAlmostEqual(m_report["total_spent"], 47.00)
        self.assertEqual(m_report["meal_totals"]["Breakfast"], 8.00)
        self.assertEqual(m_report["meal_totals"]["Lunch"], 14.00)
        self.assertEqual(m_report["meal_totals"]["Other"], 25.00)

        # Yearly report
        y_report = self.analytics.get_yearly_report_data("2026")
        self.assertAlmostEqual(y_report["total_spent"], 47.00)
        self.assertEqual(len(y_report["month_names"]), 12)

    def test_csv_export(self):
        self.db.add_expense("2026-08-10", "Lunch", "Food & Dining", "Test Export", 15.00)
        
        tmp_csv = tempfile.mktemp(suffix=".csv")
        self.assertTrue(self.analytics.export_monthly_csv("2026-08", tmp_csv))
        self.assertTrue(os.path.exists(tmp_csv))
        
        with open(tmp_csv, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Test Export", content)
            self.assertIn("15.00", content)
        
        if os.path.exists(tmp_csv):
            os.remove(tmp_csv)

if __name__ == "__main__":
    unittest.main()
