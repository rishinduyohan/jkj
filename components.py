"""
UI Components and Visual Helpers for Modern Budget Tracker App
Includes customized cards, meal chips, range gauges, and embedded matplotlib charts.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, Dict, Any, List, Tuple
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Color Theme Palette - Modern Obsidian & Indigo Palette
THEME = {
    "bg_dark": "#0B0F19",          # Deep obsidian background
    "card_dark": "#111827",        # Sleek dark card
    "card_hover": "#1F2937",       # Elevated card hover
    "sidebar_dark": "#070B12",     # Darkest sidebar background
    "border_dark": "#1F2937",      # Subtle border
    "accent_primary": "#4F46E5",    # Modern Indigo 600
    "accent_hover": "#4338CA",      # Indigo 700
    "accent_light": "#818CF8",      # Indigo 400
    
    # Meal specific accent colors
    "meal_breakfast": "#F59E0B",   # Amber / Gold
    "meal_lunch": "#10B981",       # Emerald Green
    "meal_dinner": "#8B5CF6",      # Violet / Purple
    "meal_other": "#EC4899",       # Rose / Pink
    
    # Text colors
    "text_main": "#F8FAFC",        # Crisp Slate 50
    "text_muted": "#94A3B8",       # Slate 400
    "text_sub": "#64748B",         # Slate 500
    
    # Status colors
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#38BDF8"
}

def get_meal_color(meal_type: str) -> str:
    mapping = {
        "Breakfast": THEME["meal_breakfast"],
        "Lunch": THEME["meal_lunch"],
        "Dinner": THEME["meal_dinner"],
        "Other": THEME["meal_other"]
    }
    return mapping.get(meal_type, THEME["accent_primary"])


class StatCard(ctk.CTkFrame):
    """Modern KPI / Summary Stat Card with title, value, subtext, and color indicator."""
    def __init__(self, master, title: str, value: str, subtext: str = "", 
                 accent_color: str = THEME["accent_primary"], icon_text: str = "💳", **kwargs):
        super().__init__(master, fg_color=THEME["card_dark"], corner_radius=12, 
                         border_width=1, border_color=THEME["border_dark"], **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Header Row (Icon + Title)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 4))
        
        icon_lbl = ctk.CTkLabel(header_frame, text=icon_text, font=("Segoe UI Emoji", 16))
        icon_lbl.pack(side="left", padx=(0, 6))
        
        self.title_lbl = ctk.CTkLabel(header_frame, text=title.upper(), 
                                      font=("Segoe UI", 10, "bold"), 
                                      text_color=THEME["text_muted"])
        self.title_lbl.pack(side="left")
        
        # Main Value
        self.value_lbl = ctk.CTkLabel(self, text=value, 
                                      font=("Segoe UI", 22, "bold"), 
                                      text_color=accent_color)
        self.value_lbl.pack(anchor="w", padx=16, pady=(2, 2))
        
        # Subtext
        self.sub_lbl = ctk.CTkLabel(self, text=subtext, 
                                    font=("Segoe UI", 11), 
                                    text_color=THEME["text_sub"])
        self.sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

    def update_values(self, value: str, subtext: Optional[str] = None):
        self.value_lbl.configure(text=value)
        if subtext is not None:
            self.sub_lbl.configure(text=subtext)


class MealPill(ctk.CTkFrame):
    """Interactive / Display chip for Breakfast, Lunch, Dinner, Other with spend amount."""
    def __init__(self, master, meal_name: str, amount_str: str, target_str: str = "", 
                 command: Optional[Callable] = None, **kwargs):
        color = get_meal_color(meal_name)
        super().__init__(master, fg_color=THEME["card_dark"], corner_radius=10, 
                         border_width=1, border_color=THEME["border_dark"], **kwargs)
        
        self.grid_columnconfigure(1, weight=1)
        
        # Color Stripe / Indicator Dot
        dot = ctk.CTkLabel(self, text="●", text_color=color, font=("Segoe UI", 16))
        dot.grid(row=0, column=0, rowspan=2, padx=(12, 6), pady=8)
        
        # Meal Name
        self.name_lbl = ctk.CTkLabel(self, text=meal_name, font=("Segoe UI", 13, "bold"), text_color=THEME["text_main"])
        self.name_lbl.grid(row=0, column=1, sticky="w", padx=2, pady=(8, 0))
        
        # Target info
        self.tgt_lbl = ctk.CTkLabel(self, text=f"Target: {target_str}", font=("Segoe UI", 10), text_color=THEME["text_sub"])
        self.tgt_lbl.grid(row=1, column=1, sticky="w", padx=2, pady=(0, 8))
        
        # Amount Spent
        self.amt_lbl = ctk.CTkLabel(self, text=amount_str, font=("Segoe UI", 14, "bold"), text_color=color)
        self.amt_lbl.grid(row=0, column=2, rowspan=2, sticky="e", padx=(8, 14), pady=8)


class BudgetRangeGauge(ctk.CTkFrame):
    """
    Shows the estimated monthly budget range visually:
    [ Min Projection ] -------- [ Expected Pace ] -------- [ Upper Range ]
    With comparison to User Budget.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=THEME["card_dark"], corner_radius=14, 
                         border_width=1, border_color=THEME["border_dark"], **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        
        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(14, 8))
        
        title_lbl = ctk.CTkLabel(top_frame, text="📊 Approximate Monthly Budget Forecast", 
                                 font=("Segoe UI", 14, "bold"), text_color=THEME["text_main"])
        title_lbl.pack(side="left")
        
        self.health_badge = ctk.CTkLabel(top_frame, text="On Track", 
                                         font=("Segoe UI", 11, "bold"), 
                                         text_color="#10B981", 
                                         fg_color="#064E3B", 
                                         corner_radius=6, 
                                         padx=10, pady=3)
        self.health_badge.pack(side="right")
        
        # Range Bar
        self.progress = ctk.CTkProgressBar(self, height=12, corner_radius=6, 
                                           progress_color=THEME["accent_primary"], fg_color="#1E293B")
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(4, 12))
        self.progress.set(0.0)
        
        # Range columns
        self.min_card = ctk.CTkFrame(self, fg_color="#0B0F19", corner_radius=8, border_width=1, border_color=THEME["border_dark"])
        self.min_card.grid(row=2, column=0, sticky="ew", padx=(16, 6), pady=(0, 14))
        ctk.CTkLabel(self.min_card, text="MIN ESTIMATE", font=("Segoe UI", 10, "bold"), text_color=THEME["text_muted"]).pack(pady=(6, 0))
        self.min_val = ctk.CTkLabel(self.min_card, text="$0.00", font=("Segoe UI", 13, "bold"), text_color="#10B981")
        self.min_val.pack(pady=(0, 6))
        
        self.exp_card = ctk.CTkFrame(self, fg_color="#0B0F19", corner_radius=8, border_width=1, border_color=THEME["border_dark"])
        self.exp_card.grid(row=2, column=1, sticky="ew", padx=6, pady=(0, 14))
        ctk.CTkLabel(self.exp_card, text="EXPECTED BURN", font=("Segoe UI", 10, "bold"), text_color=THEME["text_muted"]).pack(pady=(6, 0))
        self.exp_val = ctk.CTkLabel(self.exp_card, text="$0.00", font=("Segoe UI", 13, "bold"), text_color="#818CF8")
        self.exp_val.pack(pady=(0, 6))
        
        self.max_card = ctk.CTkFrame(self, fg_color="#0B0F19", corner_radius=8, border_width=1, border_color=THEME["border_dark"])
        self.max_card.grid(row=2, column=2, sticky="ew", padx=(6, 16), pady=(0, 14))
        ctk.CTkLabel(self.max_card, text="UPPER RANGE", font=("Segoe UI", 10, "bold"), text_color=THEME["text_muted"]).pack(pady=(6, 0))
        self.max_val = ctk.CTkLabel(self.max_card, text="$0.00", font=("Segoe UI", 13, "bold"), text_color="#F59E0B")
        self.max_val.pack(pady=(0, 6))

    def update_projection(self, proj_min_str: str, proj_exp_str: str, proj_max_str: str, 
                          health_text: str, health_color: str, budget_used_pct: float):
        self.min_val.configure(text=proj_min_str)
        self.exp_val.configure(text=proj_exp_str)
        self.max_val.configure(text=proj_max_str)
        
        self.health_badge.configure(text=health_text, text_color=health_color)
        if "High" in health_text or "Exceed" in health_text:
            self.health_badge.configure(fg_color="#7F1D1D")
        elif "Moderate" in health_text:
            self.health_badge.configure(fg_color="#78350F")
        else:
            self.health_badge.configure(fg_color="#064E3B")
            
        progress_val = min(1.0, max(0.0, budget_used_pct / 100.0))
        self.progress.set(progress_val)
        if budget_used_pct > 100:
            self.progress.configure(progress_color="#EF4444")
        elif budget_used_pct > 80:
            self.progress.configure(progress_color="#F59E0B")
        else:
            self.progress.configure(progress_color="#10B981")


