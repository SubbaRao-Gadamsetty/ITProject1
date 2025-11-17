#!/usr/bin/env python3
"""
Quick test script to verify JIRA integration is working correctly
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from it_incident_response.system import IncidentResponseSystem

def main():
    print("=" * 80)
    print(" JIRA Integration Test ".center(80, "="))
    print("=" * 80)
    print()

    # Check environment variables
    print("1. Checking JIRA Configuration from .env:")
    print("-" * 80)
    jira_config = {
        "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL"),
        "JIRA_USERNAME": os.getenv("JIRA_USERNAME"),
        "JIRA_TOKEN": os.getenv("JIRA_TOKEN", "***hidden***")[:10] + "..." if os.getenv("JIRA_TOKEN") else None,
        "JIRA_PROJECT_KEY": os.getenv("JIRA_PROJECT_KEY"),
        "JIRA_ISSUE_TYPE": os.getenv("JIRA_ISSUE_TYPE"),
    }
    
    print(json.dumps(jira_config, indent=2))
    print()

    # Validate configuration
    print("2. Validating JIRA Configuration:")
    print("-" * 80)
    
    required_fields = ["JIRA_BASE_URL", "JIRA_USERNAME", "JIRA_TOKEN"]
    missing_fields = [field for field in required_fields if not os.getenv(field)]
    
    if missing_fields:
        print(f"❌ MISSING REQUIRED FIELDS: {', '.join(missing_fields)}")
        print("   JIRA will run in SIMULATED MODE (no real JIRA issues will be created)")
        print()
    else:
        print("✅ All required JIRA fields are configured")
        print()

    # Initialize system
    print("3. Initializing IT Incident Response System:")
    print("-" * 80)
    try:
        system = IncidentResponseSystem(preload_incidents=False)
        print("✅ System initialized successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return

    # Check MCP tools
    print("4. Checking Registered MCP Tools:")
    print("-" * 80)
    available_tools = system.mcp_host.get_available_tools(system.coordinator.mcp_session_id)
    for tool in available_tools:
        print(f"  - {tool['name']} ({tool['tool_id']}): {tool['description']}")
    print()

    # Create an incident and verify ticket creation with JIRA integration
    print("5. Creating Test Incident (This will trigger JIRA ticket creation):")
    print("-" * 80)
    try:
        incident_id = system.create_incident(
            title="Test Database Connection Issue",
            description="This is a test incident to verify JIRA integration",
            severity="high",
            affected_systems=["test-server-01"],
            tags=["test", "jira-integration"]
        )
        print(f"✅ Incident created with ID: {incident_id}")
        print()

        # Get incident details
        incident = system.get_incident_status(incident_id)
        print("6. Incident Details (including JIRA issue key if created):")
        print("-" * 80)
        print(json.dumps(incident, indent=2))
        print()

        # Check if JIRA issue key was created
        if "jira_issue_key" in incident:
            print(f"✅ JIRA Issue Created: {incident['jira_issue_key']}")
        else:
            print("⚠️  No JIRA issue key in ticket (may be running in simulated mode)")
        
        print()
        print("=" * 80)
        print(" Test Completed Successfully ".center(80, "="))
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
