#!/usr/bin/env python3
"""
Verify JIRA integration by checking the last created incident.
"""
import json
from it_incident_response.models.incident import get_all_incidents

incidents = get_all_incidents()
if incidents:
    # Get the most recently created incident
    latest = max(incidents, key=lambda x: x.created_at)
    incident_dict = latest.to_dict()
    
    print("\n" + "="*80)
    print("JIRA INTEGRATION VERIFICATION")
    print("="*80 + "\n")
    
    print(f"Incident ID: {incident_dict.get('incident_id')}")
    print(f"Title: {incident_dict.get('title')}")
    print(f"Status: {incident_dict.get('status')}")
    print(f"\nJIRA Integration Details:")
    print(f"  - JIRA Issue Key: {incident_dict.get('metadata', {}).get('jira_issue_key', 'N/A')}")
    print(f"  - JIRA Issue URL: {incident_dict.get('metadata', {}).get('jira_issue_url', 'N/A')}")
    
    print(f"\nFull Incident JSON (metadata section):")
    print(json.dumps(incident_dict.get('metadata', {}), indent=2))
    
    print("\n" + "="*80)
else:
    print("No incidents found.")
