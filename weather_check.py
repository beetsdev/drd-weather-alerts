import os
import json
import requests
from datetime import datetime

# Configuration
NWS_API_URL = "https://api.weather.gov/alerts/active"
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

# Detroit metro area zones
PARAMS = {
    'zone': 'MIZ075,MIZ076,MIZ082,MIZ083',  # Wayne, Oakland, Macomb, Washtenaw
    'status': 'actual'
}

HEADERS = {
    'User-Agent': 'DetroitRollerDerby-WeatherBot (github-actions)'
}

# Alert severity levels to monitor
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate']

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

def filter_important_alerts(data):
    """Filter for severe/important alerts only"""
    if not data or 'features' not in data:
        return []
    
    alerts = data['features']
    important = []
    
    for alert in alerts:
        props = alert.get('properties', {})
        severity = props.get('severity')
        
        if severity in IMPORTANT_SEVERITY:
            important.append(props)
    
    return important

def format_slack_message(alerts):
    """Format alerts into Slack message"""
    if not alerts:
        return None
    
    alert_count = len(alerts)
    header = f"🌤️ *{alert_count} Active Weather Alert{'s' if alert_count > 1 else ''}*\n\n"
    
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
            # Truncate long instructions
            inst = instruction[:400] + "..." if len(instruction) > 400 else instruction
            alert_text += f"\n\n📋 *What to do:*\n{inst}"
        
        alert_blocks.append(alert_text)
    
    # Combine all alerts
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
    
    # Fetch alerts
    data = check_alerts()
    if not data:
        print("Failed to fetch alert data")
        return
    
    # Filter important alerts
    important_alerts = filter_important_alerts(data)
    
    if not important_alerts:
        print("No important alerts found")
        return
    
    print(f"Found {len(important_alerts)} important alert(s)")
    
    # Format and send to Slack
    message = format_slack_message(important_alerts)
    if message:
        send_to_slack(message)

if __name__ == "__main__":
    main()
