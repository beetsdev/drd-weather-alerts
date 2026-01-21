import os
import json
import requests
from datetime import datetime, timezone

# Configuration
NWS_API_URL = "https://api.weather.gov/alerts/active"
WAQI_API_URL = "https://api.waqi.info/feed/detroit/"
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
WAQI_API_TOKEN = os.environ.get('WAQI_API_TOKEN')
POSTED_ALERTS_FILE = 'posted_alerts.txt'
POSTED_AQI_FILE = 'posted_aqi.txt'

# Detroit metro area zones
WEATHER_PARAMS = {
    'zone': 'MIZ075,MIZ076,MIZ082,MIZ083',
    'status': 'actual'
}

NWS_HEADERS = {
    'User-Agent': 'DetroitRollerDerby-WeatherBot (github-actions)'
}

# Alert severity levels to monitor
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate']

# AQI thresholds (US EPA scale)
AQI_THRESHOLDS = {
    'good': (0, 50),
    'moderate': (51, 100),
    'unhealthy_sensitive': (101, 150),
    'unhealthy': (151, 200),
    'very_unhealthy': (201, 300),
    'hazardous': (301, 500)
}

def load_posted_items(filename):
    """Load list of already-posted item IDs"""
    try:
        with open(filename, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_posted_item(filename, item_id):
    """Save an item ID as posted"""
    with open(filename, 'a') as f:
        f.write(f"{item_id}\n")

def clean_old_items(filename):
    """Remove old IDs from tracking file"""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Keep last 100 items
        if len(lines) > 100:
            with open(filename, 'w') as f:
                f.writelines(lines[-100:])
    except FileNotFoundError:
        pass

def get_aqi_category(aqi):
    """Determine AQI category and emoji"""
    if aqi <= 50:
        return "Good", "🟢"
    elif aqi <= 100:
        return "Moderate", "🟡"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🟠"
    elif aqi <= 200:
        return "Unhealthy", "🔴"
    elif aqi <= 300:
        return "Very Unhealthy", "🟣"
    else:
        return "Hazardous", "🟤"

def format_timestamp(iso_time):
    """Convert ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p %b %d, %Y')
    except:
        return iso_time

# ==================== WEATHER ALERTS ====================

def check_weather_alerts():
    """Fetch weather alerts from NWS API"""
    try:
        response = requests.get(NWS_API_URL, params=WEATHER_PARAMS, headers=NWS_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching weather alerts: {e}")
        return None

def filter_important_alerts(data, posted_alerts):
    """Filter for severe/important alerts that haven't been posted yet"""
    if not data or 'features' not in data:
        return []
    
    alerts = data['features']
    new_important = []
    
    for alert in alerts:
        props = alert.get('properties', {})
        severity = props.get('severity')
        alert_id = props.get('id')
        
        if severity in IMPORTANT_SEVERITY and alert_id not in posted_alerts:
            new_important.append(props)
    
    return new_important

def format_weather_slack_message(alerts):
    """Format weather alerts into Slack message"""
    if not alerts:
        return None
    
    alert_count = len(alerts)
    header = f"🌤️ *{alert_count} New Weather Alert{'s' if alert_count > 1 else ''}*\n\n"
    
    alert_blocks = []
    
    for props in alerts:
        severity = props.get('severity', 'Unknown')
        event = props.get('event', 'Weather Alert')
        headline = props.get('headline', '')
        area = props.get('areaDesc', '')
        effective = props.get('effective', '')
        expires = props.get('expires', '')
        instruction = props.get('instruction', '')
        
        # Choose emoji
        if severity == 'Extreme':
            emoji = '🚨'
        elif severity == 'Severe':
            emoji = '⛔'
        else:
            emoji = '⚠️'
        
        # Format times
        effective_time = format_timestamp(effective)
        expires_time = format_timestamp(expires)
        
        # Build alert block
        alert_text = f"{emoji} *{event}* ({severity})\n"
        alert_text += f"📍 {area}\n"
        alert_text += f"⏰ Effective: {effective_time}\n"
        alert_text += f"⌛ Expires: {expires_time}\n\n"
        alert_text += f"*{headline}*"
        
        if instruction:
            inst = instruction[:400] + "..." if len(instruction) > 400 else instruction
            alert_text += f"\n\n📋 *What to do:*\n{inst}"
        
        alert_blocks.append(alert_text)
    
    combined = "\n\n────────────────────────────\n\n".join(alert_blocks)
    
    return {
        "text": header + combined,
        "username": "NWS Weather Bot",
        "icon_emoji": ":mostly_sunny:"
    }

# ==================== AIR QUALITY ====================

def check_air_quality():
    """Fetch air quality data from WAQI API"""
    if not WAQI_API_TOKEN:
        print("Warning: WAQI_API_TOKEN not set, skipping AQI check")
        return None
    
    try:
        url = f"{WAQI_API_URL}?token={WAQI_API_TOKEN}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching air quality: {e}")
        return None

def should_alert_aqi(aqi_data, posted_aqi):
    """Determine if we should alert based on AQI level and whether it's been posted"""
    if not aqi_data or aqi_data.get('status') != 'ok':
        return False, None
    
    data = aqi_data.get('data', {})
    aqi = data.get('aqi')
    
    if not aqi or aqi == '-':
        return False, None
    
    try:
        aqi = int(aqi)
    except (ValueError, TypeError):
        return False, None
    
     # Only alert if AQI is very unhealthy or hazardous (>200)
    if aqi <= 200:
        return False, None
    
    # Create a unique ID for this AQI alert level
    # We'll alert once per day per AQI category
    today = datetime.now().strftime('%Y-%m-%d')
    category, _ = get_aqi_category(aqi)
    aqi_id = f"{today}_{category}"
    
    if aqi_id in posted_aqi:
        return False, None
    
    return True, (aqi, aqi_id, data)

