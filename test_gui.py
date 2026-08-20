"""
GUI Automation and Headless verification test for BudgetTrackerApp
"""

import unittest
from datetime import date
from app import BudgetTrackerApp

class TestBudgetTrackerGUI(unittest.TestCase):
    def setUp(self):
        self.app = BudgetTrackerApp()
        self.app.withdraw()  # Don't show window on screen during automated test

    def tearDown(self):
        self.app.destroy()

    def test_gui_initialization_and_navigation(self):
        # Verify default dashboard page is loaded
        self.assertIn("dashboard", self.app.pages)
        self.assertIn("expenses", self.app.pages)
        self.assertIn("monthly", self.app.pages)
        self.assertIn("yearly", self.app.pages)
        self.assertIn("settings", self.app.pages)

        # Test navigation to each page
        for page_name in ["expenses", "monthly", "yearly", "settings", "dashboard"]:
            self.app.show_page(page_name)
            self.app.update_idletasks()

        # Add a sample expense directly and refresh
        self.app.db.add_expense(date.today().strftime("%Y-%m-%d"), "Breakfast", "Food & Dining", "Croissant", 4.50)
        self.app.refresh_dashboard()
        self.app.refresh_expenses_table()
        self.app.refresh_monthly_report()
        self.app.refresh_yearly_report()
        self.app.update_idletasks()

        # Check that table has items
        items = self.app.exp_tree.get_children()
        self.assertGreaterEqual(len(items), 1)

if __name__ == "__main__":
    unittest.main()
