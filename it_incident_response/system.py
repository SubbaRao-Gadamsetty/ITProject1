# it_incident_response/system.py
import logging
import uuid
import os
from typing import Dict, List, Any, Optional

from it_incident_response.protocols.a2a import A2AMessage, PartType
from it_incident_response.protocols.mcp import MCPHost
from it_incident_response.agents.coordinator import IncidentCoordinatorAgent
from it_incident_response.agents.diagnostic import DiagnosticAgent
from it_incident_response.agents.resolution import ResolutionAgent
from it_incident_response.tools.log_analyzer import LogAnalyzerTool
from it_incident_response.tools.system_monitor import SystemMonitorTool
from it_incident_response.tools.knowledge_base import KnowledgeBaseTool
from it_incident_response.tools.ticketing import TicketingSystemTool
from it_incident_response.tools.deployment import DeploymentSystemTool
from it_incident_response.tools.alert import AlertSystemTool
from it_incident_response.models.incident import (
    load_simulated_incidents, get_incident_by_id, get_all_incidents
)

logger = logging.getLogger("it-incident-response.system")

class IncidentResponseSystem:
    """Main class for the IT Incident Response System"""

    def __init__(self, preload_incidents: bool = True):
        """
        Initialize the Incident Response System

        Args:
            preload_incidents: Whether to preload simulated incidents
        """
        # Initialize MCP Host
        self.mcp_host = MCPHost()
        self._register_mcp_tools()

        # Initialize Agents
        self.coordinator = IncidentCoordinatorAgent(self.mcp_host)
        self.diagnostic_agent = DiagnosticAgent(self.mcp_host)
        self.resolution_agent = ResolutionAgent(self.mcp_host)

        # Set up agent collaboration
        self.coordinator.set_collaborating_agents(
            self.diagnostic_agent.agent_card.agent_id,
            self.resolution_agent.agent_card.agent_id
        )

        logger.info("IT Incident Response System initialized")

        # Preload incidents if requested
        if preload_incidents:
            self.preload_incidents()

    def _register_mcp_tools(self):
        """Register all MCP tools"""
        self.mcp_host.register_tool(LogAnalyzerTool())
        self.mcp_host.register_tool(SystemMonitorTool())
        self.mcp_host.register_tool(KnowledgeBaseTool())
        
        # Load JIRA configuration from environment variables (optional)
        jira_config = self._load_jira_config()
        
        # pass the MCP host to the ticketing tool so it can register related
        # tools (for example, a per-ticket JIRA integration) at runtime
        self.mcp_host.register_tool(TicketingSystemTool(self.mcp_host, jira_config=jira_config))
        self.mcp_host.register_tool(DeploymentSystemTool())
        self.mcp_host.register_tool(AlertSystemTool())

    def _load_jira_config(self) -> Optional[Dict[str, str]]:
        """
        Load JIRA configuration from environment variables.
        
        Expected environment variables:
            - JIRA_BASE_URL: Base URL of your JIRA instance (e.g., https://jira.example.com)
            - JIRA_USERNAME: JIRA username or email
            - JIRA_TOKEN: API token or password
            - JIRA_PROJECT_KEY: (Optional) JIRA project key (default: PROJ)
            - JIRA_ISSUE_TYPE: (Optional) Issue type (default: Task)
        
        Returns:
            Dictionary with JIRA config if all required env vars are set, None otherwise
        """
        base_url = os.getenv("JIRA_BASE_URL")
        username = os.getenv("JIRA_USERNAME")
        token = os.getenv("JIRA_TOKEN")
        
        # Only return config if all required fields are provided
        if base_url and username and token:
            return {
                "base_url": base_url,
                "username": username,
                "token": token,
                "project_key": os.getenv("JIRA_PROJECT_KEY", "PROJ"),
                "issue_type": os.getenv("JIRA_ISSUE_TYPE", "Task"),
                # Status mapping: incident status -> JIRA workflow transition
                # Customize this based on your JIRA project's workflow
                # Run check_jira_transitions.py to see available transitions
                "status_map": {
                    "investigating": "In Progress",    # Start investigation
                    "identified": "To Do",              # Move back to backlog if waiting
                    "resolving": "In Progress",         # Resolution is in progress
                    "resolved": "Done",                 # Issue resolved
                    "closed": "Done",                   # Ticket closed
                }
            }
        
        # If no env vars set, JIRA integration will use simulated mode
        if any([base_url, username, token]):
            logger.warning(
                "Incomplete JIRA configuration detected. Set all of: "
                "JIRA_BASE_URL, JIRA_USERNAME, JIRA_TOKEN. "
                "Falling back to simulated JIRA mode."
            )
        else:
            logger.info("JIRA integration not configured (no env vars). Using simulated mode.")
        
        return None

    def preload_incidents(self, count: int = 3) -> List[str]:
        """
        Preload simulated incidents

        Args:
            count: Number of incidents to preload

        Returns:
            List of incident IDs
        """
        logger.info(f"Preloading {count} simulated incidents")
        return load_simulated_incidents(count)

    def create_incident(self, title: str, description: str, severity: str,
                        affected_systems: List[str], tags: List[str] = None) -> str:
        """
        Create a new incident in the system

        Args:
            title: Incident title
            description: Incident description
            severity: Incident severity (low, medium, high, critical)
            affected_systems: List of affected systems
            tags: Tags for categorization

        Returns:
            Incident ID
        """
        # Create a message to the coordinator agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the create_incident request
        message.add_json_part({
            "create_incident": {
                "title": title,
                "description": description,
                "severity": severity,
                "affected_systems": affected_systems,
                "tags": tags or []
            }
        })

        # Create a task with the coordinator
        task_id = self.coordinator.create_task(message)

        # Process the task
        task = self.coordinator.tasks[task_id]
        self.coordinator._process_message(task, message)

        # Extract the incident ID from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        incident_data = part.content.get("incident", {})
                        return incident_data.get("incident_id")

        return None

    def analyze_incident(self, incident_id: str) -> Dict[str, Any]:
        """
        Analyze an incident using the diagnostic agent

        Args:
            incident_id: ID of the incident to analyze

        Returns:
            Diagnostic report
        """
        # Create a message to the diagnostic agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the analyze_incident request
        message.add_json_part({
            "analyze_incident": {
                "incident_id": incident_id
            }
        })

        # Create a task with the diagnostic agent
        task_id = self.diagnostic_agent.create_task(message)

        # Process the task
        task = self.diagnostic_agent.tasks[task_id]
        self.diagnostic_agent._process_message(task, message)

        # Extract the diagnostic report from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("diagnostic_report", {})

        return {}

    def implement_resolution(self, incident_id: str) -> Dict[str, Any]:
        """
        Implement a resolution using the resolution agent

        Args:
            incident_id: ID of the incident to resolve

        Returns:
            Resolution status
        """
        # Create a message to the resolution agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the implement_resolution request
        message.add_json_part({
            "implement_resolution": {
                "incident_id": incident_id
            }
        })

        # Create a task with the resolution agent
        task_id = self.resolution_agent.create_task(message)

        # Process the task
        task = self.resolution_agent.tasks[task_id]
        self.resolution_agent._process_message(task, message)

        # Extract the resolution status from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("resolution_status", {})

        return {}

    def update_incident_status(self, incident_id: str, status: str, notes: str = None, remediation_steps: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update an incident status

        Args:
            incident_id: ID of the incident to update
            status: New status (investigating, identified, resolving, resolved, closed)
            notes: Additional notes
            remediation_steps: List of remediation actions taken (for tracking in JIRA)

        Returns:
            Updated incident
        """
        # Create a message to the coordinator agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the update_incident request
        request_data = {
            "incident_id": incident_id,
            "status": status
        }

        if notes:
            request_data["notes"] = notes
        
        if remediation_steps:
            request_data["remediation_steps"] = remediation_steps

        message.add_json_part({
            "update_incident": request_data
        })

        # Create a task with the coordinator
        task_id = self.coordinator.create_task(message)

        # Process the task
        task = self.coordinator.tasks[task_id]
        self.coordinator._process_message(task, message)

        # Extract the updated incident from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("incident", {})

        return {}

    def get_incident_status(self, incident_id: str) -> Dict[str, Any]:
        """
        Get the current status of an incident

        Args:
            incident_id: ID of the incident

        Returns:
            Incident details
        """
        # Create a message to the coordinator agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the get_incident_status request
        message.add_json_part({
            "get_incident_status": {
                "incident_id": incident_id
            }
        })

        # Create a task with the coordinator
        task_id = self.coordinator.create_task(message)

        # Process the task
        task = self.coordinator.tasks[task_id]
        self.coordinator._process_message(task, message)

        # Extract the incident from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("incident", {})

        return {}

    def get_diagnostic_report(self, incident_id: str) -> Dict[str, Any]:
        """
        Get the diagnostic report for an incident

        Args:
            incident_id: ID of the incident

        Returns:
            Diagnostic report
        """
        # Create a message to the diagnostic agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the get_diagnostic_report request
        message.add_json_part({
            "get_diagnostic_report": {
                "incident_id": incident_id
            }
        })

        # Create a task with the diagnostic agent
        task_id = self.diagnostic_agent.create_task(message)

        # Process the task
        task = self.diagnostic_agent.tasks[task_id]
        self.diagnostic_agent._process_message(task, message)

        # Extract the diagnostic report from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("diagnostic_report", {})

        return {}

    def get_resolution_status(self, incident_id: str) -> Dict[str, Any]:
        """
        Get the resolution status for an incident

        Args:
            incident_id: ID of the incident

        Returns:
            Resolution status
        """
        # Create a message to the resolution agent
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            role="user"
        )

        # Add JSON part with the get_resolution_status request
        message.add_json_part({
            "get_resolution_status": {
                "incident_id": incident_id
            }
        })

        # Create a task with the resolution agent
        task_id = self.resolution_agent.create_task(message)

        # Process the task
        task = self.resolution_agent.tasks[task_id]
        self.resolution_agent._process_message(task, message)

        # Extract the resolution status from the response
        for msg in task.messages:
            if msg.role == "agent":
                for part in msg.parts:
                    if part.content_type == PartType.JSON:
                        return part.content.get("resolution_status", {})

        return {}

    def list_incidents(self) -> List[Dict[str, Any]]:
        """
        List all incidents in the system

        Returns:
            List of incidents
        """
        return get_all_incidents()

    def cleanup(self):
        """Clean up resources used by the system"""
        # End agent MCP sessions
        self.coordinator.cleanup()
        self.diagnostic_agent.cleanup()
        self.resolution_agent.cleanup()
        logger.info("IT Incident Response System cleaned up")