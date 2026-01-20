# Detroit Roller Derby - Weather Alerts

Automated weather alert system that monitors National Weather Service alerts for the Detroit metro area and posts them to the DRD Slack #weather channel.

## 🌤️ What This Does

- Checks NWS API every hour for active weather alerts
- Filters for severe/important alerts only (Extreme, Severe, Moderate)
- Posts formatted alerts to Slack #weather channel
- Monitors Wayne, Oakland, Macomb, and Washtenaw counties
- Runs completely free on GitHub Actions

## 🚀 How It Works

1. **GitHub Actions** runs on a schedule (every hour at :05 past the hour)
2. **Python script** (`weather_check.py`) fetches alerts from NWS API
3. **Filters** alerts by severity and location
4. **Posts** to Slack via webhook when alerts are found
5. **Logs** results in GitHub Actions for debugging

## 📁 Repository Structure
```
drd-weather-alerts/
├── .github/
│   └── workflows/
│       └── weather-check.yml    # GitHub Actions workflow configuration
├── weather_check.py              # Main Python script
└── README.md                     # This file
```

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
No important alerts found
```

**When there ARE alerts:**
```
Checking for weather alerts...
Found 2 important alert(s)
Successfully sent alert to Slack
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

### Getting alerts for wrong area

- Check `PARAMS` configuration in `weather_check.py`
- Verify zone codes match your desired coverage area

### Too many/few alerts

- Adjust `IMPORTANT_SEVERITY` list in `weather_check.py`
- Current setting includes Extreme, Severe, and Moderate

### Alerts posting at wrong time

- Remember cron times are UTC, not Eastern time
- 5 PM Eastern = 10 PM UTC (EST) or 9 PM UTC (EDT)

## 📊 Monitoring

Check the **Actions** tab regularly to ensure:
- Workflow is running on schedule (every hour)
- No errors in recent runs
- Python script is executing successfully

Green checkmarks = all good ✅  
Red X marks = needs attention ❌

## 🔄 Maintenance

### Regular Maintenance

- **None required!** This runs automatically

### Occasional Updates

- Update Python version in workflow if needed
- Adjust alert criteria based on feedback
- Modify coverage area if DRD moves practice locations

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

**Maintained by:** [Your Name]  
**Questions?** Post in #weather or DM the maintainer

## 📄 License

Internal use for Detroit Roller Derby only.

---

**Last Updated:** January 2026
