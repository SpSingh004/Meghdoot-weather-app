import requests

# Dictionary mapping WMO Weather Codes to descriptions and colorful emojis.
WMO_CODES = {
    0: {"desc": "Clear Sky", "emoji_day": "☀️", "emoji_night": "🌙"},
    1: {"desc": "Mainly Clear", "emoji_day": "🌤️", "emoji_night": "🌙"},
    2: {"desc": "Partly Cloudy", "emoji_day": "⛅", "emoji_night": "☁️"},
    3: {"desc": "Overcast", "emoji_day": "☁️", "emoji_night": "☁️"}, # Sun/Moon fully covered
    45: {"desc": "Foggy", "emoji_day": "🌫️", "emoji_night": "🌫️"},
    48: {"desc": "Depositing Rime Fog", "emoji_day": "🌫️", "emoji_night": "🌫️"},
    51: {"desc": "Light Drizzle", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    53: {"desc": "Moderate Drizzle", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    55: {"desc": "Dense Drizzle", "emoji_day": "🌧️", "emoji_night": "🌧️"}, # Sun/Moon fully covered
    56: {"desc": "Light Freezing Drizzle", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    57: {"desc": "Dense Freezing Drizzle", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    61: {"desc": "Slight Rain", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    63: {"desc": "Moderate Rain", "emoji_day": "🌧️", "emoji_night": "🌧️"}, # Sun/Moon fully covered
    65: {"desc": "Heavy Rain", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    66: {"desc": "Light Freezing Rain", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    67: {"desc": "Heavy Freezing Rain", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    71: {"desc": "Slight Snowfall", "emoji_day": "❄️", "emoji_night": "❄️"}, # Sun/Moon fully covered
    73: {"desc": "Moderate Snowfall", "emoji_day": "❄️", "emoji_night": "❄️"},
    75: {"desc": "Heavy Snowfall", "emoji_day": "❄️", "emoji_night": "❄️"},
    77: {"desc": "Snow Grains", "emoji_day": "❄️", "emoji_night": "❄️"},
    80: {"desc": "Slight Rain Showers", "emoji_day": "🌦️", "emoji_night": "🌧️"},
    81: {"desc": "Moderate Rain Showers", "emoji_day": "🌦️", "emoji_night": "🌧️"},
    82: {"desc": "Violent Rain Showers", "emoji_day": "🌧️", "emoji_night": "🌧️"},
    85: {"desc": "Slight Snow Showers", "emoji_day": "❄️", "emoji_night": "❄️"},
    86: {"desc": "Heavy Snow Showers", "emoji_day": "❄️", "emoji_night": "❄️"},
    95: {"desc": "Thunderstorm", "emoji_day": "⛈️", "emoji_night": "⛈️"}, # Sun/Moon fully covered
    96: {"desc": "Thunderstorm with Hail", "emoji_day": "⛈️", "emoji_night": "⛈️"},
    99: {"desc": "Heavy Thunderstorm with Hail", "emoji_day": "⛈️", "emoji_night": "⛈️"}
}

def get_weather_info(weather_code, is_day=1):
    """
    Returns description and emoji based on WMO code and day/night.
    """
    info = WMO_CODES.get(weather_code, {"desc": "Unknown Conditions", "emoji_day": "🌡️", "emoji_night": "🌡️"})
    emoji = info["emoji_day"] if is_day == 1 else info["emoji_night"]
    return {
        "desc": info["desc"],
        "emoji": emoji
    }

def detect_location_by_ip():
    """
    Geolocates the user based on their external IP address.
    Utilizes ipapi.co with a failover to ip-api.com for maximum reliability.
    Returns:
        dict: {'success': True, 'lat': float, 'lon': float, 'city': str, 'country': str}
        or {'success': False, 'error': str}
    """
    # Primary Geolocation API (ipapi.co)
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                return {
                    "success": True,
                    "lat": float(data.get("latitude")),
                    "lon": float(data.get("longitude")),
                    "city": data.get("city", "Unknown City"),
                    "country": data.get("country_name", "Unknown Country")
                }
    except Exception:
        pass  # Failover to second service if primary fails

    # Failover Geolocation API (ip-api.com)
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "success": True,
                    "lat": float(data.get("lat")),
                    "lon": float(data.get("lon")),
                    "city": data.get("city", "Unknown City"),
                    "country": data.get("country", "Unknown Country")
                }
    except Exception as e:
        return {"success": False, "error": f"Failed to detect location: {str(e)}"}

    return {"success": False, "error": "Geolocation services are currently unreachable."}

def search_city(city_name):
    """
    Converts a human-entered city name to coordinates using Open-Meteo's free Geocoding API.
    Returns:
        dict: {'success': True, 'lat': float, 'lon': float, 'city': str, 'country': str}
        or {'success': False, 'error': str}
    """
    if not city_name.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results")
            if results and len(results) > 0:
                result = results[0]
                return {
                    "success": True,
                    "lat": float(result.get("latitude")),
                    "lon": float(result.get("longitude")),
                    "city": result.get("name"),
                    "country": result.get("country", "")
                }
            else:
                return {"success": False, "error": f"City '{city_name}' not found."}
        else:
            return {"success": False, "error": f"Geocoding API error (Status {response.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Geocoding network error: {str(e)}"}

def calculate_us_aqi(pm25, pm10, o3=None, no2=None):
    """
    Calculates US AQI based on EPA breakpoints for PM2.5, PM10, Ozone, and NO2.
    Returns the maximum of the indices.
    """
    if pm25 is None and pm10 is None:
        return None
        
    def pm25_aqi(c):
        if c is None or c < 0: return 0
        c = round(c, 1)
        if 0.0 <= c <= 9.0: return round((50 / 9.0) * c)
        elif 9.1 <= c <= 35.4: return round(((100 - 51) / (35.4 - 9.1)) * (c - 9.1) + 51)
        elif 35.5 <= c <= 55.4: return round(((150 - 101) / (55.4 - 35.5)) * (c - 35.5) + 101)
        elif 55.5 <= c <= 125.4: return round(((200 - 151) / (125.4 - 55.5)) * (c - 55.5) + 151)
        elif 125.5 <= c <= 225.4: return round(((300 - 201) / (225.4 - 125.5)) * (c - 125.5) + 201)
        elif 225.5 <= c <= 325.4: return round(((400 - 301) / (325.4 - 225.5)) * (c - 225.5) + 301)
        elif 325.5 <= c <= 500.4: return round(((500 - 401) / (500.4 - 325.5)) * (c - 325.5) + 401)
        else: return 500

    def pm10_aqi(c):
        if c is None or c < 0: return 0
        c = round(c)
        if 0 <= c <= 54: return round((50 / 54) * c)
        elif 55 <= c <= 154: return round(((100 - 51) / (154 - 55)) * (c - 55) + 51)
        elif 155 <= c <= 254: return round(((150 - 101) / (254 - 155)) * (c - 155) + 101)
        elif 255 <= c <= 354: return round(((200 - 151) / (354 - 255)) * (c - 255) + 151)
        elif 355 <= c <= 424: return round(((300 - 201) / (424 - 355)) * (c - 355) + 201)
        elif 425 <= c <= 504: return round(((400 - 301) / (504 - 425)) * (c - 425) + 301)
        elif 505 <= c <= 604: return round(((500 - 401) / (604 - 505)) * (c - 505) + 401)
        else: return 500

    def o3_aqi(c):
        if c is None or c < 0: return 0
        # Convert ug/m3 to ppb: 1 ug/m3 = 0.51 ppb
        ppb = c * 0.51
        if 0.0 <= ppb <= 54.0: return round((50 / 54.0) * ppb)
        elif 54.1 <= ppb <= 70.0: return round(((100 - 51) / (70.0 - 54.1)) * (ppb - 54.1) + 51)
        elif 70.1 <= ppb <= 85.0: return round(((150 - 101) / (85.0 - 70.1)) * (ppb - 70.1) + 101)
        elif 85.1 <= ppb <= 105.0: return round(((200 - 151) / (105.0 - 85.1)) * (ppb - 85.1) + 151)
        elif 105.1 <= ppb <= 200.0: return round(((300 - 201) / (200.0 - 105.1)) * (ppb - 105.1) + 201)
        else: return 500

    def no2_aqi(c):
        if c is None or c < 0: return 0
        # Convert ug/m3 to ppb: 1 ug/m3 = 0.53 ppb
        ppb = c * 0.53
        if 0.0 <= ppb <= 53.0: return round((50 / 53.0) * ppb)
        elif 53.1 <= ppb <= 100.0: return round(((100 - 51) / (100.0 - 53.1)) * (ppb - 53.1) + 51)
        elif 100.1 <= ppb <= 360.0: return round(((150 - 101) / (360.0 - 100.1)) * (ppb - 100.1) + 101)
        elif 360.1 <= ppb <= 649.0: return round(((200 - 151) / (649.0 - 360.1)) * (ppb - 360.1) + 151)
        else: return 500

    val25 = pm25_aqi(pm25) if pm25 is not None else 0
    val10 = pm10_aqi(pm10) if pm10 is not None else 0
    val_o3 = o3_aqi(o3) if o3 is not None else 0
    val_no2 = no2_aqi(no2) if no2 is not None else 0
    return max(val25, val10, val_o3, val_no2)

def fetch_weather_data(lat, lon):
    """
    Fetches full weather dataset for specific coordinates including:
    - Current: temp, humidity, apparent temp, day/night status, weather code, wind speed.
    - Hourly (next 24 hours): temperatures and weather codes.
    - Daily (next 7 days): min/max temperatures, precipitation, and weather codes.
    Returns:
        dict: {'success': True, 'current': ..., 'hourly': ..., 'daily': ...}
        or {'success': False, 'error': str}
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Fetch Air Quality Index (AQI)
            aqi_val = None
            aqi_desc = "Unknown"
            try:
                aqi_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
                aqi_params = {"latitude": lat, "longitude": lon, "current": "pm2_5,pm10,ozone,nitrogen_dioxide"}
                aqi_res = requests.get(aqi_url, params=aqi_params, timeout=3)
                if aqi_res.status_code == 200:
                    aqi_data = aqi_res.json()
                    current_aqi = aqi_data.get("current", {})
                    pm25_val = current_aqi.get("pm2_5")
                    pm10_val = current_aqi.get("pm10")
                    o3_val = current_aqi.get("ozone")
                    no2_val = current_aqi.get("nitrogen_dioxide")
                    aqi_val = calculate_us_aqi(pm25_val, pm10_val, o3_val, no2_val)
                    
                    if aqi_val is not None:
                        if aqi_val <= 50:
                            aqi_desc = "Good"
                        elif aqi_val <= 100:
                            aqi_desc = "Moderate"
                        elif aqi_val <= 150:
                            aqi_desc = "Sensitive"
                        elif aqi_val <= 200:
                            aqi_desc = "Unhealthy"
                        elif aqi_val <= 300:
                            aqi_desc = "Very Unhealthy"
                        else:
                            aqi_desc = "Hazardous"
            except Exception:
                pass

            # Format and bundle the response logically
            current_raw = data.get("current", {})
            current_info = get_weather_info(current_raw.get("weather_code", 0), current_raw.get("is_day", 1))
            
            current_processed = {
                "temp": current_raw.get("temperature_2m"),
                "humidity": current_raw.get("relative_humidity_2m"),
                "apparent_temp": current_raw.get("apparent_temperature"),
                "is_day": current_raw.get("is_day"),
                "precipitation": current_raw.get("precipitation"),
                "weather_code": current_raw.get("weather_code"),
                "wind_speed": current_raw.get("wind_speed_10m"),
                "desc": current_info["desc"],
                "emoji": current_info["emoji"],
                "time": current_raw.get("time"),
                "aqi": aqi_val,
                "aqi_desc": aqi_desc,
                "timezone_abbreviation": data.get("timezone_abbreviation"),
                "utc_offset_seconds": data.get("utc_offset_seconds", 0)
            }

            # Slice next 24 hours of hourly data starting from the active current hour
            hourly_raw = data.get("hourly", {})
            raw_times = hourly_raw.get("time", [])
            
            # Find the index corresponding to the current hour (e.g. YYYY-MM-DDTHH:00)
            now_str = current_raw.get("time", "")
            # Align 15-minute model time (e.g. 01:15) to hourly intervals (e.g. 01:00) for exact match
            if now_str and "T" in now_str:
                parts = now_str.split("T")
                time_part = parts[1].split(":")[0] + ":00"
                now_str = f"{parts[0]}T{time_part}"
                
            start_idx = 0
            if now_str:
                for idx, t in enumerate(raw_times):
                    if t.startswith(now_str):
                        start_idx = idx
                        break
            
            # Slice 24 elements from the active current hour onwards
            times = raw_times[start_idx:start_idx+24]
            temps = hourly_raw.get("temperature_2m", [])[start_idx:start_idx+24]
            codes = hourly_raw.get("weather_code", [])[start_idx:start_idx+24]
            
            hourly_processed = []
            for i in range(len(times)):
                # Determine is_day dynamically for each forecast hour (Day: 6 AM to 6 PM)
                if "T" in times[i]:
                    hour_val = int(times[i].split("T")[1].split(":")[0])
                else:
                    hour_val = 12
                
                is_day_hour = 1 if (6 <= hour_val < 18) else 0
                hour_info = get_weather_info(codes[i], is_day=is_day_hour)
                
                # Extract simple HH:MM
                time_str = times[i].split("T")[1] if "T" in times[i] else times[i]
                hourly_processed.append({
                    "time": time_str,
                    "temp": temps[i],
                    "emoji": hour_info["emoji"]
                })

            # Process 7-day forecast
            daily_raw = data.get("daily", {})
            d_times = daily_raw.get("time", [])
            d_codes = daily_raw.get("weather_code", [])
            d_maxs = daily_raw.get("temperature_2m_max", [])
            d_mins = daily_raw.get("temperature_2m_min", [])
            d_rain_probs = daily_raw.get("precipitation_probability_max", [])
            
            daily_processed = []
            for i in range(len(d_times)):
                day_info = get_weather_info(d_codes[i], is_day=1)
                daily_processed.append({
                    "date": d_times[i],  # e.g., "2026-05-31"
                    "weather_code": d_codes[i],
                    "desc": day_info["desc"],
                    "emoji": day_info["emoji"],
                    "temp_max": d_maxs[i],
                    "temp_min": d_mins[i],
                    "rain_prob": d_rain_probs[i] if i < len(d_rain_probs) else 0
                })

            return {
                "success": True,
                "current": current_processed,
                "hourly": hourly_processed,
                "daily": daily_processed
            }
        else:
            return {"success": False, "error": f"Weather API error (Status {response.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Weather network error: {str(e)}"}
