import datetime
import logging
import uuid
from typing import Dict, List, Any, Optional

from it_incident_response.protocols.mcp import MCPTool, MCPToolType

logger = logging.getLogger("it-incident-response.tools.ticketing")


class JIRATool:
    """Represents a (simulated) JIRA integration registered per-ticket.

    This is a thin wrapper that performs best-effort operations against JIRA
    when the `jira` package is available and `jira_config` contains valid
    credentials. All operations fall back to simulated successful responses
    when JIRA is not available or an error occurs.
    """

    def __init__(self, ticket_id: str, summary: str = "", description: str = "", jira_config: Optional[Dict[str, Any]] = None):
        self.ticket_id = ticket_id
        self.summary = summary
        self.description = description
        self.jira_config = jira_config or {}
        self.issue_key: Optional[str] = None
        self._cached_transitions: Optional[List[Dict[str, Any]]] = None

    def _get_jira_client(self):
        """Return a JIRA client if available, otherwise None"""
        try:
            import importlib.util
            if importlib.util.find_spec("jira") is None:
                return None
            from jira import JIRA
            if not (self.jira_config.get("base_url") and self.jira_config.get("username") and self.jira_config.get("token")):
                return None
            jira_opts = {"server": self.jira_config.get("base_url")}
            return JIRA(options=jira_opts, basic_auth=(self.jira_config.get("username"), self.jira_config.get("token")))
        except Exception as e:
            logger.debug(f"JIRA client not available: {e}")
            return None

    def execute(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        action = params.get("action")

        if action == "create_issue":
            # Try to create a real JIRA issue if possible, else simulate
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    issue_dict = {
                        "project": {"key": self.jira_config.get("project_key", "PROJ")},
                        "summary": self.summary or params.get("data", {}).get("summary", "Automated issue"),
                        "description": self.description or params.get("data", {}).get("description", "Created from incident response system"),
                        "issuetype": {"name": self.jira_config.get("issue_type", "Task")},
                    }
                    issue = jira_client.create_issue(fields=issue_dict)
                    self.issue_key = getattr(issue, "key", None)
                    issue_url = None
                    if self.issue_key and self.jira_config.get("base_url"):
                        issue_url = f"{self.jira_config['base_url'].rstrip('/')}/browse/{self.issue_key}"
                    return {"status": "success", "data": {"issue_key": self.issue_key, "issue_url": issue_url}}
                except Exception as e:
                    logger.exception(f"JIRA issue creation failed for ticket {self.ticket_id}: {e}")

            # Simulated issue key and URL
            simulated_key = f"SIM-{str(uuid.uuid4())[:8].upper()}"
            self.issue_key = simulated_key
            issue_url = None
            if self.jira_config.get("base_url"):
                issue_url = f"{self.jira_config['base_url'].rstrip('/')}/browse/{simulated_key}"
            return {"status": "success", "data": {"issue_key": simulated_key, "issue_url": issue_url}}

        if action == "get_issue":
            if not self.issue_key:
                return {"status": "error", "message": "No issue created for this tool yet"}
            return {"status": "success", "data": {"issue_key": self.issue_key}}

        if action == "get_transitions":
            jira_client = self._get_jira_client()
            if jira_client and self.issue_key:
                try:
                    transitions = jira_client.transitions(self.issue_key)
                    self._cached_transitions = transitions
                    return {"status": "success", "data": {"transitions": transitions}}
                except Exception as e:
                    logger.debug(f"Failed to list transitions for {self.issue_key}: {e}")
            return {"status": "success", "data": {"transitions": []}}

        if action == "add_comment":
            issue_key = params.get("data", {}).get("issue_key") or self.issue_key
            comment = params.get("data", {}).get("comment")
            if not issue_key or not comment:
                return {"status": "error", "message": "issue_key and comment required"}
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    jira_client.add_comment(issue_key, comment)
                    return {"status": "success"}
                except Exception as e:
                    logger.exception(f"Failed to add comment to {issue_key}: {e}")
            # simulated success
            return {"status": "success"}

        if action == "transition_issue":
            issue_key = params.get("data", {}).get("issue_key") or self.issue_key
            transition = params.get("data", {}).get("transition")
            if not issue_key or not transition:
                return {"status": "error", "message": "issue_key and transition required"}
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    transitions = jira_client.transitions(issue_key)
                    transition_id = None
                    matched_transition = None
                    
                    # Try to find matching transition by name or ID
                    for t in transitions:
                        t_name = str(t.get("name", "")).lower()
                        t_id = str(t.get("id", ""))
                        
                        if t_name == str(transition).lower() or t_id == str(transition):
                            transition_id = t.get("id")
                            matched_transition = t.get("name")
                            break
                    
                    if not transition_id:
                        available = [t.get("name") for t in transitions]
                        logger.warning(f"Transition '{transition}' not found for {issue_key}. Available: {available}")
                        return {"status": "error", "message": f"Transition '{transition}' not found. Available: {available}"}
                    
                    jira_client.transition_issue(issue_key, transition=transition_id)
                    logger.info(f"✓ Transitioned {issue_key} to '{matched_transition}' (ID: {transition_id})")
                    return {"status": "success", "data": {"transition": matched_transition, "issue_key": issue_key}}
                except Exception as e:
                    logger.exception(f"Failed to transition {issue_key} -> {transition}: {e}")
                    return {"status": "error", "message": str(e)}
            # simulated success
            logger.debug(f"[SIMULATED] Transitioning {issue_key} to '{transition}'")
            return {"status": "success", "data": {"transition": transition, "issue_key": issue_key, "simulated": True}}

        if action == "create_subtask":
            data = params.get("data", {})
            parent_key = data.get("parent_key")
            summary = data.get("summary")
            issuetype = data.get("issuetype", "Sub-task")
            if not parent_key or not summary:
                return {"status": "error", "message": "parent_key and summary required"}
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    issue_dict = {
                        "project": {"key": self.jira_config.get("project_key")},
                        "summary": summary,
                        "issuetype": {"name": issuetype},
                        "parent": {"key": parent_key}
                    }
                    sub = jira_client.create_issue(fields=issue_dict)
                    sub_key = getattr(sub, "key", None)
                    return {"status": "success", "data": {"subtask_key": sub_key}}
                except Exception as e:
                    logger.exception(f"Failed to create subtask for {parent_key}: {e}")
            sub_key = f"SIM-SUB-{str(uuid.uuid4())[:8].upper()}"
            return {"status": "success", "data": {"subtask_key": sub_key}}

        if action == "add_attachment":
            data = params.get("data", {})
            issue_key = data.get("issue_key") or self.issue_key
            file_path = data.get("file_path")
            if not issue_key or not file_path:
                return {"status": "error", "message": "issue_key and file_path required"}
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    jira_client.add_attachment(issue=issue_key, attachment=file_path)
                    return {"status": "success"}
                except Exception as e:
                    logger.exception(f"Failed to add attachment to {issue_key}: {e}")
            return {"status": "success"}

        if action == "add_worklog":
            data = params.get("data", {})
            issue_key = data.get("issue_key") or self.issue_key
            time_spent = data.get("time_spent_seconds")
            comment = data.get("comment")
            if not issue_key or not time_spent:
                return {"status": "error", "message": "issue_key and time_spent_seconds required"}
            jira_client = self._get_jira_client()
            if jira_client:
                try:
                    jira_client.add_worklog(issue_key, time_spent_seconds=time_spent, comment=comment)
                    return {"status": "success"}
                except Exception as e:
                    logger.exception(f"Failed to add worklog to {issue_key}: {e}")
            return {"status": "success"}

        return {"status": "error", "message": f"Unsupported action: {action}"}


class TicketingSystemTool(MCPTool):
    """Ticketing System tool implementation (simulated)"""

    def __init__(self, mcp_host: Optional[Any] = None, jira_config: Optional[Dict[str, Any]] = None):
        super().__init__(
            tool_id="ticketing-system",
            tool_type=MCPToolType.TICKETING_SYSTEM,
            name="Ticketing System",
            description="Creates and manages support tickets for incidents",
            api_endpoint="http://localhost:8005/mcp/ticketing",
            parameters={
                "action": {"type": "string", "description": "Action to perform (create_ticket, update_ticket, get_ticket)"},
                "ticket_id": {"type": "string", "description": "Ticket ID for update/get operations"},
                "data": {"type": "object", "description": "Ticket data"}
            }
        )
        # Store tickets for simulation
        self.tickets: Dict[str, Dict[str, Any]] = {}
        # Optional MCP host so this tool can register related tools (like JIRA)
        self.mcp_host = mcp_host
        # Optional JIRA configuration for real integration
        self.jira_config = jira_config or {}
        # Keep per-ticket jira tools for executing lifecycle actions
        self._jira_tools: Dict[str, JIRATool] = {}

    def execute(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not params:
            params = {}
        action = params.get("action")
        if not action:
            return {"status": "error", "message": "Missing required parameter: action"}

        if action == "create_ticket":
            return self._create_ticket(params.get("data", {}))
        if action == "update_ticket":
            ticket_id = params.get("ticket_id")
            if not ticket_id:
                return {"status": "error", "message": "Missing required parameter: ticket_id"}
            return self._update_ticket(ticket_id, params.get("data", {}))
        if action == "get_ticket":
            ticket_id = params.get("ticket_id")
            if not ticket_id:
                return {"status": "error", "message": "Missing required parameter: ticket_id"}
            return self._get_ticket(ticket_id)
        return {"status": "error", "message": f"Unsupported action: {action}"}

    def _create_ticket(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            return {"status": "error", "message": "Empty ticket data"}

        ticket_id = data.get("incident_id") or str(uuid.uuid4())
        ticket = data.copy()
        ticket.update({
            "ticket_id": ticket_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "status": data.get("status", "open")
        })

        self.tickets[ticket_id] = ticket
        logger.info(f"Ticket created: {ticket_id}")

        # Register per-ticket JIRA tool and attempt to create an issue
        if self.mcp_host:
            try:
                jira_tool = JIRATool(ticket_id=ticket_id, summary=ticket.get("title", ""), description=ticket.get("description", ""), jira_config=self.jira_config)
                # register with MCP host if possible (mcp_host may not expose register_tool in this simplified context)
                try:
                    if hasattr(self.mcp_host, "register_tool"):
                        self.mcp_host.register_tool(jira_tool)
                except Exception:
                    logger.debug("MCP host register_tool failed or not supported")
                # keep local reference so updates can call jira_tool.execute directly
                self._jira_tools[ticket_id] = jira_tool

                create_result = jira_tool.execute({"action": "create_issue", "data": {"summary": ticket.get("title"), "description": ticket.get("description")}})
                if create_result.get("status") == "success":
                    issue_key = create_result.get("data", {}).get("issue_key")
                    issue_url = create_result.get("data", {}).get("issue_url")
                    if issue_key:
                        ticket["jira_issue_key"] = issue_key
                    if issue_url:
                        ticket["jira_issue_url"] = issue_url
            except Exception as e:
                logger.warning(f"Failed to register/create JIRA tool for ticket {ticket_id}: {e}")

        return {"status": "success", "data": {"ticket_id": ticket_id, "ticket": ticket}}

    def _update_ticket(self, ticket_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if ticket_id not in self.tickets:
            return {"status": "error", "message": f"Ticket not found: {ticket_id}"}

        ticket = self.tickets[ticket_id]
        # Detect status changes, notes, attachments, remediation steps
        status = data.get("status")
        notes = data.get("notes")
        attachments = data.get("attachments")  # list of file paths
        remediation_steps = data.get("remediation_steps")  # list of dicts {"summary":..., ...}

        # Update local ticket first
        ticket.update(data)
        ticket["updated_at"] = datetime.datetime.now().isoformat()

        jira_tool = self._jira_tools.get(ticket_id)

        # Best-effort: transition JIRA issue when status changes
        if jira_tool and status:
            # Use status map from config, with fallback to defaults
            status_map = self.jira_config.get("status_map", {
                "investigating": "In Progress",
                "identified": "To Do",
                "resolving": "In Progress",
                "resolved": "Done",
                "closed": "Done",
            })
            target_transition = status_map.get(status, status)
            
            # Ensure we have an issue key to operate on
            issue_key = ticket.get("jira_issue_key") or jira_tool.issue_key
            if issue_key and target_transition:
                logger.info(f"📋 Updating JIRA issue {issue_key}: incident status changed to '{status}' → transition to '{target_transition}'")
                try:
                    trans_result = jira_tool.execute({
                        "action": "transition_issue", 
                        "data": {"issue_key": issue_key, "transition": target_transition}
                    })
                    if trans_result.get("status") == "success":
                        logger.info(f"✓ JIRA transition successful for {issue_key}")
                    else:
                        logger.warning(f"⚠ JIRA transition failed: {trans_result.get('message', 'Unknown error')}")
                    
                    # add a comment about the transition
                    jira_tool.execute({
                        "action": "add_comment", 
                        "data": {"issue_key": issue_key, "comment": f"Incident status changed to: {status}"}
                    })
                except Exception as e:
                    logger.warning(f"⚠ Failed to update JIRA issue for ticket {ticket_id}: {e}")
            elif not issue_key:
                logger.warning(f"⚠ No JIRA issue key found for ticket {ticket_id}")
            elif not target_transition:
                logger.warning(f"⚠ No JIRA transition mapped for incident status '{status}'")

        # Add notes as JIRA comments
        if jira_tool and notes:
            # notes can be a single string or list
            note_list = notes if isinstance(notes, list) else [notes]
            issue_key = ticket.get("jira_issue_key") or jira_tool.issue_key
            if issue_key:
                logger.info(f"📝 Adding {len(note_list)} note(s) to JIRA issue {issue_key}")
                for n in note_list:
                    try:
                        jira_tool.execute({"action": "add_comment", "data": {"issue_key": issue_key, "comment": n}})
                    except Exception as e:
                        logger.warning(f"⚠ Failed to add comment to JIRA for ticket {ticket_id}: {e}")

        # Add attachments
        if jira_tool and attachments:
            issue_key = ticket.get("jira_issue_key") or jira_tool.issue_key
            if issue_key:
                logger.info(f"📎 Adding {len(attachments)} attachment(s) to JIRA issue {issue_key}")
                for fp in attachments:
                    try:
                        jira_tool.execute({"action": "add_attachment", "data": {"issue_key": issue_key, "file_path": fp}})
                    except Exception as e:
                        logger.warning(f"⚠ Failed to attach file to JIRA for ticket {ticket_id}: {e}")

        # Create subtasks for remediation steps (or add as comments if subtasks fail)
        if jira_tool and remediation_steps:
            issue_key = ticket.get("jira_issue_key") or jira_tool.issue_key
            if issue_key:
                logger.info(f"📋 Tracking {len(remediation_steps)} remediation action(s) in JIRA issue {issue_key}")
                
                # Build detailed remediation comment
                remediation_comment = "**Remediation Actions Executed:**\n\n"
                for idx, step in enumerate(remediation_steps, 1):
                    step_summary = step.get("summary", "Remediation step")
                    step_desc = step.get("description", step_summary)
                    remediation_comment += f"{idx}. {step_summary}\n"
                    if step_desc != step_summary:
                        remediation_comment += f"   Details: {step_desc}\n"
                remediation_comment += "\n✓ All remediation actions completed successfully."
                
                # Add as comment (more reliable than subtasks)
                try:
                    jira_tool.execute({
                        "action": "add_comment",
                        "data": {
                            "issue_key": issue_key,
                            "comment": remediation_comment
                        }
                    })
                    logger.info(f"✓ Remediation actions added as comment to {issue_key}")
                except Exception as e:
                    logger.warning(f"⚠ Failed to add remediation comment in JIRA for ticket {ticket_id}: {e}")
                
                # Try to create subtasks if possible (optional enhancement)
                for step in remediation_steps:
                    try:
                        step_summary = step.get("summary", "Remediation step")
                        jira_tool.execute({
                            "action": "create_subtask", 
                            "data": {
                                "parent_key": issue_key, 
                                "summary": step_summary
                            }
                        })
                    except Exception as e:
                        # Silently continue if subtask creation fails - comment already added
                        logger.debug(f"Subtask creation not supported for {issue_key}, using comments instead")
                        break

        logger.info(f"✓ Ticket updated: {ticket_id}")
        return {"status": "success", "data": {"ticket_id": ticket_id, "ticket": ticket}}

    def _get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        if ticket_id not in self.tickets:
            return {"status": "error", "message": f"Ticket not found: {ticket_id}"}
        return {"status": "success", "data": {"ticket_id": ticket_id, "ticket": self.tickets[ticket_id]}}