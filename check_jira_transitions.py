#!/usr/bin/env python3
"""
Check what transitions are available in your JIRA project.
This helps you customize the status mapping correctly.
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_jira_client():
    """Get JIRA client with current config"""
    try:
        from jira import JIRA
        
        base_url = os.getenv("JIRA_BASE_URL")
        username = os.getenv("JIRA_USERNAME")
        token = os.getenv("JIRA_TOKEN")
        
        if not all([base_url, username, token]):
            print("❌ Missing JIRA credentials in .env file")
            return None
        
        jira_opts = {"server": base_url}
        client = JIRA(options=jira_opts, basic_auth=(username, token))
        return client
    except Exception as e:
        print(f"❌ Failed to connect to JIRA: {e}")
        return None

def check_transitions():
    """Check available transitions in JIRA"""
    jira = get_jira_client()
    if not jira:
        return
    
    project_key = os.getenv("JIRA_PROJECT_KEY", "PROJ")
    
    print(f"\n{'='*80}")
    print(f"JIRA Transition Check for Project: {project_key}")
    print(f"{'='*80}\n")
    
    try:
        # Get all issues in the project
        issues = jira.search_issues(f'project = {project_key}', maxResults=1)
        
        if not issues:
            print(f"ℹ️  No issues found in project {project_key}")
            print(f"   Creating a test issue to check transitions...\n")
            
            # Create a test issue
            issue_dict = {
                "project": {"key": project_key},
                "summary": "[TEST] Transition Check - Please Delete",
                "description": "This is a test issue to check available transitions.",
                "issuetype": {"name": os.getenv("JIRA_ISSUE_TYPE", "Task")}
            }
            test_issue = jira.create_issue(fields=issue_dict)
            issue_key = test_issue.key
            print(f"✅ Created test issue: {issue_key}\n")
        else:
            issue_key = issues[0].key
            print(f"✅ Using existing issue: {issue_key}\n")
        
        # Get transitions for this issue
        issue = jira.issue(issue_key)
        transitions = jira.transitions(issue_key)
        
        print(f"Available Transitions for {issue_key}:")
        print(f"{'-'*80}")
        
        if transitions:
            for transition in transitions:
                trans_id = transition.get('id')
                trans_name = transition.get('name')
                print(f"  ID: {trans_id:3s} | Name: {trans_name}")
            
            print(f"\n{'='*80}")
            print(f"Recommended Status Mapping for your .env or system.py:")
            print(f"{'='*80}\n")
            print("Add this to your JIRA config (in system.py or .env):\n")
            
            # Generate suggested mapping
            mapping = {}
            trans_names = [t.get('name').lower() for t in transitions]
            
            # Smart mapping based on transition names
            status_to_jira = {
                "investigating": None,
                "identified": None,
                "resolving": None,
                "resolved": None,
                "closed": None
            }
            
            for status in status_to_jira.keys():
                # Try to find matching transition
                for trans in transitions:
                    trans_name = trans.get('name').lower()
                    if any(keyword in trans_name for keyword in [status.replace('_', ' '), status]):
                        status_to_jira[status] = trans.get('name')
                        break
                
                # Fallback mappings
                if status_to_jira[status] is None:
                    if status == "investigating":
                        status_to_jira[status] = next((t.get('name') for t in transitions 
                                                       if 'progress' in t.get('name', '').lower()), None)
                    elif status == "identified":
                        status_to_jira[status] = next((t.get('name') for t in transitions 
                                                       if 'todo' in t.get('name', '').lower() or 'backlog' in t.get('name', '').lower()), None)
                    elif status == "resolving":
                        status_to_jira[status] = next((t.get('name') for t in transitions 
                                                       if 'review' in t.get('name', '').lower() or 'progress' in t.get('name', '').lower()), None)
                    elif status in ["resolved", "closed"]:
                        status_to_jira[status] = next((t.get('name') for t in transitions 
                                                       if 'done' in t.get('name', '').lower() or 'closed' in t.get('name', '').lower()), None)
            
            print("jira_config = {")
            print(f'    "base_url": "{os.getenv("JIRA_BASE_URL")}",')
            print(f'    "username": "{os.getenv("JIRA_USERNAME")}",')
            print(f'    "token": "***",')
            print(f'    "project_key": "{project_key}",')
            print(f'    "issue_type": "{os.getenv("JIRA_ISSUE_TYPE", "Task")}",')
            print('    "status_map": {')
            
            for status, jira_transition in status_to_jira.items():
                if jira_transition:
                    print(f'        "{status}": "{jira_transition}",')
                else:
                    print(f'        "{status}": None,  # ⚠️  No suitable transition found')
            
            print('    }')
            print("}\n")
            
            # Clean up test issue if we created one
            if not issues:
                print(f"ℹ️  Cleaning up test issue {issue_key}...")
                try:
                    jira.delete_issue(issue_key)
                    print(f"✅ Test issue deleted\n")
                except:
                    print(f"⚠️  Could not delete test issue. You can delete {issue_key} manually.\n")
        else:
            print(f"⚠️  No transitions found for {issue_key}")
            print(f"   This might mean the issue is already in a terminal state.\n")
    
    except Exception as e:
        print(f"❌ Error checking transitions: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Verify JIRA_PROJECT_KEY is correct: {project_key}")
        print(f"  2. Verify you have permissions in the project")
        print(f"  3. Check that JIRA_BASE_URL, JIRA_USERNAME, and JIRA_TOKEN are correct")

if __name__ == "__main__":
    check_transitions()