class ChartContainer(ctk.CTkFrame):
    """Container for Matplotlib charts with modern aesthetic dark theme styling."""
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(master, fg_color=THEME["card_dark"], corner_radius=12, 
                         border_width=1, border_color=THEME["border_dark"], **kwargs)
        
        self.title_lbl = ctk.CTkLabel(self, text=title, font=("Segoe UI", 13, "bold"), text_color=THEME["text_main"])
        self.title_lbl.pack(anchor="w", padx=16, pady=(12, 6))
        
        self.canvas_widget = None
        self.fig = None

    def plot_meal_donut(self, meal_totals: Dict[str, float], currency: str):
        """Render a modern donut chart for Breakfast, Lunch, Dinner, Other."""
        self._clear_canvas()
        
        labels = []
        sizes = []
        colors = []
        color_map = {
            "Breakfast": THEME["meal_breakfast"],
            "Lunch": THEME["meal_lunch"],
            "Dinner": THEME["meal_dinner"],
            "Other": THEME["meal_other"]
        }
        
        total = sum(meal_totals.values())
        for meal, amt in meal_totals.items():
            if amt > 0:
                labels.append(f"{meal}\n({currency}{amt:,.0f})")
                sizes.append(amt)
                colors.append(color_map.get(meal, "#94A3B8"))

        self.fig = Figure(figsize=(4.2, 3.2), dpi=100, facecolor=THEME["card_dark"])
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["card_dark"])

        if total > 0:
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=140, pctdistance=0.75,
                textprops={'color': THEME["text_main"], 'fontsize': 8.5},
                wedgeprops={'width': 0.45, 'edgecolor': THEME["card_dark"], 'linewidth': 2.5}
            )
            for autotext in autotexts:
                autotext.set_color('#FFFFFF')
                autotext.set_fontsize(8.5)
                autotext.set_weight('bold')
        else:
            ax.text(0.5, 0.5, "No Expenses Recorded", horizontalalignment='center',
                    verticalalignment='center', transform=ax.transAxes,
                    color=THEME["text_muted"], fontsize=11)
            ax.axis('off')

        self.fig.tight_layout()
        self._embed_figure()

    def plot_daily_bars(self, daily_totals: List[Tuple[str, float]], currency: str):
        """Render bar chart of daily expenses."""
        self._clear_canvas()
        
        self.fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=THEME["card_dark"])
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["card_dark"])

        if daily_totals:
            days = [d.split("-")[-1] for d, _ in daily_totals]
            amounts = [amt for _, amt in daily_totals]
            
            bars = ax.bar(days, amounts, color=THEME["accent_primary"], width=0.6, edgecolor=THEME["accent_hover"], linewidth=1)
            
            ax.tick_params(colors=THEME["text_muted"], labelsize=8)
            ax.set_xlabel("Day of Month", color=THEME["text_muted"], fontsize=9, labelpad=4)
            ax.set_ylabel(f"Spent ({currency})", color=THEME["text_muted"], fontsize=9, labelpad=4)
            ax.grid(axis='y', linestyle='--', alpha=0.15, color='#94A3B8')
            
            for spine in ax.spines.values():
                spine.set_visible(False)
        else:
            ax.text(0.5, 0.5, "No Daily Data Available", horizontalalignment='center',
                    verticalalignment='center', transform=ax.transAxes,
                    color=THEME["text_muted"], fontsize=11)
            ax.axis('off')

        self.fig.tight_layout()
        self._embed_figure()

    def plot_yearly_trend(self, month_names: List[str], month_values: List[float], currency: str):
        """Render annual 12-month trend bar and line combo chart."""
        self._clear_canvas()
        
        self.fig = Figure(figsize=(7.5, 3.4), dpi=100, facecolor=THEME["card_dark"])
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["card_dark"])

        bars = ax.bar(month_names, month_values, color="#6366F1", width=0.55, alpha=0.85, label="Monthly Spend")
        
        # Smooth trendline overlay
        ax.plot(month_names, month_values, color="#38BDF8", marker='o', linewidth=2, markersize=5, label="Trend")

        ax.tick_params(colors=THEME["text_muted"], labelsize=8.5)
        ax.set_ylabel(f"Total Spent ({currency})", color=THEME["text_muted"], fontsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.15, color='#94A3B8')
        
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Highlight highest bar if any
        if any(month_values):
            max_val = max(month_values)
            max_idx = month_values.index(max_val)
            bars[max_idx].set_color("#F59E0B")
            
        ax.legend(facecolor=THEME["card_dark"], edgecolor=THEME["border_dark"], labelcolor=THEME["text_main"], fontsize=8)
        self.fig.tight_layout()
        self._embed_figure()

    def _clear_canvas(self):
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None

    def _embed_figure(self):
        canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.configure(bg=THEME["card_dark"], highlightthickness=0)
        self.canvas_widget.pack(fill="both", expand=True, padx=12, pady=(0, 12))
