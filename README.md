# Detroit Roller Derby - Weather Alerts

Automated weather alert system that monitors National Weather Service alerts for the Detroit metro area and posts them to the DRD Slack #weather channel.

## 🌤️ What This Does

- Checks NWS API every hour for active weather alerts
- Filters for severe/important alerts only (Extreme, Severe, Moderate)
- **Posts each unique alert only once** (no duplicate notifications)
- Monitors Wayne, Oakland, Macomb, and Washtenaw counties
- Runs completely free on GitHub Actions

## 🚀 How It Works

1. **GitHub Actions** runs on a schedule (every hour at :05 past the hour)
2. **Python script** (`weather_check.py`) fetches alerts from NWS API
3. **Checks alert IDs** against tracking file to avoid duplicates
4. **Filters** alerts by severity and location
5. **Posts** to Slack via webhook only for NEW alerts
6. **Updates tracking file** (`posted_alerts.txt`) with posted alert IDs
7. **Logs** results in GitHub Actions for debugging

## 🔄 Deduplication System

The bot tracks every alert it posts using unique NWS alert IDs:

- Each NWS alert has a unique ID (like `urn:oid:2.49.0.1.840.0.abc123...`)
- When an alert is posted, its ID is saved to `posted_alerts.txt`
- Future checks skip any alert ID already in the file
- **Result: Each alert posts exactly once, no spam!**

Even if:
- An alert is active for 12 hours → only posts once
- NWS updates/amends an alert → still won't re-post
- You manually run the workflow → won't duplicate

## 📁 Repository Structure
```
drd-weather-alerts/
├── .github/
│   └── workflows/
│       └── weather-check.yml    # GitHub Actions workflow configuration
├── weather_check.py              # Main Python script
├── posted_alerts.txt             # Tracks posted alert IDs (auto-updated)
└── README.md                     # This file
```

**Note:** `posted_alerts.txt` is automatically updated by GitHub Actions. You should never need to edit it manually.

## 🔧 Configuration

### Alert Severity Levels

Edit `weather_check.py` line 20:
```python
# Current setting (Extreme, Severe, Moderate):
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate']

# To only show critical alerts:
IMPORTANT_SEVERITY = ['Extreme', 'Severe']

# To include all advisories:
IMPORTANT_SEVERITY = ['Extreme', 'Severe', 'Moderate', 'Minor']
```

### Coverage Area

Edit `weather_check.py` line 13:
```python
# Current: Wayne, Oakland, Macomb, Washtenaw counties
PARAMS = {
    'zone': 'MIZ075,MIZ076,MIZ082,MIZ083',
    'status': 'actual'
}

# For just Wayne County (Detroit):
PARAMS = {'zone': 'MIZ075', 'status': 'actual'}

# For all of Michigan:
PARAMS = {'area': 'MI', 'status': 'actual'}
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

**Note:** Cron times are in UTC. Detroit is UTC-5 (EST) or UTC-4 (EDT).

## 🔐 Secrets

The repository uses one GitHub secret:

- **`SLACK_WEBHOOK_URL`**: Webhook URL for posting to Slack #weather channel

### Updating the Webhook

If you need to regenerate the Slack webhook:

1. Go to https://api.slack.com/apps
2. Select "Weather Bot" app
3. Go to "Incoming Webhooks"
4. Delete old webhook, create new one for #weather channel
5. In GitHub repo: Settings → Secrets → Actions
6. Update `SLACK_WEBHOOK_URL` with new URL

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
Checking for weather alerts...
Tracking X previously posted alerts
No new important alerts found
```

**When there ARE NEW alerts:**
```
Checking for weather alerts...
Tracking X previously posted alerts
Found 1 NEW important alert(s)
Successfully sent alert to Slack
Marked 1 alert(s) as posted
```

**When alerts are active but already posted:**
```
Checking for weather alerts...
Tracking X previously posted alerts
No new important alerts found
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
5. Check if alerts exist at https://www.weather.gov/dtx/

### Getting alerts for wrong area

- Check `PARAMS` configuration in `weather_check.py`
- Verify zone codes match your desired coverage area

### Too many/few alerts

- Adjust `IMPORTANT_SEVERITY` list in `weather_check.py`
- Current setting includes Extreme, Severe, and Moderate

### Duplicate alerts posting

- Check that `posted_alerts.txt` exists in the repo
- Verify workflow has `permissions: contents: write`
- Check Actions logs to confirm tracking file is being updated
- View `posted_alerts.txt` to see tracked alert IDs

### Workflow fails with "exit code 128"

- GitHub Actions needs write permissions
- Verify workflow file has `permissions: contents: write` at the top

### `posted_alerts.txt` getting too large

- The script automatically cleans old entries (keeps last 100)
- File should stay under 10KB
- No manual cleanup needed

## 📊 Monitoring

### Check the Actions Tab Regularly

Ensure:
- Workflow is running on schedule (every hour)
- No errors in recent runs
- Python script is executing successfully
- Tracking file is being updated

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
- Tracking file cleans itself automatically

### Occasional Updates

- Update Python version in workflow if needed
- Adjust alert criteria based on feedback
- Modify coverage area if DRD moves practice locations
- Clean up very old alert IDs (automatically done, but can be manual)

### Resetting Alert Tracking

If you want to clear all tracked alerts (e.g., for testing):
1. Delete all contents of `posted_alerts.txt`
2. Commit the empty file
3. Next run will post any currently active alerts

## 📚 Resources

- [NWS API Documentation](https://www.weather.gov/documentation/services-web-api)
- [NWS Detroit Office](https://www.weather.gov/dtx/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)

## 📝 Alert Types Reference

**Common Alert Types:**
- 🚨 **Extreme**: Blizzard Warning, Ice Storm Warning, Tornado Warning
- ⛔ **Severe**: Winter Storm Warning, Severe Thunderstorm Warning (destructive), Flash Flood Warning (catastrophic)
- ⚠️ **Moderate**: Winter Weather Advisory, Wind Advisory, Flood Advisory

## 👥 Contact

**Maintained by:** Oi!
**Questions?** Post in #weather or DM the maintainer

## 📄 License

Internal use for Detroit Roller Derby only.

---

**Last Updated:** January 2026
