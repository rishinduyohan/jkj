"""
My Budget Tracker Desktop Application
Main Desktop GUI Application built with CustomTkinter and SQLite.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import os
import calendar
from typing import Optional, List, Dict, Any, Tuple

from database import Database
from analytics import AnalyticsEngine
from components import THEME, get_meal_color, StatCard, MealPill, ChartContainer

# Global App Styling Configurations
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Other"]
CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Utilities & Bills",
    "Health & Fitness",
    "Travel",
    "Personal Care",
    "Education",
    "Miscellaneous"
]

class BudgetTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("My Budget Tracker")
        self.geometry("1240x800")
        self.minsize(1080, 700)
        self.configure(fg_color=THEME["bg_dark"])

        # Database & Analytics
        self.db = Database()
        self.analytics = AnalyticsEngine(self.db)
        
        # Load theme setting
        theme_setting = self.db.get_setting("app_theme", "Dark")
        ctk.set_appearance_mode(theme_setting)

        # Main Layout Grid (2 Columns: Sidebar and Content Area)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Setup Views
        self._build_sidebar()
        
        # Container for pages
        self.content_container = ctk.CTkFrame(self, fg_color=THEME["bg_dark"], corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Pages Dictionary
        self.pages = {}
        self._init_pages()

        # Show default page (Dashboard)
        self.show_page("dashboard")

        # Check First Time Setup
        self.after(300, self.check_first_time_setup)

    def check_first_time_setup(self):
        """Prompt user on first launch to set their estimated monthly budget."""
        is_done = self.db.get_setting("first_setup_done", "false")
        if is_done.lower() != "true":
            self.open_first_time_budget_modal()

    def open_first_time_budget_modal(self):
        """Welcome popup for first-time onboarding to set estimated budget & currency."""
        modal = ctk.CTkToplevel(self)
        modal.title("Welcome to My Budget Tracker")
        modal.geometry("500x560")
        modal.minsize(460, 520)
        modal.configure(fg_color=THEME["bg_dark"])
        modal.transient(self)
        modal.grab_set()

        m_frame = ctk.CTkFrame(
            modal, 
            fg_color=THEME["card_dark"], 
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_dark"]
        )
        m_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            m_frame, 
            text="✨ Welcome to My Budget Tracker", 
            font=("Segoe UI", 16), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            m_frame, 
            text="Please set your estimated monthly budget & currency to begin tracking.", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=20, pady=(0, 16))

        inner_box = ctk.CTkFrame(m_frame, fg_color="transparent")
        inner_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Currency Selection
        ctk.CTkLabel(
            inner_box, 
            text="Choose Currency:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 3))

        curr_combo = ctk.CTkComboBox(
            inner_box, 
            values=["Rs", "$", "€", "£", "₹", "¥", "A$", "C$"],
            width=160
        )
        curr_combo.pack(anchor="w", pady=(0, 12))
        curr_combo.set(self.db.get_setting("currency", "Rs"))

        # Estimated Monthly Budget
        ctk.CTkLabel(
            inner_box, 
            text="Estimated Monthly Budget Limit:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 3))

        budget_entry = ctk.CTkEntry(inner_box, placeholder_text="e.g. 15000.00", font=("Segoe UI", 12))
        budget_entry.pack(fill="x", pady=(0, 14))
        budget_entry.insert(0, self.db.get_setting("monthly_budget", "1500.0"))

        # Daily Meal Baseline Targets
        ctk.CTkLabel(
            inner_box, 
            text="Daily Meal Budget Estimates:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 4))

        meal_grid = ctk.CTkFrame(inner_box, fg_color="transparent")
        meal_grid.pack(fill="x", pady=(0, 16))
        meal_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(meal_grid, text="🍳 Breakfast:", font=("Segoe UI", 11), text_color=THEME["meal_breakfast"]).grid(row=0, column=0, sticky="w", padx=2, pady=2)
        b_in = ctk.CTkEntry(meal_grid, width=120)
        b_in.grid(row=1, column=0, sticky="w", padx=2, pady=(0, 8))
        b_in.insert(0, self.db.get_setting("breakfast_target", "5.0"))

        ctk.CTkLabel(meal_grid, text="🥗 Lunch:", font=("Segoe UI", 11), text_color=THEME["meal_lunch"]).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        l_in = ctk.CTkEntry(meal_grid, width=120)
        l_in.grid(row=1, column=1, sticky="w", padx=2, pady=(0, 8))
        l_in.insert(0, self.db.get_setting("lunch_target", "10.0"))

        ctk.CTkLabel(meal_grid, text="🍲 Dinner:", font=("Segoe UI", 11), text_color=THEME["meal_dinner"]).grid(row=2, column=0, sticky="w", padx=2, pady=2)
        d_in = ctk.CTkEntry(meal_grid, width=120)
        d_in.grid(row=3, column=0, sticky="w", padx=2, pady=(0, 4))
        d_in.insert(0, self.db.get_setting("dinner_target", "12.0"))

        ctk.CTkLabel(meal_grid, text="🛍️ Other:", font=("Segoe UI", 11), text_color=THEME["meal_other"]).grid(row=2, column=1, sticky="w", padx=2, pady=2)
        o_in = ctk.CTkEntry(meal_grid, width=120)
        o_in.grid(row=3, column=1, sticky="w", padx=2, pady=(0, 4))
        o_in.insert(0, self.db.get_setting("other_target", "10.0"))

        def save_and_continue():
            try:
                mb_val = float(budget_entry.get().strip())
                b_val = float(b_in.get().strip())
                l_val = float(l_in.get().strip())
                d_val = float(d_in.get().strip())
                o_val = float(o_in.get().strip())
                c_val = curr_combo.get().strip()

                if mb_val <= 0:
                    messagebox.showerror("Error", "Please enter a budget greater than zero.")
                    return

                self.db.set_setting("monthly_budget", str(mb_val))
                self.db.set_setting("currency", c_val)
                self.db.set_setting("breakfast_target", str(b_val))
                self.db.set_setting("lunch_target", str(l_val))
                self.db.set_setting("dinner_target", str(d_val))
                self.db.set_setting("other_target", str(o_val))
                self.db.set_setting("first_setup_done", "true")

                modal.destroy()
                self.refresh_dashboard()
                self.load_settings_values()

                # Prompt to add first expense
                if messagebox.askyesno("Setup Complete", "Budget setup successfully! Would you like to log your first expense now?"):
                    self.open_quick_meal_modal()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please ensure all values are valid numbers.")

        save_btn = ctk.CTkButton(
            inner_box, 
            text="✓ Save Budget & Start Tracking", 
            font=("Segoe UI", 12),
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            height=38, 
            corner_radius=8, 
            cursor="hand2",
            command=save_and_continue
        )
        save_btn.pack(fill="x", pady=(10, 0))

    def _build_sidebar(self):
        """Constructs modern left sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self, 
            width=230, 
            corner_radius=0, 
            fg_color=THEME["sidebar_dark"],
            border_width=1,
            border_color=THEME["border_dark"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # App Logo & Branding
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(22, 18))

        logo_lbl = ctk.CTkLabel(
            brand_frame, 
            text="💰 My Budget Tracker", 
            font=("Segoe UI", 16), 
            text_color=THEME["text_main"]
        )
        logo_lbl.pack(anchor="w")

        sub_logo = ctk.CTkLabel(
            brand_frame, 
            text="Smart Expense & Meal Tracker", 
            font=("Segoe UI", 10), 
            text_color=THEME["text_sub"]
        )
        sub_logo.pack(anchor="w", pady=(2, 0))

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("expenses", "💳  Daily Expenses"),
            ("monthly", "📊  Monthly Report"),
            ("yearly", "📈  Yearly Report"),
            ("settings", "⚙️  Budget & Settings")
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                font=("Segoe UI", 12),
                fg_color="transparent",
                text_color=THEME["text_muted"],
                hover_color=THEME["card_hover"],
                cursor="hand2",
                command=lambda k=key: self.show_page(k)
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[key] = btn

        # Quick Add Section in Sidebar
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=THEME["border_dark"])
        sep.pack(fill="x", padx=14, pady=16)

        quick_lbl = ctk.CTkLabel(
            self.sidebar, 
            text="QUICK LOG MEAL", 
            font=("Segoe UI", 10), 
            text_color=THEME["text_sub"]
        )
        quick_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        quick_meals = [
            ("🍳 Breakfast", "Breakfast", THEME["meal_breakfast"]),
            ("🥗 Lunch", "Lunch", THEME["meal_lunch"]),
            ("🍲 Dinner", "Dinner", THEME["meal_dinner"]),
            ("🛍️ Other Exp", "Other", THEME["meal_other"]),
        ]

        for label, meal_type, color in quick_meals:
            qbtn = ctk.CTkButton(
                self.sidebar,
                text=label,
                height=32,
                corner_radius=6,
                font=("Segoe UI", 11),
                fg_color=THEME["card_dark"],
                text_color=color,
                hover_color=THEME["card_hover"],
                border_width=1,
                border_color=THEME["border_dark"],
                anchor="w",
                cursor="hand2",
                command=lambda m=meal_type: self.open_quick_meal_modal(m)
            )
            qbtn.pack(fill="x", padx=12, pady=3)

        # Bottom Info
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=16, pady=16)
        
        self.today_date_lbl = ctk.CTkLabel(
            bottom_frame, 
            text=date.today().strftime("%A, %b %d"), 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        )
        self.today_date_lbl.pack(anchor="w")

    def _init_pages(self):
        """Initializes all view frames."""
        self.pages["dashboard"] = self._create_dashboard_page()
        self.pages["expenses"] = self._create_expenses_page()
        self.pages["monthly"] = self._create_monthly_page()
        self.pages["yearly"] = self._create_yearly_page()
        self.pages["settings"] = self._create_settings_page()

    def show_page(self, page_key: str):
        """Switches active page with visual highlight in sidebar."""
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(
                    fg_color=THEME["accent_primary"], 
                    text_color="#FFFFFF",
                    hover_color=THEME["accent_hover"]
                )
            else:
                btn.configure(
                    fg_color="transparent", 
                    text_color=THEME["text_muted"],
                    hover_color=THEME["card_hover"]
                )

        # Display active page and forget all others
        for key, page in self.pages.items():
            if key == page_key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_forget()

        # Refresh page data upon opening
        if page_key == "dashboard":
            self.refresh_dashboard()
        elif page_key == "expenses":
            self.refresh_expenses_table()
        elif page_key == "monthly":
            self.refresh_monthly_report()
        elif page_key == "yearly":
            self.refresh_yearly_report()
        elif page_key == "settings":
            self.load_settings_values()

    # ==========================================
    # 1. DASHBOARD VIEW
    # ==========================================
    def _create_dashboard_page(self) -> ctk.CTkScrollableFrame:
        page = ctk.CTkScrollableFrame(self.content_container, fg_color=THEME["bg_dark"])
        
        # Header Row
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 14))
        
        ctk.CTkLabel(
            header, 
            text="Financial Dashboard", 
            font=("Segoe UI", 20), 
            text_color=THEME["text_main"]
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header, 
            text="➕ Add Expense", 
            font=("Segoe UI", 12),
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            corner_radius=8, 
            height=34,
            cursor="hand2",
            command=lambda: self.open_quick_meal_modal()
        )
        add_btn.pack(side="right")

        # Plain Text Forecast Box
        self.forecast_box = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        self.forecast_box.pack(fill="x", padx=24, pady=(0, 14))

        f_inner = ctk.CTkFrame(self.forecast_box, fg_color="transparent")
        f_inner.pack(fill="x", padx=16, pady=12)

        self.forecast_text_lbl = ctk.CTkLabel(
            f_inner,
            text="Calculating spending forecast...",
            font=("Segoe UI", 12),
            text_color=THEME["text_main"],
            justify="left",
            wraplength=850
        )
        self.forecast_text_lbl.pack(anchor="w")

        # Essential KPI Metric Cards Grid (3 Cards for clean simplicity)
        kpi_frame = ctk.CTkFrame(page, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=24, pady=(0, 14))
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.kpi_today = StatCard(kpi_frame, title="Today's Spend", value="$0.00", subtext="Daily target: $37.00", icon_text="📅", accent_color="#38BDF8")
        self.kpi_today.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.kpi_month = StatCard(kpi_frame, title="This Month Total", value="$0.00", subtext="Budget: $500.00", icon_text="📊", accent_color="#818CF8")
        self.kpi_month.grid(row=0, column=1, sticky="nsew", padx=4)

        self.kpi_remaining = StatCard(kpi_frame, title="Budget Remaining", value="$0.00", subtext="Remaining funds", icon_text="💰", accent_color="#10B981")
        self.kpi_remaining.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        # Today's Meals Section
        meal_section = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        meal_section.pack(fill="x", padx=24, pady=(0, 14))

        m_header = ctk.CTkFrame(meal_section, fg_color="transparent")
        m_header.pack(fill="x", padx=16, pady=(10, 6))
        ctk.CTkLabel(
            m_header, 
            text="🍽️ Today's Meal Breakdown", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(side="left")

        pills_frame = ctk.CTkFrame(meal_section, fg_color="transparent")
        pills_frame.pack(fill="x", padx=16, pady=(0, 12))
        pills_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.pill_breakfast = MealPill(pills_frame, meal_name="Breakfast", amount_str="$0.00", target_str="$5.00")
        self.pill_breakfast.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.pill_lunch = MealPill(pills_frame, meal_name="Lunch", amount_str="$0.00", target_str="$10.00")
        self.pill_lunch.grid(row=0, column=1, sticky="nsew", padx=3)

        self.pill_dinner = MealPill(pills_frame, meal_name="Dinner", amount_str="$0.00", target_str="$12.00")
        self.pill_dinner.grid(row=0, column=2, sticky="nsew", padx=3)

        self.pill_other = MealPill(pills_frame, meal_name="Other", amount_str="$0.00", target_str="$10.00")
        self.pill_other.grid(row=0, column=3, sticky="nsew", padx=(4, 0))

        # Recent Transactions Header & List
        recent_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        recent_card.pack(fill="x", padx=24, pady=(0, 20))

        r_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        r_header.pack(fill="x", padx=16, pady=(10, 6))
        ctk.CTkLabel(
            r_header, 
            text="🕒 Recent Activity", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(side="left")
        
        view_all_btn = ctk.CTkButton(
            r_header, 
            text="View All →", 
            font=("Segoe UI", 11),
            fg_color="transparent", 
            text_color=THEME["accent_light"],
            hover_color=THEME["card_hover"], 
            width=80,
            cursor="hand2",
            command=lambda: self.show_page("expenses")
        )
        view_all_btn.pack(side="right")

        self.recent_list_frame = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_list_frame.pack(fill="x", padx=16, pady=(0, 10))

        return page

    def refresh_dashboard(self):
        """Updates all values and plain-text forecast on Dashboard."""
        today_str = date.today().strftime("%Y-%m-%d")
        ym_str = date.today().strftime("%Y-%m")
        cur = self.analytics.get_currency()

        # Daily overview
        daily = self.analytics.get_daily_overview(today_str)
        self.kpi_today.update_values(
            self.analytics.format_currency(daily["total"]),
            f"Daily target: {cur}{daily['day_target']:.2f}"
        )

        # Monthly Projection
        proj = self.analytics.get_monthly_budget_projection(ym_str)
        self.kpi_month.update_values(
            self.analytics.format_currency(proj["current_spend"]),
            f"Budget: {cur}{proj['monthly_budget']:.2f} ({proj['budget_used_pct']}%)"
        )
        self.kpi_remaining.update_values(
            self.analytics.format_currency(proj["remaining_budget"]),
            f"{proj['days_remaining']} days remaining"
        )

        # Update Plain Text Forecast Sentence
        daily_avg = proj["daily_avg"]
        proj_exp = proj["proj_expected"]
        mb = proj["monthly_budget"]
        rem = mb - proj_exp

        if proj["current_spend"] == 0:
            forecast_msg = (
                f"💡 Monthly Goal: Your budget is set to {cur}{mb:,.2f}. "
                f"Use '+ Add Expense' or the Quick Log buttons to record your first meal/expense!"
            )
            self.forecast_box.configure(border_color=THEME["border_dark"])
            self.forecast_text_lbl.configure(text=forecast_msg, text_color=THEME["text_main"])
        elif rem >= 0:
            forecast_msg = (
                f"💡 Spending Forecast: If you spend ~{cur}{daily_avg:.2f} per day, "
                f"your estimated total this month will be {cur}{proj_exp:,.2f}. "
                f"You will remain within your budget with {cur}{rem:,.2f} remaining."
            )
            self.forecast_box.configure(border_color="#10B981")
            self.forecast_text_lbl.configure(text=forecast_msg, text_color="#E2E8F0")
        else:
            over = abs(rem)
            forecast_msg = (
                f"⚠️ Spending Forecast: At your current pace of ~{cur}{daily_avg:.2f} per day, "
                f"your projected spend this month will reach {cur}{proj_exp:,.2f}, "
                f"which is {cur}{over:,.2f} over your monthly budget of {cur}{mb:,.2f}."
            )
            self.forecast_box.configure(border_color="#EF4444")
            self.forecast_text_lbl.configure(text=forecast_msg, text_color="#FCA5A5")

        # Update Meal Pills
        meals = daily["meals"]
        targets = daily["targets"]
        self.pill_breakfast.amt_lbl.configure(text=self.analytics.format_currency(meals["Breakfast"]))
        self.pill_breakfast.tgt_lbl.configure(text=f"Target: {cur}{targets['Breakfast']:.2f}")

        self.pill_lunch.amt_lbl.configure(text=self.analytics.format_currency(meals["Lunch"]))
        self.pill_lunch.tgt_lbl.configure(text=f"Target: {cur}{targets['Lunch']:.2f}")

        self.pill_dinner.amt_lbl.configure(text=self.analytics.format_currency(meals["Dinner"]))
        self.pill_dinner.tgt_lbl.configure(text=f"Target: {cur}{targets['Dinner']:.2f}")

        self.pill_other.amt_lbl.configure(text=self.analytics.format_currency(meals["Other"]))
        self.pill_other.tgt_lbl.configure(text=f"Target: {cur}{targets['Other']:.2f}")

        # Update Recent Activity Items
        for widget in self.recent_list_frame.winfo_children():
            widget.destroy()

        recent_expenses = self.db.get_expenses(limit=5)
        if not recent_expenses:
            ctk.CTkLabel(
                self.recent_list_frame, 
                text="No expenses recorded yet. Use the '+ Add Expense' button to get started!", 
                text_color=THEME["text_sub"], 
                font=("Segoe UI", 11)
            ).pack(pady=10)
        else:
            for exp in recent_expenses:
                row = ctk.CTkFrame(
                    self.recent_list_frame, 
                    fg_color="#0B0F19", 
                    corner_radius=6,
                    border_width=1,
                    border_color=THEME["border_dark"]
                )
                row.pack(fill="x", pady=2)

                m_color = get_meal_color(exp["meal_type"])
                
                badge = ctk.CTkLabel(
                    row, 
                    text=exp["meal_type"], 
                    font=("Segoe UI", 10),
                    text_color=m_color, 
                    fg_color=THEME["card_dark"], 
                    corner_radius=4, 
                    padx=6, 
                    pady=2
                )
                badge.pack(side="left", padx=8, pady=6)

                title = ctk.CTkLabel(
                    row, 
                    text=exp["title"], 
                    font=("Segoe UI", 11), 
                    text_color=THEME["text_main"]
                )
                title.pack(side="left", padx=6)

                cat = ctk.CTkLabel(
                    row, 
                    text=f"• {exp['category']} • {exp['date']}", 
                    font=("Segoe UI", 10), 
                    text_color=THEME["text_sub"]
                )
                cat.pack(side="left", padx=4)

                amt = ctk.CTkLabel(
                    row, 
                    text=f"-{self.analytics.format_currency(exp['amount'])}", 
                    font=("Segoe UI", 11), 
                    text_color="#F87171"
                )
                amt.pack(side="right", padx=10)

    # ==========================================
    # 2. EXPENSES & MEAL MANAGEMENT VIEW
    # ==========================================
    def _create_expenses_page(self) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self.content_container, fg_color=THEME["bg_dark"])
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        
        ctk.CTkLabel(
            header, 
            text="Expense Records & Management", 
            font=("Segoe UI", 20), 
            text_color=THEME["text_main"]
        ).pack(side="left")
        
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        add_btn = ctk.CTkButton(
            btn_box, 
            text="➕ Add Entry", 
            font=("Segoe UI", 12),
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            corner_radius=6, 
            height=32, 
            cursor="hand2",
            command=lambda: self.open_quick_meal_modal()
        )
        add_btn.pack(side="left")

        # Filters Bar
        filter_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=8, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        filter_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))

        f_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=14, pady=8)

        # Search box
        self.search_entry = ctk.CTkEntry(
            f_inner, 
            placeholder_text="🔍 Search title or notes...", 
            width=220, 
            font=("Segoe UI", 11)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_expenses_table())

        # Meal Filter
        ctk.CTkLabel(
            f_inner, 
            text="Meal:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=(4, 4))
        
        self.meal_filter_cb = ctk.CTkComboBox(
            f_inner, 
            values=["All", "Breakfast", "Lunch", "Dinner", "Other"], 
            width=110,
            command=lambda v: self.refresh_expenses_table()
        )
        self.meal_filter_cb.pack(side="left", padx=(0, 10))
        self.meal_filter_cb.set("All")

        # Category Filter
        ctk.CTkLabel(
            f_inner, 
            text="Category:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=(4, 4))
        
        self.cat_filter_cb = ctk.CTkComboBox(
            f_inner, 
            values=["All"] + CATEGORIES, 
            width=140,
            command=lambda v: self.refresh_expenses_table()
        )
        self.cat_filter_cb.pack(side="left", padx=(0, 10))
        self.cat_filter_cb.set("All")

        # Action Buttons
        refresh_btn = ctk.CTkButton(
            f_inner, 
            text="🔄 Refresh", 
            width=70, 
            height=28, 
            fg_color=THEME["card_hover"], 
            hover_color="#374151",
            font=("Segoe UI", 11),
            cursor="hand2",
            command=self.refresh_expenses_table
        )
        refresh_btn.pack(side="right")

        # Table Frame using Treeview
        table_container = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=8, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        table_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME["card_dark"],
            foreground=THEME["text_main"],
            fieldbackground=THEME["card_dark"],
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#070B12",
            foreground=THEME["text_muted"],
            font=("Segoe UI", 10),
            relief="flat",
            padding=6
        )
        style.map("Treeview", background=[('selected', THEME["accent_primary"])], foreground=[('selected', '#FFFFFF')])
        style.map("Treeview.Heading", background=[('active', '#111827')])

        columns = ("id", "date", "meal", "category", "title", "amount", "notes")
        self.exp_tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")
        
        self.exp_tree.heading("id", text="ID")
        self.exp_tree.heading("date", text="Date")
        self.exp_tree.heading("meal", text="Meal / Type")
        self.exp_tree.heading("category", text="Category")
        self.exp_tree.heading("title", text="Title / Description")
        self.exp_tree.heading("amount", text="Amount")
        self.exp_tree.heading("notes", text="Notes")

        self.exp_tree.column("id", width=50, anchor="center")
        self.exp_tree.column("date", width=95, anchor="center")
        self.exp_tree.column("meal", width=110, anchor="center")
        self.exp_tree.column("category", width=140, anchor="w")
        self.exp_tree.column("title", width=230, anchor="w")
        self.exp_tree.column("amount", width=100, anchor="e")
        self.exp_tree.column("notes", width=180, anchor="w")

        # Tags for alternating row striping
        self.exp_tree.tag_configure('odd', background='#111827')
        self.exp_tree.tag_configure('even', background='#162032')

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.exp_tree.yview)
        self.exp_tree.configure(yscrollcommand=scrollbar.set)

        self.exp_tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        # Table Action Bar
        action_bar = ctk.CTkFrame(table_container, fg_color="transparent")
        action_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))

        self.table_count_lbl = ctk.CTkLabel(
            action_bar, 
            text="Showing 0 expenses", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_sub"]
        )
        self.table_count_lbl.pack(side="left")

        del_btn = ctk.CTkButton(
            action_bar, 
            text="🗑️ Delete Selected", 
            fg_color="#EF4444", 
            hover_color="#DC2626",
            font=("Segoe UI", 11), 
            height=28, 
            corner_radius=6,
            cursor="hand2",
            command=self.delete_selected_expense
        )
        del_btn.pack(side="right", padx=4)

        edit_btn = ctk.CTkButton(
            action_bar, 
            text="✏️ Edit Selected", 
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            font=("Segoe UI", 11), 
            height=28, 
            corner_radius=6,
            cursor="hand2",
            command=self.edit_selected_expense
        )
        edit_btn.pack(side="right", padx=4)

        return page

    def refresh_expenses_table(self):
        """Re-populates the expenses Treeview based on current filters."""
        for item in self.exp_tree.get_children():
            self.exp_tree.delete(item)

        search_query = self.search_entry.get().strip()
        meal_filter = self.meal_filter_cb.get()
        cat_filter = self.cat_filter_cb.get()
        cur = self.analytics.get_currency()

        expenses = self.db.get_expenses(
            meal_type=meal_filter if meal_filter != "All" else None,
            category=cat_filter if cat_filter != "All" else None,
            search=search_query if search_query else None
        )

        for idx, exp in enumerate(expenses):
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.exp_tree.insert("", "end", values=(
                exp["id"],
                exp["date"],
                exp["meal_type"],
                exp["category"],
                exp["title"],
                f"{cur}{exp['amount']:.2f}",
                exp["notes"] or "-"
            ), tags=(tag,))

        self.table_count_lbl.configure(text=f"Total: {len(expenses)} transactions | Sum: {self.analytics.format_currency(sum(e['amount'] for e in expenses))}")

    def delete_selected_expense(self):
        selected = self.exp_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to delete.")
            return

        item = self.exp_tree.item(selected[0])
        exp_id = item["values"][0]
        title = item["values"][4]
        amt = item["values"][5]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}' ({amt})?"):
            self.db.delete_expense(int(exp_id))
            self.refresh_expenses_table()
            self.refresh_dashboard()

    def edit_selected_expense(self):
        selected = self.exp_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to edit.")
            return

        item = self.exp_tree.item(selected[0])
        exp_id = int(item["values"][0])
        exp_data = self.db.get_expense_by_id(exp_id)
        if exp_data:
            self.open_quick_meal_modal(initial_data=exp_data)

    # ==========================================
    # 3. MONTHLY REPORT VIEW
    # ==========================================
    def _create_monthly_page(self) -> ctk.CTkScrollableFrame:
        page = ctk.CTkScrollableFrame(self.content_container, fg_color=THEME["bg_dark"])

        # Header Row & Month Picker
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))

        ctk.CTkLabel(
            header, 
            text="Monthly Budget & Expense Report", 
            font=("Segoe UI", 20), 
            text_color=THEME["text_main"]
        ).pack(side="left")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")

        ctk.CTkLabel(
            controls, 
            text="Select Month:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=6)
        
        self.month_picker = ctk.CTkComboBox(
            controls, 
            values=[date.today().strftime("%Y-%m")], 
            width=120,
            command=lambda v: self.refresh_monthly_report()
        )
        self.month_picker.pack(side="left", padx=4)

        export_btn = ctk.CTkButton(
            controls, 
            text="📥 Export CSV", 
            font=("Segoe UI", 11),
            fg_color=THEME["card_dark"], 
            hover_color=THEME["card_hover"],
            border_width=1,
            border_color=THEME["border_dark"],
            corner_radius=6, 
            height=32, 
            cursor="hand2",
            command=self.export_monthly_csv
        )
        export_btn.pack(side="left", padx=8)

        # KPI Summary Cards for Selected Month
        month_kpi_frame = ctk.CTkFrame(page, fg_color="transparent")
        month_kpi_frame.pack(fill="x", padx=24, pady=(0, 16))
        month_kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.m_kpi_total = StatCard(month_kpi_frame, title="Total Spent", value="$0.00", subtext="This month", icon_text="💳", accent_color="#38BDF8")
        self.m_kpi_total.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.m_kpi_daily_avg = StatCard(month_kpi_frame, title="Daily Average", value="$0.00", subtext="Per active day", icon_text="📅", accent_color="#F59E0B")
        self.m_kpi_daily_avg.grid(row=0, column=1, sticky="nsew", padx=4)

        self.m_kpi_count = StatCard(month_kpi_frame, title="Transactions", value="0", subtext="Recorded entries", icon_text="📝", accent_color="#A78BFA")
        self.m_kpi_count.grid(row=0, column=2, sticky="nsew", padx=4)

        self.m_kpi_peak = StatCard(month_kpi_frame, title="Peak Spend Day", value="$0.00", subtext="Highest day", icon_text="🚀", accent_color="#EF4444")
        self.m_kpi_peak.grid(row=0, column=3, sticky="nsew", padx=(6, 0))

        # Visual Charts Grid (Donut Meal Chart & Daily Bar Chart)
        charts_row = ctk.CTkFrame(page, fg_color="transparent")
        charts_row.pack(fill="x", padx=24, pady=(0, 16))
        charts_row.grid_columnconfigure(0, weight=4)
        charts_row.grid_columnconfigure(1, weight=6)

        self.month_meal_chart = ChartContainer(charts_row, title="🥧 Meal & Expense Distribution")
        self.month_meal_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.month_daily_chart = ChartContainer(charts_row, title="📊 Daily Spending Flow")
        self.month_daily_chart.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Category Breakdown Table / Cards
        cat_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        cat_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(
            cat_card, 
            text="🏷️ Spending by Category", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.month_cat_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
        self.month_cat_frame.pack(fill="x", padx=16, pady=(0, 12))

        return page

    def refresh_monthly_report(self):
        """Loads and visualizes monthly data for the selected month."""
        months, _ = self.db.get_available_months_and_years()
        self.month_picker.configure(values=months)
        
        ym_selected = self.month_picker.get()
        if not ym_selected or ym_selected not in months:
            ym_selected = months[0] if months else date.today().strftime("%Y-%m")
            self.month_picker.set(ym_selected)

        cur = self.analytics.get_currency()
        report = self.analytics.get_monthly_report_data(ym_selected)

        # Update KPIs
        self.m_kpi_total.update_values(self.analytics.format_currency(report["total_spent"]))
        self.m_kpi_daily_avg.update_values(self.analytics.format_currency(report["daily_avg"]))
        self.m_kpi_count.update_values(str(report["transaction_count"]))
        
        peak_date, peak_amt = report["highest_day"]
        self.m_kpi_peak.update_values(self.analytics.format_currency(peak_amt), subtext=f"Date: {peak_date}")

        # Render Matplotlib Charts
        self.month_meal_chart.plot_meal_donut(report["meal_totals"], cur)
        self.month_daily_chart.plot_daily_bars(report["daily_totals"], cur)

        # Render Category Breakdown
        for w in self.month_cat_frame.winfo_children():
            w.destroy()

        if not report["category_totals"]:
            ctk.CTkLabel(
                self.month_cat_frame, 
                text="No expenses recorded for this month.", 
                text_color=THEME["text_sub"],
                font=("Segoe UI", 11)
            ).pack(pady=10)
        else:
            for cat, amt in report["category_totals"]:
                pct = (amt / report["total_spent"] * 100) if report["total_spent"] > 0 else 0
                row = ctk.CTkFrame(
                    self.month_cat_frame, 
                    fg_color="#0B0F19", 
                    corner_radius=6,
                    border_width=1,
                    border_color=THEME["border_dark"]
                )
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row, 
                    text=cat, 
                    font=("Segoe UI", 11), 
                    text_color=THEME["text_main"]
                ).pack(side="left", padx=12, pady=5)
                
                ctk.CTkLabel(
                    row, 
                    text=f"{pct:.1f}%", 
                    font=("Segoe UI", 10), 
                    text_color=THEME["text_sub"]
                ).pack(side="left", padx=6)
                
                ctk.CTkLabel(
                    row, 
                    text=self.analytics.format_currency(amt), 
                    font=("Segoe UI", 11), 
                    text_color="#818CF8"
                ).pack(side="right", padx=12)

    def export_monthly_csv(self):
        ym = self.month_picker.get()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"budget_report_{ym}.csv"
        )
        if filepath:
            success = self.analytics.export_monthly_csv(ym, filepath)
            if success:
                messagebox.showinfo("Export Successful", f"Monthly report exported to:\n{filepath}")
            else:
                messagebox.showerror("Export Failed", "Could not export monthly CSV report.")

    # ==========================================
    # 4. YEARLY REPORT VIEW
    # ==========================================
    def _create_yearly_page(self) -> ctk.CTkScrollableFrame:
        page = ctk.CTkScrollableFrame(self.content_container, fg_color=THEME["bg_dark"])

        # Header & Year Picker
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))

        ctk.CTkLabel(
            header, 
            text="Annual Financial Overview", 
            font=("Segoe UI", 20), 
            text_color=THEME["text_main"]
        ).pack(side="left")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")

        ctk.CTkLabel(
            controls, 
            text="Select Year:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=6)
        
        self.year_picker = ctk.CTkComboBox(
            controls, 
            values=[date.today().strftime("%Y")], 
            width=100,
            command=lambda v: self.refresh_yearly_report()
        )
        self.year_picker.pack(side="left", padx=4)

        export_btn = ctk.CTkButton(
            controls, 
            text="📥 Export CSV", 
            font=("Segoe UI", 11),
            fg_color=THEME["card_dark"], 
            hover_color=THEME["card_hover"],
            border_width=1,
            border_color=THEME["border_dark"],
            corner_radius=6, 
            height=32, 
            cursor="hand2",
            command=self.export_yearly_csv
        )
        export_btn.pack(side="left", padx=8)

        # Yearly KPIs
        kpi_frame = ctk.CTkFrame(page, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=24, pady=(0, 16))
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.y_kpi_total = StatCard(kpi_frame, title="Total Annual Spend", value="$0.00", subtext="Full year total", icon_text="💰", accent_color="#38BDF8")
        self.y_kpi_total.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.y_kpi_avg = StatCard(kpi_frame, title="Monthly Average", value="$0.00", subtext="Across active months", icon_text="📊", accent_color="#10B981")
        self.y_kpi_avg.grid(row=0, column=1, sticky="nsew", padx=4)

        self.y_kpi_high = StatCard(kpi_frame, title="Highest Month", value="$0.00", subtext="Peak spend", icon_text="📈", accent_color="#F59E0B")
        self.y_kpi_high.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        # 12-Month Bar & Trend Curve Chart
        self.year_trend_chart = ChartContainer(page, title="📅 Month-over-Month Expense Curve")
        self.year_trend_chart.pack(fill="x", padx=24, pady=(0, 16))

        # Annual Meal vs Other Breakdown Grid
        meal_summary_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        meal_summary_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(
            meal_summary_card, 
            text="🍽️ Annual Meal & Expense Split", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.yearly_meals_grid = ctk.CTkFrame(meal_summary_card, fg_color="transparent")
        self.yearly_meals_grid.pack(fill="x", padx=16, pady=(0, 12))
        self.yearly_meals_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        return page

    def refresh_yearly_report(self):
        """Loads and visualizes annual trends."""
        _, years = self.db.get_available_months_and_years()
        self.year_picker.configure(values=years)

        year_selected = self.year_picker.get()
        if not year_selected or year_selected not in years:
            year_selected = years[0] if years else date.today().strftime("%Y")
            self.year_picker.set(year_selected)

        cur = self.analytics.get_currency()
        report = self.analytics.get_yearly_report_data(year_selected)

        # Update KPIs
        self.y_kpi_total.update_values(self.analytics.format_currency(report["total_spent"]))
        self.y_kpi_avg.update_values(self.analytics.format_currency(report["avg_monthly"]))
        
        h_month, h_amt = report["highest_month"]
        self.y_kpi_high.update_values(self.analytics.format_currency(h_amt), subtext=f"Month: {h_month}")

        # Render 12-Month Chart
        self.year_trend_chart.plot_yearly_trend(report["month_names"], report["month_values"], cur)

        # Update Annual Meals Cards
        for w in self.yearly_meals_grid.winfo_children():
            w.destroy()

        meal_items = [
            ("Breakfast", report["meal_totals"]["Breakfast"], THEME["meal_breakfast"], "🍳"),
            ("Lunch", report["meal_totals"]["Lunch"], THEME["meal_lunch"], "🥗"),
            ("Dinner", report["meal_totals"]["Dinner"], THEME["meal_dinner"], "🍲"),
            ("Other Exp", report["meal_totals"]["Other"], THEME["meal_other"], "🛍️"),
        ]

        for i, (m_name, amt, color, icon) in enumerate(meal_items):
            pct = (amt / report["total_spent"] * 100) if report["total_spent"] > 0 else 0
            c = StatCard(
                self.yearly_meals_grid, 
                title=f"{icon} {m_name}", 
                value=self.analytics.format_currency(amt), 
                subtext=f"{pct:.1f}% of annual total", 
                accent_color=color
            )
            c.grid(row=0, column=i, sticky="nsew", padx=4)

    def export_yearly_csv(self):
        y = self.year_picker.get()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"annual_budget_report_{y}.csv"
        )
        if filepath:
            success = self.analytics.export_yearly_csv(y, filepath)
            if success:
                messagebox.showinfo("Export Successful", f"Yearly report exported to:\n{filepath}")
            else:
                messagebox.showerror("Export Failed", "Could not export annual CSV report.")

    # ==========================================
    # 5. SETTINGS & BUDGET TARGETS VIEW
    # ==========================================
    def _create_settings_page(self) -> ctk.CTkScrollableFrame:
        page = ctk.CTkScrollableFrame(self.content_container, fg_color=THEME["bg_dark"])

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))
        ctk.CTkLabel(
            header, 
            text="Budget & Application Settings", 
            font=("Segoe UI", 20), 
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Monthly Budget Card
        b_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        b_card.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            b_card, 
            text="🎯 Monthly Budget Target & Currency", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 4))
        
        ctk.CTkLabel(
            b_card, 
            text="Set your expected monthly expenditure limit to enable forecasting alerts.", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=16, pady=(0, 10))

        b_grid = ctk.CTkFrame(b_card, fg_color="transparent")
        b_grid.pack(fill="x", padx=16, pady=(0, 14))
        b_grid.grid_columnconfigure((0, 1), weight=1)

        # Monthly Budget Entry
        ctk.CTkLabel(
            b_grid, 
            text="Monthly Budget Goal:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).grid(row=0, column=0, sticky="w", pady=3)
        
        self.set_monthly_budget = ctk.CTkEntry(b_grid, width=200, font=("Segoe UI", 11))
        self.set_monthly_budget.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Currency Entry
        ctk.CTkLabel(
            b_grid, 
            text="Currency Symbol:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).grid(row=0, column=1, sticky="w", pady=3)
        
        self.set_currency = ctk.CTkComboBox(
            b_grid, 
            values=["Rs", "$", "€", "£", "₹", "¥", "A$", "C$"], 
            width=140
        )
        self.set_currency.grid(row=1, column=1, sticky="w", pady=(0, 10))

        # Daily Meal Targets Card
        m_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        m_card.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            m_card, 
            text="🍽️ Daily Meal Target Allocations", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 4))
        
        ctk.CTkLabel(
            m_card, 
            text="Specify approximate baseline budgets per meal for accurate forecasting.", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=16, pady=(0, 10))

        m_grid = ctk.CTkFrame(m_card, fg_color="transparent")
        m_grid.pack(fill="x", padx=16, pady=(0, 14))
        m_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(m_grid, text="🍳 Breakfast Target:", font=("Segoe UI", 11), text_color=THEME["meal_breakfast"]).grid(row=0, column=0, sticky="w", padx=4)
        self.set_b_target = ctk.CTkEntry(m_grid, width=120)
        self.set_b_target.grid(row=1, column=0, sticky="w", padx=4, pady=(2, 6))

        ctk.CTkLabel(m_grid, text="🥗 Lunch Target:", font=("Segoe UI", 11), text_color=THEME["meal_lunch"]).grid(row=0, column=1, sticky="w", padx=4)
        self.set_l_target = ctk.CTkEntry(m_grid, width=120)
        self.set_l_target.grid(row=1, column=1, sticky="w", padx=4, pady=(2, 6))

        ctk.CTkLabel(m_grid, text="🍲 Dinner Target:", font=("Segoe UI", 11), text_color=THEME["meal_dinner"]).grid(row=0, column=2, sticky="w", padx=4)
        self.set_d_target = ctk.CTkEntry(m_grid, width=120)
        self.set_d_target.grid(row=1, column=2, sticky="w", padx=4, pady=(2, 6))

        ctk.CTkLabel(m_grid, text="🛍️ Other Target:", font=("Segoe UI", 11), text_color=THEME["meal_other"]).grid(row=0, column=3, sticky="w", padx=4)
        self.set_o_target = ctk.CTkEntry(m_grid, width=120)
        self.set_o_target.grid(row=1, column=3, sticky="w", padx=4, pady=(2, 6))

        # Appearance & Theme Card
        app_card = ctk.CTkFrame(
            page, 
            fg_color=THEME["card_dark"], 
            corner_radius=10, 
            border_width=1, 
            border_color=THEME["border_dark"]
        )
        app_card.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            app_card, 
            text="🎨 Appearance & UI Theme", 
            font=("Segoe UI", 13), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(12, 6))

        app_grid = ctk.CTkFrame(app_card, fg_color="transparent")
        app_grid.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            app_grid, 
            text="Theme Mode:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=(0, 10))
        
        self.set_theme_mode = ctk.CTkSegmentedButton(
            app_grid, 
            values=["Dark", "Light", "System"], 
            command=self.on_theme_change
        )
        self.set_theme_mode.pack(side="left")

        # Action Buttons Row
        action_row = ctk.CTkFrame(page, fg_color="transparent")
        action_row.pack(anchor="w", padx=24, pady=(8, 30))

        save_btn = ctk.CTkButton(
            action_row, 
            text="💾 Save Settings", 
            font=("Segoe UI", 12),
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            corner_radius=8, 
            height=38, 
            cursor="hand2",
            command=self.save_settings
        )
        save_btn.pack(side="left", padx=(0, 12))

        reset_btn = ctk.CTkButton(
            action_row, 
            text="🗑️ Clear All Expense Data", 
            font=("Segoe UI", 11),
            fg_color="#7F1D1D", 
            hover_color="#991B1B",
            corner_radius=8, 
            height=38, 
            cursor="hand2",
            command=self.reset_all_data
        )
        reset_btn.pack(side="left")

        return page

    def reset_all_data(self):
        """Clears all expenses from DB."""
        if messagebox.askyesno("Confirm Clear All Data", "Are you sure you want to clear all logged expenses? This cannot be undone."):
            self.db.clear_all_expenses()
            self.refresh_dashboard()
            self.refresh_expenses_table()
            messagebox.showinfo("Cleared", "All expenses have been cleared.")

    def load_settings_values(self):
        """Populate settings input fields with current database values."""
        self.set_monthly_budget.delete(0, "end")
        self.set_monthly_budget.insert(0, self.db.get_setting("monthly_budget", "1500.0"))

        self.set_currency.set(self.db.get_setting("currency", "Rs"))

        self.set_b_target.delete(0, "end")
        self.set_b_target.insert(0, self.db.get_setting("breakfast_target", "5.0"))

        self.set_l_target.delete(0, "end")
        self.set_l_target.insert(0, self.db.get_setting("lunch_target", "10.0"))

        self.set_d_target.delete(0, "end")
        self.set_d_target.insert(0, self.db.get_setting("dinner_target", "12.0"))

        self.set_o_target.delete(0, "end")
        self.set_o_target.insert(0, self.db.get_setting("other_target", "10.0"))

        self.set_theme_mode.set(self.db.get_setting("app_theme", "Dark"))

    def on_theme_change(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        self.db.set_setting("app_theme", new_mode)

    def save_settings(self):
        """Save settings entries to DB."""
        try:
            mb = float(self.set_monthly_budget.get().strip())
            bt = float(self.set_b_target.get().strip())
            lt = float(self.set_l_target.get().strip())
            dt = float(self.set_d_target.get().strip())
            ot = float(self.set_o_target.get().strip())
            curr = self.set_currency.get().strip()

            self.db.set_setting("monthly_budget", str(mb))
            self.db.set_setting("currency", curr)
            self.db.set_setting("breakfast_target", str(bt))
            self.db.set_setting("lunch_target", str(lt))
            self.db.set_setting("dinner_target", str(dt))
            self.db.set_setting("other_target", str(ot))

            messagebox.showinfo("Saved", "Settings and budget goals updated successfully!")
            self.refresh_dashboard()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please ensure budget and target values are valid numbers.")

    # ==========================================
    # MODAL: QUICK MEAL & EXPENSE ENTRY
    # ==========================================
    def open_quick_meal_modal(self, meal_preset: Optional[str] = None, initial_data: Optional[dict] = None):
        """Opens a modal popup to record or edit an expense."""
        modal = ctk.CTkToplevel(self)
        modal.title("Edit Expense" if initial_data else "Log Expense / Meal")
        modal.geometry("480x540")
        modal.minsize(450, 520)
        modal.configure(fg_color=THEME["bg_dark"])
        modal.transient(self)
        modal.grab_set()

        # Modal Container
        m_frame = ctk.CTkFrame(
            modal, 
            fg_color=THEME["card_dark"], 
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_dark"]
        )
        m_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        modal_title = "✏️ Edit Expense Record" if initial_data else "➕ Log Expense / Meal"
        ctk.CTkLabel(
            m_frame, 
            text=modal_title, 
            font=("Segoe UI", 15), 
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=20, pady=(16, 12))

        inner_box = ctk.CTkFrame(m_frame, fg_color="transparent")
        inner_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Meal Type Selection Segmented Button
        ctk.CTkLabel(
            inner_box, 
            text="Meal / Expense Category Type:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 4))
        
        meal_selector = ctk.CTkSegmentedButton(inner_box, values=MEAL_TYPES)
        meal_selector.pack(fill="x", pady=(0, 12))
        
        default_meal = "Lunch"
        if initial_data:
            default_meal = initial_data["meal_type"]
        elif meal_preset:
            default_meal = meal_preset
        meal_selector.set(default_meal)

        # Amount
        cur = self.analytics.get_currency()
        ctk.CTkLabel(
            inner_box, 
            text=f"Amount Spent ({cur}):", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 4))
        
        amount_entry = ctk.CTkEntry(inner_box, placeholder_text="0.00", font=("Segoe UI", 12))
        amount_entry.pack(fill="x", pady=(0, 12))
        if initial_data:
            amount_entry.insert(0, str(initial_data["amount"]))

        # Title / Description
        ctk.CTkLabel(
            inner_box, 
            text="Description / Meal Name:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 4))
        
        title_entry = ctk.CTkEntry(inner_box, placeholder_text="e.g. Chicken Rice / Coffee / Bus Pass", font=("Segoe UI", 12))
        title_entry.pack(fill="x", pady=(0, 12))
        if initial_data:
            title_entry.insert(0, initial_data["title"])

        # Date & Category Row
        dc_frame = ctk.CTkFrame(inner_box, fg_color="transparent")
        dc_frame.pack(fill="x", pady=(0, 12))
        dc_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            dc_frame, 
            text="Date (YYYY-MM-DD):", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).grid(row=0, column=0, sticky="w")
        
        date_entry = ctk.CTkEntry(dc_frame, font=("Segoe UI", 11))
        date_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(2, 0))
        date_entry.insert(0, initial_data["date"] if initial_data else date.today().strftime("%Y-%m-%d"))

        ctk.CTkLabel(
            dc_frame, 
            text="Category:", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).grid(row=0, column=1, sticky="w")
        
        cat_combo = ctk.CTkComboBox(dc_frame, values=CATEGORIES)
        cat_combo.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(2, 0))
        cat_combo.set(initial_data["category"] if initial_data else "Food & Dining")

        # Notes
        ctk.CTkLabel(
            inner_box, 
            text="Notes (Optional):", 
            font=("Segoe UI", 11), 
            text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 4))
        
        notes_entry = ctk.CTkEntry(inner_box, placeholder_text="Additional notes or receipt info...", font=("Segoe UI", 11))
        notes_entry.pack(fill="x", pady=(0, 16))
        if initial_data and initial_data["notes"]:
            notes_entry.insert(0, initial_data["notes"])

        # Save Button Action
        def save_action():
            amt_str = amount_entry.get().strip()
            title_str = title_entry.get().strip()
            date_str = date_entry.get().strip()
            meal_val = meal_selector.get()
            cat_val = cat_combo.get()
            notes_val = notes_entry.get().strip()

            if not amt_str:
                messagebox.showerror("Error", "Amount cannot be empty.")
                return

            try:
                amt_val = float(amt_str)
                if amt_val <= 0:
                    messagebox.showerror("Error", "Amount must be greater than zero.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numeric amount.")
                return

            if not title_str:
                title_str = f"{meal_val} expense"

            # Validate date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
                return

            if initial_data:
                self.db.update_expense(
                    expense_id=initial_data["id"],
                    date_str=date_str,
                    meal_type=meal_val,
                    category=cat_val,
                    title=title_str,
                    amount=amt_val,
                    notes=notes_val
                )
            else:
                self.db.add_expense(
                    date_str=date_str,
                    meal_type=meal_val,
                    category=cat_val,
                    title=title_str,
                    amount=amt_val,
                    notes=notes_val
                )

            modal.destroy()
            self.refresh_dashboard()
            self.refresh_expenses_table()

        action_btn = ctk.CTkButton(
            inner_box, 
            text="✓ Save Expense", 
            font=("Segoe UI", 12),
            fg_color=THEME["accent_primary"], 
            hover_color=THEME["accent_hover"],
            height=36, 
            corner_radius=8, 
            cursor="hand2",
            command=save_action
        )
        action_btn.pack(fill="x", pady=(4, 0))


if __name__ == "__main__":
    app = BudgetTrackerApp()
    app.mainloop()
