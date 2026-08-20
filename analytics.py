"""
Analytics and Projection Engine for Budget Tracker App
Handles spend calculations, forecasting monthly ranges, and generating report datasets.
"""

import calendar
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional
from database import Database

class AnalyticsEngine:
    def __init__(self, db: Database):
        self.db = db

    def get_currency(self) -> str:
        return self.db.get_setting("currency", "$")

    def format_currency(self, amount: float) -> str:
        symbol = self.get_currency()
        return f"{symbol}{amount:,.2f}"

    def get_daily_overview(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns overview for a specific date (defaults to today):
        - Meals: Breakfast, Lunch, Dinner, Other amounts
        - Daily Total
        - Daily Target limits comparison
        """
        if not target_date:
            target_date = date.today().strftime("%Y-%m-%d")

        meals = self.db.get_daily_meal_totals(target_date)
        total_day = sum(meals.values())

        # Meal targets from settings
        targets = {
            "Breakfast": float(self.db.get_setting("breakfast_target", "5.0")),
            "Lunch": float(self.db.get_setting("lunch_target", "10.0")),
            "Dinner": float(self.db.get_setting("dinner_target", "12.0")),
            "Other": float(self.db.get_setting("other_target", "10.0"))
        }
        day_target = sum(targets.values())

        return {
            "date": target_date,
            "meals": meals,
            "total": total_day,
            "targets": targets,
            "day_target": day_target,
            "is_over_target": total_day > day_target if day_target > 0 else False
        }

    def get_monthly_budget_projection(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates monthly budget metrics and approximate projected range.
        
        Range Calculation Formula:
        1. Days in month = total_days
        2. Days elapsed (if current month) = current_day
        3. Days remaining = total_days - current_day
        4. Current spend = sum(expenses in month)
        5. Daily Average Spend so far = current_spend / current_day
        6. Baseline daily minimum (breakfast + lunch + dinner targets or essential rate) = min_daily_rate
        7. Min Projected = current_spend + (min_daily_rate * remaining_days)
        8. Expected Projected = current_spend + (daily_avg * remaining_days)
        9. Upper Range Projected = current_spend + (max(daily_avg * 1.35, daily_avg + std_buffer) * remaining_days)
        """
        today = date.today()
        if not year_month:
            year_month = today.strftime("%Y-%m")

        target_year, target_month = map(int, year_month.split("-"))
        _, days_in_month = calendar.monthrange(target_year, target_month)

        is_current_month = (target_year == today.year and target_month == today.month)
        is_past_month = (target_year < today.year) or (target_year == today.year and target_month < today.month)

        meal_totals = self.db.get_monthly_meal_totals(year_month)
        current_spend = sum(meal_totals.values())
        monthly_budget = float(self.db.get_setting("monthly_budget", "500.0"))

        if is_past_month:
            # For past months, actual spend is the final total
            return {
                "year_month": year_month,
                "days_in_month": days_in_month,
                "days_elapsed": days_in_month,
                "days_remaining": 0,
                "current_spend": current_spend,
                "monthly_budget": monthly_budget,
                "daily_avg": current_spend / max(1, days_in_month),
                "proj_min": current_spend,
                "proj_expected": current_spend,
                "proj_max": current_spend,
                "status": "Completed",
                "remaining_budget": max(0.0, monthly_budget - current_spend),
                "budget_used_pct": (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0,
                "meal_totals": meal_totals,
                "is_current": False
            }

        if is_current_month:
            days_elapsed = max(1, today.day)
            days_remaining = max(0, days_in_month - today.day)
        else:
            # Future month
            days_elapsed = 0
            days_remaining = days_in_month

        daily_avg = current_spend / max(1, days_elapsed) if days_elapsed > 0 else (monthly_budget / days_in_month)
        
        # Meal targets baseline
        b_tgt = float(self.db.get_setting("breakfast_target", "5.0"))
        l_tgt = float(self.db.get_setting("lunch_target", "10.0"))
        d_tgt = float(self.db.get_setting("dinner_target", "12.0"))
        min_meal_rate = b_tgt + l_tgt + d_tgt

        # Conservative minimum daily rate
        conservative_rate = min(daily_avg * 0.75, min_meal_rate) if daily_avg > 0 else min_meal_rate
        proj_min = current_spend + (conservative_rate * days_remaining)

        # Expected based on current burn rate
        proj_expected = current_spend + (daily_avg * days_remaining)

        # Upper bound (accounting for weekend/heavy spending spikes)
        upper_rate = max(daily_avg * 1.30, daily_avg + 8.0)
        proj_max = current_spend + (upper_rate * days_remaining)

        remaining_budget = max(0.0, monthly_budget - current_spend)
        budget_used_pct = (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0

        # Health status
        if monthly_budget > 0:
            if proj_expected <= monthly_budget * 0.90:
                health = "Healthy (Well within Budget)"
                health_color = "#10B981"  # Emerald green
            elif proj_expected <= monthly_budget:
                health = "On Track (Approaching Target)"
                health_color = "#3B82F6"  # Blue
            elif proj_expected <= monthly_budget * 1.15:
                health = "Moderate Risk (Slightly Over Pace)"
                health_color = "#F59E0B"  # Amber
            else:
                health = "High Alert (Projected to Exceed Budget)"
                health_color = "#EF4444"  # Red
        else:
            health = "Budget Not Configured"
            health_color = "#9CA3AF"

        return {
            "year_month": year_month,
            "days_in_month": days_in_month,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "current_spend": current_spend,
            "monthly_budget": monthly_budget,
            "daily_avg": daily_avg,
            "proj_min": round(proj_min, 2),
            "proj_expected": round(proj_expected, 2),
            "proj_max": round(proj_max, 2),
            "health": health,
            "health_color": health_color,
            "remaining_budget": remaining_budget,
            "budget_used_pct": round(budget_used_pct, 1),
            "meal_totals": meal_totals,
            "is_current": True
        }

    def get_monthly_report_data(self, year_month: str) -> Dict[str, Any]:
        """Detailed breakdown for the monthly report."""
        meal_totals = self.db.get_monthly_meal_totals(year_month)
        cat_totals = self.db.get_monthly_category_totals(year_month)
        daily_totals = self.db.get_monthly_daily_totals(year_month)
        total_spent = sum(meal_totals.values())
        expenses = self.db.get_expenses(start_date=f"{year_month}-01", end_date=f"{year_month}-31")
        
        target_year, target_month = map(int, year_month.split("-"))
        _, days_in_month = calendar.monthrange(target_year, target_month)
        
        # Highest spending day
        highest_day = max(daily_totals, key=lambda x: x[1]) if daily_totals else ("None", 0.0)
        
        # Meal percentages
        meal_pcts = {}
        for m, amt in meal_totals.items():
            meal_pcts[m] = (amt / total_spent * 100) if total_spent > 0 else 0.0

        return {
            "year_month": year_month,
            "month_name": datetime.strptime(year_month, "%Y-%m").strftime("%B %Y"),
            "total_spent": total_spent,
            "daily_avg": total_spent / max(1, len(daily_totals)) if daily_totals else 0.0,
            "transaction_count": len(expenses),
            "highest_day": highest_day,
            "meal_totals": meal_totals,
            "meal_percentages": meal_pcts,
            "category_totals": cat_totals,
            "daily_totals": daily_totals,
            "expenses": expenses
        }

    def get_yearly_report_data(self, year_str: str) -> Dict[str, Any]:
        """Detailed breakdown for the yearly report."""
        monthly_totals = self.db.get_yearly_monthly_totals(year_str)
        meal_totals = self.db.get_yearly_meal_totals(year_str)
        total_spent = sum(monthly_totals.values())
        
        # Monthly names and values
        month_names = [calendar.month_abbr[m] for m in range(1, 13)]
        month_values = [monthly_totals[m] for m in range(1, 13)]
        
        # Active months with spending > 0
        active_months = [v for v in month_values if v > 0]
        avg_monthly = (total_spent / len(active_months)) if active_months else 0.0
        
        # Highest & lowest spend months
        highest_month_idx = month_values.index(max(month_values)) if any(month_values) else 0
        highest_month = (month_names[highest_month_idx], month_values[highest_month_idx])
        
        return {
            "year": year_str,
            "total_spent": total_spent,
            "avg_monthly": avg_monthly,
            "active_months_count": len(active_months),
            "highest_month": highest_month,
            "month_names": month_names,
            "month_values": month_values,
            "meal_totals": meal_totals
        }

    def export_monthly_csv(self, year_month: str, filepath: str) -> bool:
        """Export monthly transaction report to a CSV file."""
        import csv
        expenses = self.db.get_expenses(start_date=f"{year_month}-01", end_date=f"{year_month}-31")
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Meal/Type", "Category", "Description", f"Amount ({self.get_currency()})", "Notes", "Created At"])
                for exp in expenses:
                    writer.writerow([
                        exp["id"],
                        exp["date"],
                        exp["meal_type"],
                        exp["category"],
                        exp["title"],
                        f"{exp['amount']:.2f}",
                        exp["notes"],
                        exp["created_at"]
                    ])
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False

    def export_yearly_csv(self, year_str: str, filepath: str) -> bool:
        """Export yearly summary and transactions to CSV."""
        import csv
        expenses = self.db.get_expenses(start_date=f"{year_str}-01-01", end_date=f"{year_str}-12-31")
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([f"Annual Budget Report for {year_str}"])
                writer.writerow([])
                writer.writerow(["ID", "Date", "Meal/Type", "Category", "Description", f"Amount ({self.get_currency()})", "Notes"])
                for exp in expenses:
                    writer.writerow([
                        exp["id"],
                        exp["date"],
                        exp["meal_type"],
                        exp["category"],
                        exp["title"],
                        f"{exp['amount']:.2f}",
                        exp["notes"]
                    ])
            return True
        except Exception as e:
            print(f"Error exporting yearly CSV: {e}")
            return False
