# 💎 AuraBudget - Desktop Budget & Meal Tracker

A smooth, modern Python desktop application to track daily meal expenses (**Breakfast**, **Lunch**, **Dinner**, and **Other**), calculate approximate monthly budget projections, and generate visual monthly and yearly reports.

---

## ✨ Features

- 🍳 **Daily Meal Logging**: Fast separate recording for **Breakfast**, **Lunch**, **Dinner**, and **Other Expenses** with custom titles, amounts, and notes.
- 🔮 **Approximate Monthly Budget Forecasting**:
  - Automatically calculates current daily burn rate and active spend pace.
  - Dynamically calculates **Min Estimate**, **Expected Burn**, and **Upper Range** monthly totals.
  - Visual color-coded health gauge comparing projection with your target budget (Healthy, On Track, Moderate Risk, High Alert).
- 📊 **Interactive Monthly Reports**:
  - Visual donut chart showing Meal vs Other expense split.
  - Daily spending flow bar chart.
  - Category-by-category breakdown and peak spending day insights.
  - One-click CSV export.
- 📈 **Yearly Reports & Annual Trends**:
  - 12-month month-over-month trend line and bar chart.
  - Annual meal distribution breakdown.
  - Annual KPI metrics (Total Spend, Monthly Average, Peak Month).
  - One-click Annual CSV export.
- ⚙️ **Customizable Settings**:
  - Monthly budget limit.
  - Individual baseline targets for Breakfast, Lunch, Dinner, and Other.
  - Currency symbol customization ($, €, £, ₹, ¥, Rs, etc.).
  - Dark / Light / System UI theme modes.
- 💾 **Local Data Persistence**: Fast, reliable SQLite storage requiring no internet connection.

---

## 🚀 How to Run

### Option 1: Double-Click Launcher (Windows)
Double-click [`run_app.bat`](file:///d:/Python%20workspace/Budget%20tracker/run_app.bat) to launch the app immediately.

### Option 2: Command Line
```powershell
# 1. Install dependencies (if not already installed)
py -3.13 -m pip install -r requirements.txt

# 2. Run the application
py -3.13 app.py
```

---

## 🧪 Testing

Run backend tests:
```powershell
py -3.13 test_backend.py
```

Run GUI automation tests:
```powershell
py -3.13 test_gui.py
```

---

## 📁 Project Structure

```
Budget tracker/
├── app.py              # Main desktop application & GUI view manager
├── components.py       # Custom styled cards, range meter, & embedded Matplotlib charts
├── database.py         # SQLite data access layer and connection management
├── analytics.py        # Forecasting engine, budget range calculations, and report generator
├── test_backend.py     # Backend unit & integration test suite
├── test_gui.py         # GUI automation and headless verification test suite
├── requirements.txt    # Python dependencies (customtkinter, matplotlib, pillow)
├── run_app.bat         # 1-click Windows launcher
└── README.md           # Documentation
```
