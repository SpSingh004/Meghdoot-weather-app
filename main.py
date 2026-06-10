import customtkinter as ctk
import weather_api
import threading
import datetime

# Initialize customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Main window configuration
        self.title("Meghdoot - Modern Forecast Dashboard")
        self.geometry("980x740")
        self.minsize(980, 740)
        
        # Matte Charcoal background for a modern, sleek native OS feel
        self.configure(fg_color="#121212")
        
        # State variables
        self.current_unit = "°C"  # Toggles between "°C" and "°F"
        self.weather_data = None
        self.current_city = "Detecting..."
        self.current_country = ""
        self.is_dashboard_visible = False  # Track visibility state to prevent redraw glitches
        self.search_in_progress = True  # Block interactions until initial load completes
        
        # Main structure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_header()
        self.setup_main_layout()
        self.setup_loading_screen()
        self.setup_error_screen()
        
        # Initial load: Detect location and fetch weather
        self.fetch_local_weather()

    # --- UI Reactivity Hover Bindings ---

    def make_reactive(self, widget, normal_color, hover_color):
        """Recursively binds hover animations to a widget and all of its nested children."""
        def on_enter(event):
            widget.configure(fg_color=hover_color)
        def on_leave(event):
            widget.configure(fg_color=normal_color)
            
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        # Bind events to all child labels and elements inside the card
        for child in widget.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            
            # Recurse down one more layer if sub-containers exist (e.g. details headers)
            for sub_child in child.winfo_children():
                sub_child.bind("<Enter>", on_enter)
                sub_child.bind("<Leave>", on_leave)

    # --- UI Setup Methods ---
    
    def setup_header(self):
        """Header row containing app name, search bar, GPS button, and unit toggle."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(15, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)  # Search input stretches

        # Brand Logo (Bold and premium matte silver-white)
        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="✨ MEGHDOOT", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        self.logo_label.grid(row=0, column=0, padx=(0, 20), sticky="w")

        # Search Box Container
        self.search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.search_container.grid(row=0, column=1, sticky="ew")
        self.search_container.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="Search city (e.g. Tokyo, London)...",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=40,
            corner_radius=20,
            border_color="#2C2C2E",
            fg_color="#1C1C1E",
            placeholder_text_color="#636366"
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.trigger_search())

        self.search_btn = ctk.CTkButton(
            self.search_container,
            text="Search",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            width=110,
            corner_radius=20,
            fg_color="#3A3A3C",
            hover_color="#48484A",
            text_color="#FFFFFF",
            command=self.trigger_search
        )
        self.search_btn.grid(row=0, column=1)

        # GPS Detection Button
        self.gps_btn = ctk.CTkButton(
            self.header_frame,
            text="📍 My Location",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            height=40,
            width=135,
            corner_radius=20,
            fg_color="#1C1C1E",
            hover_color="#2C2C2E",
            border_width=1,
            border_color="#2C2C2E",
            text_color="#FFFFFF",
            command=self.fetch_local_weather
        )
        self.gps_btn.grid(row=0, column=2, padx=(15, 10))

        # Unit Toggle Control (Celsius vs Fahrenheit)
        self.unit_control = ctk.CTkSegmentedButton(
            self.header_frame,
            values=["°C", "°F"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            width=90,
            corner_radius=20,
            command=self.toggle_units
        )
        self.unit_control.set(self.current_unit)
        self.unit_control.grid(row=0, column=3, padx=(5, 0))

        # Error notification banner (hidden by default)
        self.error_badge = ctk.CTkLabel(
            self.search_container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#FF453A",
            fg_color="transparent"
        )
        self.error_badge.place(in_=self.search_entry, relx=0.0, rely=1.0, y=4, anchor="nw")

    def setup_main_layout(self):
        """Dashboard layout split into Left Column (weather details) and Right Column (7-day)."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=25, pady=(5, 25))
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # UNIFORM LAYOUT LOCK: Locks column widths mathematically to 60% and 40% of the screen
        self.main_container.grid_columnconfigure(0, weight=6, uniform="main_cols") # Left Column
        self.main_container.grid_columnconfigure(1, weight=4, uniform="main_cols") # Right Column

        self.main_container.grid_remove() 

        # --- LEFT COLUMN ---
        self.left_col = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Grid partitions: Headers and sections
        self.left_col.grid_rowconfigure(0, weight=0) # Hero Header
        self.left_col.grid_rowconfigure(1, weight=3) # Hero card
        self.left_col.grid_rowconfigure(2, weight=0) # Metrics Header
        self.left_col.grid_rowconfigure(3, weight=2) # Details grid
        self.left_col.grid_rowconfigure(4, weight=0) # Hourly Header
        self.left_col.grid_rowconfigure(5, weight=2) # Hourly forecast
        self.left_col.grid_columnconfigure(0, weight=1)

        # 0. Hero Section Header
        self.hero_hdr = ctk.CTkLabel(
            self.left_col, 
            text="CURRENT FORECAST", 
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#8E8E93"
        )
        self.hero_hdr.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # 1. Weather Hero Card (Muted sophisticated gradient/solid background)
        self.hero_card = ctk.CTkFrame(
            self.left_col, 
            fg_color="#1C1C1E", # Updated dynamically
            corner_radius=20,
            border_width=1,
            border_color="#2C2C2E"
        )
        self.hero_card.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        self.hero_card.grid_columnconfigure(0, weight=1)
        self.hero_card.grid_rowconfigure(1, weight=1)

        self.hero_meta_frame = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.hero_meta_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 0))
        self.hero_meta_frame.grid_columnconfigure(0, weight=1)
        self.hero_meta_frame.grid_columnconfigure(1, weight=0)
        
        self.city_label = ctk.CTkLabel(
            self.hero_meta_frame, 
            text="Detecting Location...", 
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color="#FFFFFF"
        )
        self.city_label.grid(row=0, column=0, sticky="w")
        
        self.date_label = ctk.CTkLabel(
            self.hero_meta_frame, 
            text="Fetching current forecast", 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#8E8E93"
        )
        self.date_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Modern AQI label inside the Current Forecast hero card
        self.aqi_label = ctk.CTkLabel(
            self.hero_meta_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF",
            fg_color="transparent"
        )
        self.aqi_label.grid(row=0, column=1, rowspan=2, sticky="e")

        # Main stats (Temp and Emoji Icon)
        self.hero_stats_frame = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.hero_stats_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=(5, 20))
        
        # UNIFORM HERO STATS LOCK: mathematically splits stats panel into exactly 50% left and 50% right
        self.hero_stats_frame.grid_columnconfigure(0, weight=1, uniform="hero_stats") # Temp
        self.hero_stats_frame.grid_columnconfigure(1, weight=1, uniform="hero_stats") # Emoji

        # REDUCED TEMP SIZE TO 60PX TO GUARANTEE NO BOX OVERFLOW OR CLIPPING
        self.temp_label = ctk.CTkLabel(
            self.hero_stats_frame, 
            text="--°", 
            font=ctk.CTkFont(family="Segoe UI", size=60, weight="bold"),
            text_color="#FFFFFF"
        )
        self.temp_label.grid(row=0, column=0, sticky="w")

        # REDUCED WEATHER STATE EMOJI SIZE TO 42PX FOR PERFECT BALANCED VISUAL WEIGHT
        self.emoji_label = ctk.CTkLabel(
            self.hero_stats_frame, 
            text="⌛", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=42),
            fg_color="transparent"
        )
        self.emoji_label.grid(row=0, column=1, sticky="e", padx=(0, 20))

        self.desc_label = ctk.CTkLabel(
            self.hero_stats_frame, 
            text="Initializing details...", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="normal"),
            text_color="#E5E5EA"
        )
        self.desc_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # 2. Metrics Section Header
        self.metrics_hdr = ctk.CTkLabel(
            self.left_col, 
            text="CLIMATE METRICS", 
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#8E8E93"
        )
        self.metrics_hdr.grid(row=2, column=0, sticky="w", pady=(0, 5))

        # Metrics Grid (4 flat, clean cards with no color borders)
        self.details_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.details_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 15))
        self.details_frame.grid_rowconfigure((0, 1), weight=1, uniform="equal")
        self.details_frame.grid_columnconfigure((0, 1), weight=1, uniform="equal")

        # Flat minimalist cards with dedicated soft, muted pastel colored icons and hover-reactivity
        self.feel_card = self.create_detail_card(self.details_frame, 0, 0, "🌡️", "RealFeel", "--°", "Apparent temperature", "#FF8A8A")  # Muted Rose
        self.wind_card = self.create_detail_card(self.details_frame, 0, 1, "💨", "Wind Speed", "-- km/h", "Wind flow rate", "#7FD8FF")  # Muted Blue-Sky
        self.humidity_card = self.create_detail_card(self.details_frame, 1, 0, "💧", "Humidity", "--%", "Relative air moisture", "#8AB4F8")  # Muted Cobalt
        self.rain_card = self.create_detail_card(self.details_frame, 1, 1, "🌧️", "Rain Chance", "--%", "Max daily probability", "#81C784")  # Muted Green-Mint

        # 4. Hourly Section Header
        self.hourly_hdr = ctk.CTkLabel(
            self.left_col, 
            text="24-HOUR FORECAST RADAR (SCROLLABLE)", 
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#8E8E93"
        )
        self.hourly_hdr.grid(row=4, column=0, sticky="w", pady=(0, 5))

        # Hourly Forecast Card List (Next 24 Hours - scrollable)
        self.hourly_frame = ctk.CTkFrame(self.left_col, fg_color="#1C1C1E", corner_radius=20, border_width=1, border_color="#2C2C2E")
        self.hourly_frame.grid(row=5, column=0, sticky="nsew")
        self.hourly_frame.grid_rowconfigure(0, weight=1)
        self.hourly_frame.grid_columnconfigure(0, weight=1)

        # Horizontal CTkScrollableFrame enabling horizontal scroll for all 24 hours
        self.hourly_scroll = ctk.CTkScrollableFrame(
            self.hourly_frame, 
            orientation="horizontal", 
            fg_color="transparent",
            height=100
        )
        self.hourly_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.hourly_scroll.grid_rowconfigure(0, weight=1)
        
        self.hourly_slots = []
        for i in range(24):
            slot = self.create_hourly_slot(self.hourly_scroll, i)
            self.hourly_slots.append(slot)

        # --- RIGHT COLUMN (7-Day Outlook) ---
        self.right_col = ctk.CTkFrame(
            self.main_container, 
            fg_color="#1C1C1E", 
            corner_radius=24,
            border_width=1,
            border_color="#2C2C2E"
        )
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        self.right_col.grid_rowconfigure(1, weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        # Sidebar Title
        self.forecast_title = ctk.CTkLabel(
            self.right_col,
            text="📅 7-Day Outlook",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#FFFFFF"
        )
        self.forecast_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Vertical list containing days
        self.days_container = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.days_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 20))
        self.days_container.grid_columnconfigure(0, weight=1)
        
        self.day_rows = []
        for i in range(7):
            self.days_container.grid_rowconfigure(i, weight=1, uniform="equal")
            row = self.create_forecast_row(self.days_container, i)
            self.day_rows.append(row)

    # --- UI Helper Component Builders ---
    
    def create_detail_card(self, parent, r, c, icon, title, value, subtitle, icon_color):
        """Creates a modern, clean charcoal card box with separate colored icon."""
        card = ctk.CTkFrame(parent, fg_color="#1C1C1E", corner_radius=16, border_width=1, border_color="#2C2C2E")
        card.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure((0, 1, 2), weight=1)

        # Container for Row 0: Icon and Title side-by-side
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="w", padx=18, pady=(15, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        icon_lbl = ctk.CTkLabel(
            header_frame, 
            text=icon, 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=14),
            text_color=icon_color
        )
        icon_lbl.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            header_frame, 
            text=title, 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#8E8E93"
        )
        title_lbl.grid(row=0, column=1, sticky="w", padx=(5, 0))

        val_lbl = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        val_lbl.grid(row=1, column=0, sticky="w", padx=18)

        sub_lbl = ctk.CTkLabel(
            card, 
            text=subtitle, 
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#48484A"
        )
        sub_lbl.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 15))

        # Make it dynamically reactive to mouse hovers
        self.make_reactive(card, "#1C1C1E", "#2C2C2E")

        return {"card": card, "title": title_lbl, "value": val_lbl, "subtitle": sub_lbl}

    def create_hourly_slot(self, parent, index):
        """Creates a single vertical hourly forecast pill-card with strict fixed width."""
        slot_frame = ctk.CTkFrame(parent, fg_color="#2C2C2E", corner_radius=12, border_width=1, border_color="#3A3A3C", width=80, height=90)
        slot_frame.grid(row=0, column=index, sticky="nsew", padx=4, pady=2)
        slot_frame.grid_propagate(False) # Strict layout locks so columns don't compress
        
        slot_frame.grid_rowconfigure((0, 1, 2), weight=1)
        slot_frame.grid_columnconfigure(0, weight=1)

        time_lbl = ctk.CTkLabel(
            slot_frame, 
            text="--:--", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#8E8E93"
        )
        time_lbl.grid(row=0, column=0, pady=(6, 0))

        emoji_lbl = ctk.CTkLabel(
            slot_frame, 
            text="❓", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=18)
        )
        emoji_lbl.grid(row=1, column=0, pady=2)

        temp_lbl = ctk.CTkLabel(
            slot_frame, 
            text="--°", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF"
        )
        temp_lbl.grid(row=2, column=0, pady=(0, 6))

        # Make it dynamically reactive to mouse hovers
        self.make_reactive(slot_frame, "#2C2C2E", "#3A3A3C")

        return {"frame": slot_frame, "time": time_lbl, "emoji": emoji_lbl, "temp": temp_lbl}

    def create_forecast_row(self, parent, index):
        """Creates a horizontal row widget showing one forecast day in the list with strictly locked dimensions."""
        # Apply a subtle highlight for even numbers for grid scannability
        bg_col = "#2C2C2E" if index % 2 == 0 else "transparent"
        border_w = 1 if index % 2 == 0 else 0
        row_frame = ctk.CTkFrame(
            parent, 
            fg_color=bg_col, 
            border_width=border_w, 
            border_color="#3A3A3C", 
            corner_radius=12, 
            height=45
        )

        row_frame.grid(row=index, column=0, sticky="ew", pady=3)
        
        # UNIFORM LAYOUT LOCKING: mathematically restricts column widths to prevent C/F swap resizing shifts
        row_frame.grid_columnconfigure(0, weight=3, uniform="days") # Day Name
        row_frame.grid_columnconfigure(1, weight=1, uniform="days") # Emoji Icon
        row_frame.grid_columnconfigure(2, weight=2, uniform="days") # Rain Prob
        row_frame.grid_columnconfigure(3, weight=3, uniform="days") # Temp Min/Max

        day_lbl = ctk.CTkLabel(
            row_frame, 
            text="--", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF"
        )
        day_lbl.grid(row=0, column=0, sticky="w", padx=15, pady=8)

        emoji_lbl = ctk.CTkLabel(
            row_frame, 
            text="❓", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=20)
        )
        emoji_lbl.grid(row=0, column=1)

        rain_lbl = ctk.CTkLabel(
            row_frame, 
            text="☔ 0%", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            text_color="#0A84FF" # Modern Apple blue
        )
        rain_lbl.grid(row=0, column=2)

        temp_lbl = ctk.CTkLabel(
            row_frame, 
            text="--° / --°", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF"
        )
        temp_lbl.grid(row=0, column=3, sticky="e", padx=(0, 10))

        # Make it dynamically reactive to mouse hovers
        self.make_reactive(row_frame, bg_col, "#3A3A3C")

        return {"frame": row_frame, "day": day_lbl, "emoji": emoji_lbl, "rain": rain_lbl, "temp": temp_lbl}

    def setup_loading_screen(self):
        """Full-screen modal that covers the app when loading."""
        self.loading_frame = ctk.CTkFrame(self, fg_color="#121212")
        self.loading_frame.grid_rowconfigure(0, weight=1)
        self.loading_frame.grid_columnconfigure(0, weight=1)

        inner_loading = ctk.CTkFrame(self.loading_frame, fg_color="transparent")
        inner_loading.grid(row=0, column=0)

        # Spinning Emoji
        self.loading_spinner = ctk.CTkLabel(
            inner_loading, 
            text="🌍", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=72)
        )
        self.loading_spinner.grid(row=0, column=0, pady=10)

        self.loading_lbl = ctk.CTkLabel(
            inner_loading,
            text="Locating current coordinates...",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="normal"),
            text_color="#8E8E93"
        )
        self.loading_lbl.grid(row=1, column=0, pady=5)
        
        # Subtle tip under loader
        self.loading_tip = ctk.CTkLabel(
            inner_loading,
            text="Fetching real-time satellite conditions...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#48484A"
        )
        self.loading_tip.grid(row=2, column=0)

    def setup_error_screen(self):
        """Clean offline and critical error overlay screen."""
        self.error_frame = ctk.CTkFrame(self, fg_color="#121212")
        self.error_frame.grid_rowconfigure(0, weight=1)
        self.error_frame.grid_columnconfigure(0, weight=1)

        inner_err = ctk.CTkFrame(self.error_frame, fg_color="transparent")
        inner_err.grid(row=0, column=0)

        self.error_icon = ctk.CTkLabel(
            inner_err, 
            text="⚠️", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=68)
        )
        self.error_icon.grid(row=0, column=0, pady=10)

        self.error_title_lbl = ctk.CTkLabel(
            inner_err,
            text="Failed to Retrieve Weather",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#FFFFFF"
        )
        self.error_title_lbl.grid(row=1, column=0, pady=5)

        self.error_desc_lbl = ctk.CTkLabel(
            inner_err,
            text="Check your network connection and search spelling.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#8E8E93"
        )
        self.error_desc_lbl.grid(row=2, column=0, pady=(0, 20))

        self.retry_btn = ctk.CTkButton(
            inner_err,
            text="Try Again",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            width=120,
            corner_radius=19,
            fg_color="#FF453A",
            hover_color="#FF3B30",
            text_color="#FFFFFF",
            command=self.fetch_local_weather
        )
        self.retry_btn.grid(row=3, column=0)

    # --- Loading & Layer Control Methods ---
    
    def flash_badge_error(self, message):
        """Displays a red error message in the header that automatically fades after 4 seconds."""
        self.error_badge.configure(text=message)
        if hasattr(self, "_error_clear_id") and self._error_clear_id:
            self.after_cancel(self._error_clear_id)
        self._error_clear_id = self.after(4000, lambda: self.error_badge.configure(text=""))

    def handle_error(self, message):
        """Thread-safe entry point to handle error."""
        self.after(0, lambda: self._ui_handle_error(message))

    def _ui_handle_error(self, message):
        """Actual UI updates for error handling on the main thread."""
        self.search_in_progress = False
        self.configure(cursor="")

        if self.is_dashboard_visible:
            self.flash_badge_error(message)
        else:
            self.show_error(message)

    def show_loading(self, text="Fetching real-time conditions..."):
        """Displays full-screen loading frame."""
        if self.is_dashboard_visible:
            self.main_container.grid_forget()
            self.is_dashboard_visible = False
        self.error_frame.grid_forget()
        self.loading_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        self.loading_lbl.configure(text=text)

    def show_error(self, message="Network issue occurred."):
        """Displays full-screen error frame."""
        if self.is_dashboard_visible:
            self.main_container.grid_forget()
            self.is_dashboard_visible = False
        self.loading_frame.grid_forget()
        self.error_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        self.error_desc_lbl.configure(text=message)

    def show_main(self):
        """Displays main dashboard panel once data loaded."""
        self.loading_frame.grid_forget()
        self.error_frame.grid_forget()
        
        self.search_in_progress = False
        self.configure(cursor="")

        # ONLY grid if the dashboard was completely hidden. Eliminates Celsius/Fahrenheit redrawing glitches!
        if not self.is_dashboard_visible:
            self.main_container.grid(row=1, column=0, sticky="nsew", padx=25, pady=(5, 25))
            self.is_dashboard_visible = True

    # --- Async Data Threading Core ---

    def run_async(self, target_fn, *args):
        """Fires network queries on background thread to prevent UI freezing."""
        threading.Thread(target=target_fn, args=args, daemon=True).start()

    # --- Weather Retrieval Controllers ---

    def fetch_local_weather(self):
        """IP locates user and fetches weather automatically."""
        if getattr(self, "search_in_progress", False) and self.is_dashboard_visible:
            return

        # Clear previous error
        self.error_badge.configure(text="")
        if hasattr(self, "_error_clear_id") and self._error_clear_id:
            self.after_cancel(self._error_clear_id)
            self._error_clear_id = None

        if self.is_dashboard_visible:
            self.search_in_progress = True
            self.configure(cursor="watch")
        else:
            self.show_loading("Locating current network IP coordinates...")

        self.run_async(self._thread_fetch_local)

    def _thread_fetch_local(self):
        geo = weather_api.detect_location_by_ip()
        if not geo["success"]:
            self.handle_error(geo.get("error", "No network connection."))
            return

        self.current_city = geo["city"]
        self.current_country = geo["country"]
        
        def update_label():
            if not self.is_dashboard_visible:
                self.loading_lbl.configure(text=f"Loading weather for {self.current_city}...")
        self.after(0, update_label)
        self._load_weather(geo["lat"], geo["lon"])

    def trigger_search(self):
        """Invoked when user clicks Search or presses Enter."""
        if getattr(self, "search_in_progress", False):
            return

        query = self.search_entry.get().strip()
        if not query:
            self.flash_badge_error("Enter a city name!")
            return

        # Clear previous error
        self.error_badge.configure(text="")
        if hasattr(self, "_error_clear_id") and self._error_clear_id:
            self.after_cancel(self._error_clear_id)
            self._error_clear_id = None

        if self.is_dashboard_visible:
            self.search_in_progress = True
            self.configure(cursor="watch")
        else:
            self.show_loading(f"Searching for '{query}'...")

        self.run_async(self._thread_search, query)

    def _thread_search(self, city_name):
        geo = weather_api.search_city(city_name)
        if not geo["success"]:
            self.handle_error(geo.get("error"))
            return

        self.current_city = geo["city"]
        self.current_country = geo["country"]
        
        def update_label():
            if not self.is_dashboard_visible:
                self.loading_lbl.configure(text=f"Loading weather for {self.current_city}...")
        self.after(0, update_label)
        self._load_weather(geo["lat"], geo["lon"])

    def _load_weather(self, lat, lon):
        weather = weather_api.fetch_weather_data(lat, lon)
        if not weather["success"]:
            self.handle_error(weather.get("error"))
            return

        self.weather_data = weather
        self.after(0, lambda: self.update_dashboard_ui(only_temp=False))

    # --- UI Rendering & Temperature Conversions ---

    def toggle_units(self, unit):
        """Triggered by the segmented Celsius/Fahrenheit control."""
        if getattr(self, "search_in_progress", False):
            self.unit_control.set(self.current_unit)
            return

        self.current_unit = unit
        if self.weather_data:
            # TEMPERATURE-ONLY MODE: swaps numbers instantly without redrawing header, search, logo or emoji icons
            self.update_dashboard_ui(only_temp=True)

    def convert_temp(self, celsius_val):
        """Converts raw Celsius value to user-selected scale."""
        if celsius_val is None:
            return "--"
        if self.current_unit == "°F":
            fahrenheit = (celsius_val * 9/5) + 32
            return f"{round(fahrenheit)}°F"
        return f"{round(celsius_val)}°C"

    def convert_wind(self, kmh_val):
        """Converts raw wind speed in km/h to mph."""
        if kmh_val is None:
            return "--"
        if self.current_unit == "°F":
            mph = kmh_val * 0.621371
            return f"{round(mph, 1)} mph"
        return f"{round(kmh_val, 1)} km/h"

    def update_dashboard_ui(self, only_temp=False):
        """Re-renders the widgets atomically when units toggle, preventing any render tearing glitches."""
        if not self.weather_data:
            return

        current = self.weather_data["current"]
        hourly = self.weather_data["hourly"]
        daily = self.weather_data["daily"]

        # ATOMIC RENDER LOCK: update labels on locked layout

        # 1. Update Temperature values in Hero Card
        feel_temp_str = self.convert_temp(current["apparent_temp"])
        self.temp_label.configure(text=self.convert_temp(current["temp"]))
        
        self.desc_label.configure(text=f"{current['desc']} (Feels like: {feel_temp_str})")

        # Update dynamic AQI Label with a clean leaf icon and color-coded text
        if current.get("aqi") is not None:
            aqi_val = current["aqi"]
            aqi_desc = current.get("aqi_desc", "Unknown")
            
            # Map quality index descriptor to professional text colors (supports both US EPA and Indian CPCB scales)
            text_color = "#FFFFFF"
            if aqi_desc == "Good":
                text_color = "#34C759"
            elif aqi_desc in ["Moderate", "Satisfactory"]:
                text_color = "#FFCC00"
            elif aqi_desc == "Sensitive":
                text_color = "#FF9500"
            elif aqi_desc in ["Unhealthy", "Poor"]:
                text_color = "#FF3B30"
            elif aqi_desc in ["Very Unhealthy", "Very Poor"]:
                text_color = "#AF52DE"
            elif aqi_desc in ["Hazardous", "Severe"]:
                text_color = "#FF2D55"
                
            self.aqi_label.configure(
                text=f"🍃 AQI: {aqi_val} ({aqi_desc})",
                text_color=text_color
            )
            self.aqi_label.grid(row=0, column=1, rowspan=2, sticky="e")
        else:
            self.aqi_label.grid_remove()

        # 2. Update Details Card Temperature & Wind Speed
        self.feel_card["value"].configure(text=feel_temp_str)
        self.wind_card["value"].configure(text=self.convert_wind(current["wind_speed"]))

        # 3. Update Hourly Forecast temperatures
        for idx, slot in enumerate(self.hourly_slots):
            if idx < len(hourly):
                data = hourly[idx]
                slot["temp"].configure(text=self.convert_temp(data["temp"]))

        # 4. Update 7-Day Forecast temperatures
        for idx, row in enumerate(self.day_rows):
            if idx < len(daily):
                data = daily[idx]
                min_max_text = f"{self.convert_temp(data['temp_min'])} / {self.convert_temp(data['temp_max'])}"
                row["temp"].configure(text=min_max_text)

        # If not just a temp toggle, update EVERYTHING else (backgrounds, text, static buttons, loading screens)
        if not only_temp:
            # Update dynamic header background theme in Hero panel
            theme_bg = "#2C2C2E" # Muted granite dark grey is default
            if current["weather_code"] in [0, 1]:
                theme_bg = "#1A1D24" if current["is_day"] else "#121318"
            elif current["weather_code"] in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
                theme_bg = "#141517"
            elif current["weather_code"] in [95, 96, 99]:
                theme_bg = "#1E1724"
                
            self.hero_card.configure(fg_color=theme_bg, border_color="#3A3A3C")

            location_text = f"{self.current_city}"
            if self.current_country:
                location_text += f", {self.current_country}"
            self.city_label.configure(text=location_text)
            
            # Calculate the exact real-time current local clock of the location using its UTC offset
            offset = current.get("utc_offset_seconds", 0)
            utc_now = datetime.datetime.utcnow()
            local_now = utc_now + datetime.timedelta(seconds=offset)
            formatted_time = local_now.strftime("%B %d, %H:%M")
                
            tz_abbr = current.get("timezone_abbreviation", "")
            tz_suffix = f" ({tz_abbr})" if tz_abbr else ""
            self.date_label.configure(text=f"Current Conditions • {formatted_time}{tz_suffix}")
            
            self.emoji_label.configure(text=current["emoji"])
            self.humidity_card["value"].configure(text=f"{current['humidity']}%")
            
            today_rain_prob = daily[0]["rain_prob"] if len(daily) > 0 else 0
            self.rain_card["value"].configure(text=f"{today_rain_prob}%")

            for idx, slot in enumerate(self.hourly_slots):
                if idx < len(hourly):
                    data = hourly[idx]
                    slot["time"].configure(text=data["time"])
                    slot["emoji"].configure(text=data["emoji"])

            for idx, row in enumerate(self.day_rows):
                if idx < len(daily):
                    data = daily[idx]
                    date_obj = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
                    if idx == 0:
                        day_name = "Today"
                    elif idx == 1:
                        day_name = "Tomorrow"
                    else:
                        day_name = date_obj.strftime("%A")

                    row["day"].configure(text=day_name)
                    row["emoji"].configure(text=data["emoji"])
                    row["rain"].configure(text=f"☔ {data['rain_prob']}%")

            self.error_badge.configure(text="")
            self.show_main()

        # ATOMIC FLUSH: Forces the OS window manager to render all text changes in one single screen refresh pass
        self.update_idletasks()

        # RELEASE RENDER LOCK: update complete

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
