# 🏁 F1 MapFeed

Formula 1 Telemetry Analytics Dashboard built using FastF1, Flask, Pandas, NumPy, and Matplotlib.

F1 MapFeed enables users to analyze Formula 1 telemetry data, compare driver performance, visualize track layouts, and generate race insights through an interactive web dashboard.

---

## 📌 Project Overview

F1 MapFeed uses Formula 1 telemetry data provided by FastF1 and transforms it into meaningful analytics and visualizations.

The project focuses on:

* Driver performance analysis
* Telemetry visualization
* Race pace comparison
* Track mapping
* Data-driven motorsport insights

This project demonstrates skills in data analytics, data visualization, backend development, and dashboard design using real-world Formula 1 data.

---

## 🚀 Features

### Driver Analysis

Analyze a driver's fastest lap and view:

* Maximum Speed
* Average Speed
* Maximum RPM
* Throttle Analysis
* Sector Time Analysis
* Circuit Layout Visualization
* Speed Heatmap

### Driver Comparison

Compare multiple drivers and analyze:

* Speed Profiles
* Race Pace
* Fastest Laps
* Consistency Metrics

### Interactive Dashboard

* Session Selection
* Driver Selection
* Telemetry Visualizations
* Plot Generation
* Performance Analytics

---

## 🛠 Tech Stack

### Backend

* Python
* Flask
* FastF1

### Data Processing

* Pandas
* NumPy

### Visualization

* Matplotlib

### Frontend

* HTML
* CSS
* JavaScript
* Bootstrap

### Database

* SQLite
* SQLAlchemy

---

## 📂 Project Structure

```text
F1-MapFeed
│
├── src/
│   ├── dashboard.py
│   ├── analytics.py
│   ├── comparison.py
│   ├── telemetry.py
│   ├── trackmap.py
│   ├── plotter.py
│   ├── session_loader.py
│   ├── models.py
│   ├── auth.py
│   └── history.py
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│   └── index.html
│
├── plots/
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/Suchendra-018/F1-MapFeed.git

cd F1-MapFeed
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the dashboard:

```bash
python src/dashboard.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

---

## 📊 Workflow

1. Select a race session
2. Select a driver
3. Click Analyze Driver
4. View telemetry statistics and visualizations
5. Compare multiple drivers for performance analysis

---

## 📸 Screenshots

Add screenshots here after UI improvements.

```text
assets/dashboard.png
assets/analysis.png
assets/comparison.png
```

---

## 🔮 Future Enhancements

* Live Telemetry Support
* Interactive Circuit Maps
* Tire Strategy Analysis
* Driver Performance Trends
* Advanced Race Analytics
* Modern Telemetry Dashboard UI

---

## 👨‍💻 Author

**Suchendra A**

Information Science Engineering Student

Interested in Data Analytics, Software Development, and Formula 1 Technology.
# F1 MapFeed — Formula 1 Intelligence Platform

F1 MapFeed is a FastF1-powered analytics workspace for session-level Formula 1 performance intelligence. The active application is a responsive, sidebar-first command center with dark and light themes, designed around readable race analytics rather than a form workflow.

## Active experience

- Command Center with large KPI cards, driver rankings, team performance and sector leaders
- Driver Analytics with driver, team, pace, top-speed and consistency metrics
- Constructor and Race Analytics views driven by the selected FastF1 session
- Session Explorer controls for season, Grand Prix and session selection
- Dark/light theme preference saved in browser local storage
- Lightweight dashboard loading; detailed telemetry stays on-demand

## Run locally

```bash
venv\Scripts\activate
python src\dashboard.py
```

Open `http://127.0.0.1:5000`. When offline, start with a completed cached session such as 2025 Monaco Race.

## Active architecture

```text
src/
  dashboard.py          Flask application and API routes
  session_loader.py     FastF1 session and calendar cache
  session_analytics.py  Driver, team, sector and KPI calculations
  calendar_fallback.py  Offline calendar fallback
static/
  css/theme.css         Global dark/light tokens and responsive layout
  js/platform_client.js Active analytics workspace
templates/
  platform.html         Active analytics shell
```

---
