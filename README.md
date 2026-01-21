# Detroit Roller Derby - Weather & Air Quality Alerts

Automated alert system that monitors National Weather Service weather alerts and air quality data for the Detroit metro area, posting to the DRD Slack #weather channel.

## 🌤️ What This Does

- Checks NWS API every hour for active weather alerts
- Checks WAQI (World Air Quality Index) API for current air quality
- Filters for severe/important weather alerts (Extreme, Severe, Moderate)
- **Only alerts for dangerous air quality** (Very Unhealthy or Hazardous, AQI >200)
- **Posts each unique alert only once** (no duplicate notifications)
- Monitors Wayne, Oakland, Macomb, and Washtenaw counties for weather
- Monitors Detroit area for air quality
- Runs completely free on GitHub Actions

## 🚀 How It Works

1. **GitHub Actions** runs on a schedule (every hour at :05 past the hour)
2. **Python script** (`weather_check.py`) fetches data from both NWS and WAQI APIs
3. **Checks alert IDs** against tracking files to avoid duplicates
4. **Filters** weather alerts by severity and location
5. **Filters** air quality by threshold (>200 AQI only)
6. **Posts** to Slack via webhook only for NEW alerts
7. **Updates tracking files** with posted alert IDs
8. **Logs** results in GitHub Actions for debugging

## 🔄 Deduplication System

The bot tracks every alert it posts using unique IDs:

### Weather Alerts
- Each NWS alert has a unique ID (like `urn:oid:2.49.0.1.840.0.abc123...`)
- When posted, ID is saved to `posted_alerts.txt`
- Future checks skip any alert ID already in the file

### Air Quality Alerts
- AQI alerts are tracked by date and category
- Only posts once per day per AQI category
- Saved to `posted_aqi.txt` as `YYYY-MM-DD_category`
- **Result: No spam, timely alerts only!**

## 📁 Repository Structure
```
drd-weather-alerts/
├── .github/
│   └── workflows/
│       └── weather-check.yml    # GitHub Actions workflow configuration
├── weather_check.py              # Main Python script
├── posted_alerts.txt             # Tracks posted weather alert IDs (auto-updated)
├── posted_aqi.txt                # Tracks posted AQI alert IDs (auto-updated)
└── README.md                     # This file
```

**Note:** Both tracking files are automatically updated by GitHub Actions. You should never need to edit them manually.

## 🔧 Configuration

### Weather Alert Severity Levels

Edit `weather_check.py` line 30:
```python
# Current setting (Extreme, Severe, Moderate):
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate']

# To only show critical alerts:
IMPORTANT_SEVERITY = ['Extreme', 'Severe']

# To include all advisories:
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate', 'Minor']
```

### Air Quality Alert Threshold

Edit `weather_check.py` around line 150:
```python
# Current: Only alert if AQI is very unhealthy or hazardous (>200)
if aqi <= 200:
    return False, None

# To alert at "Unhealthy" level (>150):
if aqi <= 150:
    return False, None

# To alert at "Unhealthy for Sensitive Groups" (>100):
if aqi <= 100:
    return False, None
```

**AQI Scale:**
- 🟢 0-50: Good
- 🟡 51-100: Moderate
- 🟠 101-150: Unhealthy for Sensitive Groups
- 🔴 151-200: Unhealthy
- 🟣 201-300: Very Unhealthy ← **Current threshold**
- 🟤 301-500: Hazardous ← **Current threshold**

### Weather Coverage Area

Edit `weather_check.py` line 18:
```python
# Current: Wayne, Oakland, Macomb, Washtenaw counties
WEATHER_PARAMS = {
    'zone': 'MIZ075,MIZ076,MIZ082,MIZ083',
    'status': 'actual'
}

# For just Wayne County (Detroit):
WEATHER_PARAMS = {'zone': 'MIZ075', 'status': 'actual'}

# For all of Michigan:
WEATHER_PARAMS = {'area': 'MI', 'status': 'actual'}
```

**Zone codes:**
- `MIZ075` - Wayne County (Detroit)
- `MIZ076` - Oakland County (Pontiac, Troy)
- `MIZ082` - Macomb County (Warren, Sterling Heights)
- `MIZ083` - Washtenaw County (Ann Arbor)

### Check Frequency

Edit `.github/workflows/weather-check.yml` line 6:
```yaml
# Current: Every hour at :05
- cron: '5 * * * *'

# Every 2 hours:
- cron: '5 */2 * * *'

# Every 30 minutes:
- cron: '*/30 * * * *'

# Every 4 hours:
- cron: '5 */4 * * *'
```

**Note:** Cron times are in UTC. Detroit is UTC-5 (EST) or UTC-4 (EDT). GitHub scheduled workflows may experience delays of up to 15 minutes during high load periods.

## 🔐 Secrets

The repository uses two GitHub secrets:

