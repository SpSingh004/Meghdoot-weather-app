# ✨ Meghdoot (मेघदूत) - The Cloud Messenger

Meghdoot is a highly polished, feature-rich Graphical Weather Application built in Python using **CustomTkinter** for modern, premium aesthetics and the keyless **Open-Meteo API** for lightning-fast forecast retrieval. 

*The name is inspired by Kalidasa's classical Sanskrit masterpiece, **Meghadūta**, where a cloud acts as a messenger delivering messages across lands. Similarly, this application acts as your digital messenger, fetching weather packets from "the cloud" and displaying them in a stunning, modern desktop dashboard.*

---

## 🚀 Key Features

*   **Premium Visual Aesthetics:** Designed with deep slate/indigo gradients, clean card-based grids, high-DPI modern typography, and responsive layouts mimicking state-of-the-art native weather widgets.
*   **Zero-Key Out-Of-The-Box Execution:** No signups, API keys, or configurations required! It utilizes Open-Meteo's non-commercial open endpoints and `ipapi.co` geolocator to run instantly.
*   **Automatic IP Geolocation:** Automatically detects your location on startup using your external IP address, presenting a custom local forecast instantly.
*   **Asynchronous Background Threading:** Network requests run completely asynchronously on background worker threads, keeping the desktop interface fully fluid and interactive with zero freezing.
*   **Instant Temperature Unit Swapping (C° ⇄ F°):** Swapping between Metric and Imperial coordinates instantly translates all temperatures, feels-like readings, and wind speeds on-the-fly without making new network requests.
*   **Dynamic Theme Colors:** The weather cards dynamically alter their background theme colors based on the fetched weather conditions (e.g. sunny sky yields deep blue, rain turns it to dark slate, and thunderstorms shift it to violet).
*   **Detailed Metrics Grid:** Highlights critical conditions: RealFeel (Apparent Temperature), Wind Speed, Relative Humidity, and Maximum Rain/Precipitation probability.
*   **Hourly Strip & 7-Day Outlook:** Renders horizontal segments for the next 24 hours of hourly temperature developments and a clean vertical listing for the 7-day outlook.
*   **Robust Network & Input Fail-Safes:** Includes full-screen offline overlay screens with instant retry checks, as well as descriptive search-error badges when entering invalid inputs.

---

## 🛠️ Technology Stack & Dependencies

*   **Python 3.10+**
*   **GUI Framework:** `customtkinter` (modern tk-based widget library)
*   **Networking:** `requests` (for REST API communication)

---

## 📥 Installation

1.  **Clone or Download** this directory to your desktop.
2.  Open your terminal inside the project directory (`c:\Users\samee\OneDrive\Desktop\Weather App`).
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🏃 Running the Application

Launch the weather app by running:
```bash
python main.py
```

---

## 📂 Project Architecture

```
Weather App/
│
├── main.py             # Main GUI application logic, layouts, thread workers, and unit togglers
├── weather_api.py      # Backend API connectors (Geocoding, Geolocation, Forecast parser)
├── requirements.txt    # Declared python dependencies
└── README.md           # Documentation guide
```

*   **`main.py`:** Contains the main CustomTkinter graphical loop. Coordinates the application frames: `loading_frame` (initial status), `error_frame` (offline/spelling retry interface), and `main_container` (active weather display).
*   **`weather_api.py`:** Contains direct requests queries to Open-Meteo and coordinates fallback configurations. Maps WMO condition codes (0-99) into human-readable descriptions and colorful, crisp emojis.
