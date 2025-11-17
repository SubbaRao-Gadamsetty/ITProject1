# JIRA Workflow Lifecycle Integration - Complete Guide

## Overview

Your incident response system now **automatically transitions JIRA issues through workflow states** as incidents progress through their lifecycle.

## What's Happening Now

### Workflow States

Your JIRA project has these 3 workflow states:

```
To Do  →  In Progress  →  Done
  ↑                        ↓
  └────────────────────────┘
```

### Incident Status Mapping

When your incident changes status, the JIRA issue automatically transitions:

| Incident Status | JIRA Transition | JIRA ID | When Used |
|---|---|---|---|
| `investigating` | **In Progress** | 21 | Initial analysis phase |
| `identified` | **To Do** | 11 | Root cause found, ready for resolution |
| `resolving` | **In Progress** | 21 | Actively implementing fix |
| `resolved` | **Done** | 31 | Fix completed and verified |
| `closed` | **Done** | 31 | Ticket closed |

## How It Works

### 1. Issue Creation
```
Incident Created
    ↓
JIRA Issue Created (KAN-8)
    ↓
Status: To Do (default)
```

### 2. Status Update Flow
```
"investigating" status
    ↓
Call: transition_issue(KAN-8, "In Progress")
    ↓
JIRA workflow applies: To Do → In Progress
    ↓
Add comment: "Incident status changed to: investigating"
```

### 3. Example Flow Through Full Lifecycle

**Demo Run Log:**

```
08:37:26  → Incident created: "investigating"
           JIRA: To Do (default)

08:37:34  → Status update: "identified"
           📋 Updating JIRA issue KAN-8: 
              'identified' → transition to 'To Do'
           ✓ Transitioned KAN-8 to 'To Do' (ID: 11)
           + Added comment with diagnostic analysis

08:37:36  → Status update: "resolving"
           📋 Updating JIRA issue KAN-8:
              'resolving' → transition to 'In Progress'
           ✓ Transitioned KAN-8 to 'In Progress' (ID: 21)

08:37:48  → Status update: "resolved"
           (would transition to "Done" if called)
           + Added comments and created subtasks
```

## Configuration

### Located in: `system.py`

```python
"status_map": {
    "investigating": "In Progress",    # Start investigation
    "identified": "To Do",              # Move back to backlog if waiting
    "resolving": "In Progress",         # Resolution is in progress
    "resolved": "Done",                 # Issue resolved
    "closed": "Done",                   # Ticket closed
}
```

### How to Customize for Your JIRA Workflow

1. **Check your JIRA transitions:**
   ```bash
   python check_jira_transitions.py
   ```

2. **Output shows available transitions:**
   ```
   Available Transitions for KAN-8:
   ID: 11  | Name: To Do
   ID: 21  | Name: In Progress
   ID: 31  | Name: Done
   ```

3. **Update `system.py` if needed:**
   ```python
   # Change the mapping to match your workflow
   "status_map": {
       "investigating": "In Progress",
       "identified": "Review",  # if your workflow has this
       "resolving": "In Progress",
       "resolved": "Done",
       "closed": "Done",
   }
   ```

## Log Output Explained

### Transition Initiated
```
📋 Updating JIRA issue KAN-8: incident status changed to 'identified' → transition to 'To Do'
```
- 📋 indicates a JIRA update is happening
- Shows which issue is being updated
- Shows incident status and target JIRA transition

### Transition Successful
```
✓ Transitioned KAN-8 to 'To Do' (ID: 11)
✓ JIRA transition successful for KAN-8
```
- ✓ indicates success
- Shows the JIRA workflow state reached
- Shows the workflow ID used

### Notes Added
```
📝 Adding 1 note(s) to JIRA issue KAN-8
```
- 📝 indicates comments are being added
- Shows diagnostic analysis and status change comments

### Subtasks Created
```
✓ Creating 6 subtask(s) for JIRA issue KAN-8
```
- ✓ indicates remediation steps are being created as subtasks
- Allows tracking individual action items in JIRA

## Error Handling

### When Transition Fails

Example error if transition name doesn't match:
```
⚠ JIRA transition failed: Transition 'In Review' not found. 
Available: ['To Do', 'In Progress', 'Done']
```

**What to do:**
1. Run `python check_jira_transitions.py` to see available transitions
2. Update `status_map` in `system.py` with correct transition names
3. Re-run demo

### When JIRA is Unavailable