- **`SLACK_WEBHOOK_URL`**: Webhook URL for posting to Slack #weather channel
- **`WAQI_API_TOKEN`**: API token for World Air Quality Index (get free at https://aqicn.org/data-platform/token/)

### Updating Secrets

**Slack Webhook:**
1. Go to https://api.slack.com/apps
2. Select "Weather Bot" app
3. Go to "Incoming Webhooks"
4. Delete old webhook, create new one for #weather channel
5. In GitHub repo: Settings → Secrets → Actions
6. Update `SLACK_WEBHOOK_URL` with new URL

**WAQI API Token:**
1. Go to https://aqicn.org/data-platform/token/
2. Fill out form for free API access
3. Copy token from email
4. In GitHub repo: Settings → Secrets → Actions
5. Update `WAQI_API_TOKEN` with new token

## 🧪 Testing

### Manual Test Run

1. Go to **Actions** tab in this repo
2. Click **"Check Weather Alerts"** in left sidebar
3. Click **"Run workflow"** button (top right)
4. Select branch: `main`
5. Click **"Run workflow"**
6. Watch the logs to see results

### Expected Behavior

**When there are NO alerts:**
```
=== Starting weather and air quality check ===
--- Checking weather alerts ---
Tracking X weather alerts, Y AQI alerts
No new weather alerts
--- Checking air quality ---
Current AQI: 42 - no alert needed
=== Check complete ===
```

**When there ARE weather alerts:**
```
--- Checking weather alerts ---
Found 1 NEW weather alert(s)
Successfully sent message to Slack
Marked 1 weather alert(s) as posted
```

**When AQI is dangerous (>200):**
```
--- Checking air quality ---
AQI is 215 - sending alert
Successfully sent message to Slack
Marked AQI alert as posted: 2026-01-21_Very Unhealthy
```

## 🐛 Troubleshooting

### No alerts are posting to Slack

1. Check **Actions** tab for errors
2. Verify `SLACK_WEBHOOK_URL` secret is set correctly
3. Test webhook manually:
```bash
   curl -X POST -H 'Content-Type: application/json' \
   -d '{"text":"Test message"}' \
   YOUR_WEBHOOK_URL
```
4. Run manual test (see Testing section)
5. Check if alerts exist at:
   - Weather: https://www.weather.gov/dtx/
   - Air Quality: https://aqicn.org/city/detroit/

### Getting weather alerts for wrong area

- Check `WEATHER_PARAMS` configuration in `weather_check.py`
- Verify zone codes match your desired coverage area

### Too many/few weather alerts

- Adjust `IMPORTANT_SEVERITY` list in `weather_check.py`
- Current setting includes Extreme, Severe, and Moderate

### Too many/few air quality alerts

- Adjust AQI threshold in `weather_check.py` (see Configuration section)
- Current threshold: >200 (Very Unhealthy or Hazardous only)

### AQI not being checked

- Verify `WAQI_API_TOKEN` secret is set
- Check logs for "WAQI_API_TOKEN not set" warning
- Test token at: `https://api.waqi.info/feed/detroit/?token=YOUR_TOKEN`

### Duplicate alerts posting

- Check that both `posted_alerts.txt` and `posted_aqi.txt` exist
- Verify workflow has `permissions: contents: write`
- Check Actions logs to confirm tracking files are being updated
- View tracking files to see posted alert IDs

### Workflow fails with "exit code 128"

- GitHub Actions needs write permissions
- Verify workflow file has `permissions: contents: write` at the top

### Tracking files getting too large

- The script automatically cleans old entries (keeps last 100)
- Files should stay under 10KB
- No manual cleanup needed

### Scheduled workflows not running

- Check that repository is public (private repos have unreliable scheduled workflows)
- Wait 24-48 hours after making repo public - GitHub's scheduler needs time to activate
- Verify workflow syntax is correct
- Check Actions tab for any disabled workflows

## 📊 Monitoring

### Check the Actions Tab Regularly

Ensure:
- Workflow is running on schedule (roughly every hour)
- No errors in recent runs
- Python script is executing successfully
- Both tracking files are being updated

Green checkmarks = all good ✅  
Red X marks = needs attention ❌

### Failure Notifications

GitHub will email you when workflows fail. Make sure:
1. Go to https://github.com/settings/notifications
2. Under **Actions**, verify:
   - ✅ "Send notifications for failed workflows only"
   - ✅ Email is selected

## 🔄 Maintenance

### Regular Maintenance

- **None required!** This runs automatically
- Both tracking files clean themselves automatically

### Occasional Updates

- Update Python version in workflow if needed
- Adjust alert criteria based on feedback
- Modify coverage area if DRD moves practice locations
- Renew WAQI API token if needed (tokens don't expire under normal usage)

### Resetting Alert Tracking

If you want to clear tracked alerts (e.g., for testing):

**Weather alerts:**
1. Delete all contents of `posted_alerts.txt`
2. Commit the empty file
3. Next run will post any currently active weather alerts

**AQI alerts:**
1. Delete all contents of `posted_aqi.txt`
2. Commit the empty file
3. Next run will post if AQI is currently >200

## 📚 Resources

- [NWS API Documentation](https://www.weather.gov/documentation/services-web-api)
- [NWS Detroit Office](https://www.weather.gov/dtx/)
- [WAQI API Documentation](https://aqicn.org/api/)
- [Detroit Air Quality](https://aqicn.org/city/detroit/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)

## 📝 Alert Types Reference

**Weather Alert Types:**
- 🚨 **Extreme**: Blizzard Warning, Ice Storm Warning, Tornado Warning
- ⛔ **Severe**: Winter Storm Warning, Severe Thunderstorm Warning (destructive), Flash Flood Warning (catastrophic)
- ⚠️ **Moderate**: Winter Weather Advisory, Wind Advisory, Flood Advisory

**Air Quality Alert Types:**
- 🟣 **Very Unhealthy** (AQI 201-300): Everyone should avoid prolonged outdoor exertion
- 🟤 **Hazardous** (AQI 301-500): Health alert - everyone may experience serious effects

## 👥 Contact

**Maintained by:** Oi!
**Questions?** Post in #weather or DM the maintainer

## 📄 License

Internal use for Detroit Roller Derby only.

---

**Last Updated:** January 2026
