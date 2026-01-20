import os
import json
import requests
from datetime import datetime, timezone

# Configuration
NWS_API_URL = "https://api.weather.gov/alerts/active"
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
POSTED_ALERTS_FILE = 'posted_alerts.txt'

# Detroit metro area zones
PARAMS = {
    'zone': 'MIZ075,MIZ076,MIZ082,MIZ083',
    'status': 'actual'
}

HEADERS = {
    'User-Agent': 'DetroitRollerDerby-WeatherBot (github-actions)'
}

# Alert severity levels to monitor
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate']

def load_posted_alerts():
    """Load list of already-posted alert IDs"""
    try:
        with open(POSTED_ALERTS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_posted_alert(alert_id):
    """Save an alert ID as posted"""
    with open(POSTED_ALERTS_FILE, 'a') as f:
        f.write(f"{alert_id}\n")

def clean_old_alerts():
    """Remove alert IDs older than 7 days from tracking file"""
    try:
        with open(POSTED_ALERTS_FILE, 'r') as f:
            lines = f.readlines()
        
        # Keep last 100 alerts (roughly 4 days worth)
        if len(lines) > 100:
            with open(POSTED_ALERTS_FILE, 'w') as f:
                f.writelines(lines[-100:])
    except FileNotFoundError:
        pass

def format_timestamp(iso_time):
    """Convert ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p %b %d, %Y')
    except:
        return iso_time

def check_alerts():
    """Fetch alerts from NWS API"""
    try:
        response = requests.get(NWS_API_URL, params=PARAMS, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching alerts: {e}")
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
        alert_id = props.get('id')  # Unique ID from NWS
        
        # Check if important and not already posted
        if severity in IMPORTANT_SEVERITY and alert_id not in posted_alerts:
            new_important.append(props)
    
    return new_important

def format_slack_message(alerts):
    """Format alerts into Slack message"""
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
        print(f"Successfully sent alert to Slack")
        return True
    except requests.RequestException as e:
        print(f"Error sending to Slack: {e}")
        return False

def main():
    print("Checking for weather alerts...")
    
    # Load previously posted alerts
    posted_alerts = load_posted_alerts()
    print(f"Tracking {len(posted_alerts)} previously posted alerts")
    
    # Clean old alerts from tracking
    clean_old_alerts()
    
    # Fetch current alerts
    data = check_alerts()
    if not data:
        print("Failed to fetch alert data")
        return
    
    # Filter for new important alerts
    new_alerts = filter_important_alerts(data, posted_alerts)
    
    if not new_alerts:
        print("No new important alerts found")
        return
    
    print(f"Found {len(new_alerts)} NEW important alert(s)")
    
    # Format and send to Slack
    message = format_slack_message(new_alerts)
    if message and send_to_slack(message):
        # Mark these alerts as posted
        for props in new_alerts:
            alert_id = props.get('id')
            if alert_id:
                save_posted_alert(alert_id)
        print(f"Marked {len(new_alerts)} alert(s) as posted")

if __name__ == "__main__":
    main()
