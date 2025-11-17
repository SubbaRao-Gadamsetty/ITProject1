# JIRA Workflow Lifecycle - Quick Reference

## 🎯 The Problem You Had

When incident status changes, JIRA issue was staying in "To Do" state instead of transitioning through the workflow.

## ✅ The Solution

We implemented a proper **status mapping** that transitions JIRA issues through workflow states as incidents progress.

## 📊 Current Status Mapping

```
INCIDENT STATUS          JIRA WORKFLOW STATE        JIRA ID
─────────────────────────────────────────────────────────────
investigating    ────→    In Progress                  21
identified       ────→    To Do                        11
resolving        ────→    In Progress                  21
resolved         ────→    Done                         31
closed           ────→    Done                         31
```

## 🔄 Workflow Flow

```
┌─────────────────────────────────────────────────────────┐
│                  INCIDENT LIFECYCLE                     │
└─────────────────────────────────────────────────────────┘
    
    investigating
         ↓
    ┌─────────────────────────────────┐
    │  JIRA: "In Progress" (ID: 21)   │
    └─────────────────────────────────┘
         ↓
    identified
         ↓
    ┌─────────────────────────────────┐
    │  JIRA: "To Do" (ID: 11)         │
    └─────────────────────────────────┘
         ↓
    resolving
         ↓
    ┌─────────────────────────────────┐
    │  JIRA: "In Progress" (ID: 21)   │
    └─────────────────────────────────┘
         ↓
    resolved
         ↓
    ┌─────────────────────────────────┐
    │  JIRA: "Done" (ID: 31)          │
    └─────────────────────────────────┘
         ↓
    closed
         ↓
    ┌─────────────────────────────────┐
    │  JIRA: "Done" (ID: 31)          │
    └─────────────────────────────────┘
```

## 📋 What Happens During Transitions

### Step 1: Check Available Transitions
```python
transitions = jira_client.transitions(issue_key)
# Output: [
#   {'id': '11', 'name': 'To Do'},
#   {'id': '21', 'name': 'In Progress'},
#   {'id': '31', 'name': 'Done'}
# ]
```

### Step 2: Map Incident Status
```python
status_map = {
    "investigating": "In Progress",
    "identified": "To Do",
    "resolving": "In Progress",
    "resolved": "Done",
    "closed": "Done"
}
target_transition = status_map.get("investigating")  # "In Progress"
```

### Step 3: Execute Transition
```python
# Find the transition ID
transition_id = next(t['id'] for t in transitions if t['name'] == "In Progress")  # '21'

# Apply the transition
jira_client.transition_issue(issue_key, transition=transition_id)

# Add comment
jira_client.add_comment(issue_key, "Incident status changed to: investigating")
```

## 🎬 Demo Output

The demo clearly shows transitions happening:

```
📋 Updating JIRA issue KAN-8: incident status changed to 'identified' → transition to 'To Do'
✓ Transitioned KAN-8 to 'To Do' (ID: 11)
✓ JIRA transition successful for KAN-8
📝 Adding 1 note(s) to JIRA issue KAN-8

📋 Updating JIRA issue KAN-8: incident status changed to 'resolving' → transition to 'In Progress'
✓ Transitioned KAN-8 to 'In Progress' (ID: 21)
✓ JIRA transition successful for KAN-8
```

## 🔧 Customizing the Mapping

### 1. Check Your JIRA Transitions
```bash
python check_jira_transitions.py
```

### 2. Get the Output
```
Available Transitions for KAN-8:
  ID: 11  | Name: To Do
  ID: 21  | Name: In Progress
  ID: 31  | Name: Done
```

### 3. Update in `system.py`
```python
"status_map": {
    "investigating": "In Progress",
    "identified": "To Do",
    "resolving": "In Progress",
    "resolved": "Done",
    "closed": "Done",
}
```

### 4. Test
```bash
python run_demo.py
```

## 📁 Key Files

| File | Purpose |
|---|---|
| `it_incident_response/tools/ticketing.py` | Implements JIRA transitions |
| `it_incident_response/system.py` | Contains status_map configuration |
| `check_jira_transitions.py` | Tool to check available transitions |
| `JIRA_WORKFLOW_LIFECYCLE.md` | Detailed documentation |

## 🚀 How to Use

### For Your Project with KAN Workflow

Your workflow is set up correctly! Just run:

```bash
python run_demo.py
```

And watch the JIRA issues transition automatically:
- **To Do** ← **In Progress** ← **Done**

### For Different Workflows

1. Run `check_jira_transitions.py`
2. Copy the workflow state names
3. Update `status_map` in `system.py`
4. Done!

## ❓ FAQ

**Q: Why doesn't it show "Resolved" in JIRA?**
A: "Resolved" doesn't exist in standard JIRA workflows. It's mapped to "Done". You can customize this in `status_map`.

**Q: Can I add more statuses?**
A: Yes! Just add them to `status_map`:
```python
"status_map": {
    "investigating": "In Progress",
    "identified": "To Do",
    "analyzing": "In Progress",  # New status
    "resolving": "In Progress",
    "resolved": "Done",
    "closed": "Done",
}
```

**Q: What if transition doesn't exist?**
A: You'll see an error log:
```
⚠ JIRA transition failed: Transition 'In Review' not found. 
Available: ['To Do', 'In Progress', 'Done']
```

Run `check_jira_transitions.py` to fix it.

## 📖 Related Docs

- `JIRA_INTEGRATION_REPORT.md` - Full technical documentation
- `JIRA_WORKFLOW_LIFECYCLE.md` - Complete workflow guide
- `QUICK_START.md` - Getting started guide

---

**Status:** ✅ IMPLEMENTED AND TESTED

Your JIRA workflow integration is working perfectly! Issues now automatically transition through your workflow as incidents progress.