- System logs the error but continues
- Creates simulated issue key `SIM-XXXXXXXX`
- Incident response continues normally

## Key Features

✅ **Automatic Transitions** - Status changes automatically move JIRA issues
✅ **Real-time Comments** - Diagnostic reports added as JIRA comments
✅ **Subtask Creation** - Remediation steps become JIRA subtasks
✅ **Attachment Support** - Diagnostic files attached to JIRA issues
✅ **Error Recovery** - Falls back gracefully if JIRA unavailable
✅ **Full Logging** - Detailed logs show all transitions and activities

## Viewing in JIRA

### To See Transitions in JIRA:

1. Open the JIRA issue in browser
2. Look at the **Activity** section (bottom of issue)
3. You'll see:
   - Workflow transitions (e.g., "Status: To Do → In Progress")
   - Comments added by incident system
   - Subtasks created for remediation
   - Attachments linked

Example Activity Log:
```
[System Bot] Transitioned issue to In Progress
[System Bot] Incident status changed to: investigating
[System Bot] Added diagnostic analysis comment
[System Bot] Created subtask: Monitor system for additional error patterns
```

## Workflow Diagram

```
Incident Lifecycle              JIRA Workflow
─────────────────────────────   ────────────────

created (investigating)     →    To Do (default)
                                    ↓
analysis complete (identified) →   To Do (state 11)
                                    ↓
implementation (resolving)  →    In Progress (state 21)
                                    ↓
completed (resolved)        →       Done (state 31)
                                    ↓
closed                      →       Done (state 31)
```

## Complete Example: What Happens During Demo

```
TIME:08:37:26  Create Incident
└─ Incident: "investigating"
└─ JIRA KAN-8: Created (status: To Do)

TIME:08:37:34  Diagnostic Analysis Complete
└─ Update status: "identified"
└─ JIRA Transition: To Do (call transition_issue with "To Do")
└─ JIRA KAN-8: Status changed to To Do
└─ Add Comment: "Diagnostic analysis completed..."

TIME:08:37:36  Start Resolution
└─ Update status: "resolving"
└─ JIRA Transition: In Progress (call transition_issue with "In Progress")
└─ JIRA KAN-8: Status changed to In Progress
└─ Add Comment: "Incident status changed to: resolving"

TIME:08:37:48  Resolution Complete
└─ Update status: "resolved"
└─ Create Subtasks: 6 remediation actions
└─ JIRA KAN-8: Would transition to Done (if called)
└─ Add Comments: "Resolution implemented..."
```

## Customizing for Different Workflows

### Example: DevOps/SRE Workflow

Your JIRA might have different states:

```python
"status_map": {
    "investigating": "In Investigation",
    "identified": "Identified / Awaiting Resolution",
    "resolving": "In Resolution",
    "resolved": "Resolved / Verifying",
    "closed": "Closed",
}
```

### Steps to Customize:

1. **Check your transitions:**
   ```bash
   python check_jira_transitions.py
   ```

2. **Copy the suggested mapping** from the output

3. **Paste into `system.py`:**
   ```python
   def _load_jira_config(self):
       ...
       return {
           "status_map": {
               # Paste here
           }
       }
   ```

4. **Test with demo:**
   ```bash
   python run_demo.py
   ```

## Troubleshooting

### Issue: "To Do" state in JIRA but not seeing updates

1. Check the JIRA issue Activity/History tab
2. Verify `.env` has correct credentials
3. Check logs for transition errors:
   ```bash
   python run_demo.py 2>&1 | grep "transition"
   ```

### Issue: Wrong transitions being applied

1. Run `check_jira_transitions.py` to verify available transitions
2. Update `status_map` in `system.py`
3. Make sure transition names exactly match JIRA workflow

### Issue: "Transition not found" error

1. The transition name in `status_map` doesn't match JIRA
2. Run `check_jira_transitions.py`
3. Copy exact transition names from output
4. Update `status_map` with correct names

## Summary

Your JIRA workflow is now **fully integrated** with incident lifecycle:

✅ Issues created automatically when tickets raised
✅ Status changes transition JIRA issues through workflow
✅ Comments track diagnostic analysis and updates
✅ Subtasks created for remediation actions
✅ Full audit trail in JIRA activity log
✅ Customizable status mapping for any workflow

The flow is: **Incident Status Change** → **JIRA Transition** → **JIRA Workflow State Updated**

This ensures JIRA is always kept in sync with the incident status!
