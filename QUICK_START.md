# JIRA Integration - Quick Start Guide

## 1. Setup JIRA Configuration

Create a `.env` file in the project root with your JIRA credentials:

```bash
# .env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_TOKEN=your-api-token
JIRA_PROJECT_KEY=KAN
JIRA_ISSUE_TYPE=Task
```

### How to Get These Values

| Variable | Where to Find | Notes |
|----------|---------------|-------|
| `JIRA_BASE_URL` | Your Jira Cloud URL | e.g., `https://subbarao-g.atlassian.net` |
| `JIRA_USERNAME` | Your Atlassian account email | No spaces, no trailing spaces |
| `JIRA_TOKEN` | https://id.atlassian.com/manage-profile/security/api-tokens | Create new API token |
| `JIRA_PROJECT_KEY` | Project Settings → Details → Key field | Short code like `KAN`, not full project name |
| `JIRA_ISSUE_TYPE` | Project Settings → Issue Types | Usually `Task`, `Bug`, `Story` etc |

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `python-dotenv` - Load `.env` file
- `jira` - JIRA API client library

## 3. Run the Demo

```bash
python run_demo.py
```

You should see output like:
```
2025-11-14 08:28:54 [INFO] JIRA issue created for incident 79f4fd01-...: KAN-5
2025-11-14 08:28:54 [INFO] Persisted JIRA issue URL: https://subbarao-g.atlassian.net/browse/KAN-5
```

## 4. Verify JIRA Issue Was Created

Click the JIRA URL in the demo output to open your issue in a browser.

You should see:
- ✅ Issue Key: `KAN-5` (or similar)
- ✅ Summary: Matches the incident title
- ✅ Description: Includes incident details
- ✅ Workflow transitions applied as incident progresses

## How It Works

### Automatic Ticket Creation
```
Incident Created → Ticket Created → JIRA Issue Created → URL Persisted
```

### Lifecycle Tracking
```
investigating → In Progress (JIRA)
identified   → To Do (JIRA)
resolving    → In Review (JIRA)
resolved     → Done (JIRA)
```

## Common Issues

### "valid project is required"
- ❌ Using project **name** instead of project **key**
- ✅ Use short code: `KAN` not `Knowledge and Automation`

### "Invalid username or password"
- ❌ Using password instead of API token
- ✅ Create token: https://id.atlassian.com/manage-profile/security/api-tokens

### Issues show as `SIM-XXXXX`
- ❌ JIRA credentials not set or invalid
- ✅ Check `.env` file exists and is complete
- ✅ Run: `python verify_jira.py` to see config

## Files Modified

### Core Implementation
- `it_incident_response/tools/ticketing.py` - JIRA integration
- `it_incident_response/system.py` - Load JIRA config
- `it_incident_response/agents/coordinator.py` - Persist JIRA metadata
- `it_incident_response/models/incident.py` - Metadata storage

### Configuration
- `requirements.txt` - Added `python-dotenv`, `jira`
- `.env` - JIRA credentials (create this file)
- `run_demo.py` - Load `.env` on startup

### Documentation
- `JIRA_INTEGRATION_REPORT.md` - Full technical report
- `QUICK_START.md` - This file

## Next Steps

1. ✅ Copy `.env` template to `.env`
2. ✅ Fill in your JIRA credentials
3. ✅ Run `python run_demo.py`
4. ✅ Click the JIRA URL to verify issue was created
5. ✅ Watch as incident progresses and JIRA issue transitions

## Support

See `JIRA_INTEGRATION_REPORT.md` for:
- Detailed architecture
- Code examples
- Error handling & resilience
- Troubleshooting guide
- Future enhancement ideas