def format_aqi_slack_message(aqi, data):
    """Format AQI data into Slack message"""
    category, emoji = get_aqi_category(aqi)
    
    # Get dominant pollutant
    dominant = data.get('dominentpol', 'unknown')
    pollutant_names = {
        'pm25': 'PM2.5 (Fine Particulates)',
        'pm10': 'PM10 (Coarse Particulates)',
        'o3': 'Ozone',
        'no2': 'Nitrogen Dioxide',
        'so2': 'Sulfur Dioxide',
        'co': 'Carbon Monoxide'
    }
    dominant_name = pollutant_names.get(dominant, dominant.upper())
    
    # Get specific pollutant values if available
    iaqi = data.get('iaqi', {})
    pollutant_details = []
    
    if 'pm25' in iaqi:
        pollutant_details.append(f"PM2.5: {iaqi['pm25'].get('v', 'N/A')} µg/m³")
    if 'pm10' in iaqi:
        pollutant_details.append(f"PM10: {iaqi['pm10'].get('v', 'N/A')} µg/m³")
    if 'o3' in iaqi:
        pollutant_details.append(f"Ozone: {iaqi['o3'].get('v', 'N/A')} µg/m³")
    
    pollutant_text = "\n".join(pollutant_details) if pollutant_details else ""
    
    # Health recommendations based on AQI
    if aqi <= 150:
        health_msg = "⚠️ *Sensitive groups* should limit prolonged outdoor exertion"
    elif aqi <= 200:
        health_msg = "⚠️ *Everyone* should limit prolonged outdoor exertion\n🚫 *Sensitive groups* should avoid prolonged outdoor exertion"
    elif aqi <= 300:
        health_msg = "🚫 *Everyone* should avoid prolonged outdoor exertion\n⛔ *Sensitive groups* should remain indoors"
    else:
        health_msg = "⛔ *Everyone* should avoid all outdoor exertion\n🆘 *Health alert*: Everyone may experience serious health effects"
    
    # Build message
    message = f"{emoji} *Air Quality Alert*\n\n"
    message += f"📍 Detroit Metro Area\n"
    message += f"🌫️ AQI: *{aqi}* ({category})\n"
    message += f"💨 Dominant pollutant: {dominant_name}\n"
    
    if pollutant_text:
        message += f"\n{pollutant_text}\n"
    
    message += f"\n{health_msg}\n"
    message += f"\n_Checked at {datetime.now().strftime('%I:%M %p')}_"
    
    return {
        "text": message,
        "username": "Air Quality Bot",
        "icon_emoji": ":dash:"
    }

# ==================== SLACK ====================

def send_to_slack(message):
    """Send message to Slack"""
    if not SLACK_WEBHOOK_URL:
        print("Error: SLACK_WEBHOOK_URL not set")
        return False
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        print(f"Successfully sent message to Slack")
        return True
    except requests.RequestException as e:
        print(f"Error sending to Slack: {e}")
        return False

# ==================== MAIN ====================

def main():
    print("=== Starting weather and air quality check ===")
    
    # Load tracking files
    posted_alerts = load_posted_items(POSTED_ALERTS_FILE)
    posted_aqi = load_posted_items(POSTED_AQI_FILE)
    print(f"Tracking {len(posted_alerts)} weather alerts, {len(posted_aqi)} AQI alerts")
    
    # Clean old entries
    clean_old_items(POSTED_ALERTS_FILE)
    clean_old_items(POSTED_AQI_FILE)
    
    # Check weather alerts
    print("\n--- Checking weather alerts ---")
    weather_data = check_weather_alerts()
    if weather_data:
        new_alerts = filter_important_alerts(weather_data, posted_alerts)
        
        if new_alerts:
            print(f"Found {len(new_alerts)} NEW weather alert(s)")
            message = format_weather_slack_message(new_alerts)
            if message and send_to_slack(message):
                for props in new_alerts:
                    alert_id = props.get('id')
                    if alert_id:
                        save_posted_item(POSTED_ALERTS_FILE, alert_id)
                print(f"Marked {len(new_alerts)} weather alert(s) as posted")
        else:
            print("No new weather alerts")
    else:
        print("Failed to fetch weather data")
    
    # Check air quality
    print("\n--- Checking air quality ---")
    aqi_data = check_air_quality()
    if aqi_data:
        should_alert, aqi_info = should_alert_aqi(aqi_data, posted_aqi)
        
        if should_alert and aqi_info:
            aqi, aqi_id, data = aqi_info
            print(f"AQI is {aqi} - sending alert")
            message = format_aqi_slack_message(aqi, data)
            if message and send_to_slack(message):
                save_posted_item(POSTED_AQI_FILE, aqi_id)
                print(f"Marked AQI alert as posted: {aqi_id}")
        else:
            current_aqi = aqi_data.get('data', {}).get('aqi', 'N/A')
            print(f"Current AQI: {current_aqi} - no alert needed")
    else:
        print("Failed to fetch air quality data")
    
    print("\n=== Check complete ===")

if __name__ == "__main__":
    main()
