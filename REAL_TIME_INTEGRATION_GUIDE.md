# Real-Time Integration Guide: From Simulation to Live IT Systems

## Executive Summary

Your POC currently uses **simulated data** for incident detection and remediation. This document provides a **complete roadmap** to integrate real-time data from actual IT infrastructure while keeping the agent-based architecture intact.

---

## Current Simulation Architecture

### Where Simulation Happens

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATION LAYER (Current)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. INCIDENT DATA                                               │
│     ├─ incident_data.py: 5 hardcoded incident templates        │
│     ├─ Tags: database, api, memory, disk, ssl                  │
│     └─ Used by: incident.py model                              │
│                                                                   │
│  2. LOG DATA                                                     │
│     ├─ log_data.py: Predefined log patterns per incident type  │
│     ├─ No real log ingestion                                   │
│     └─ Used by: LogAnalyzerTool via get_logs_for_incident()   │
│                                                                   │
│  3. SYSTEM METRICS                                              │
│     ├─ system_data.py: Randomly generated metrics              │
│     ├─ Functions: generate_*_metrics() with is_problem flag    │
│     └─ Used by: SystemMonitorTool                              │
│                                                                   │
│  4. DIAGNOSTIC ANALYSIS                                         │
│     ├─ diagnostic.py: Pattern matching on simulated logs       │
│     ├─ Simple if/else rules based on tag patterns             │
│     └─ Returns fixed root cause + confidence score             │
│                                                                   │
│  5. REMEDIATION STEPS                                           │
│     ├─ resolution.py: Hardcoded actions per root cause        │
│     ├─ Simulated MCP tool execution (no actual changes)       │
│     └─ Fake verification checks                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Current Data Flow

```
SimulatedIncident → DiagnosticAgent → LogAnalyzer → pattern matching → 
root cause → ResolutionAgent → fake remediation steps → JIRA ticket
```

---

## Real-Time Integration Strategy

### Phase 1: Incident Detection (Replace incident_data.py)

#### Option A: Prometheus + Alertmanager (Recommended for POC)

**What to replace:**
- `it_incident_response/simulation/incident_data.py`

**Implementation:**
```python
# it_incident_response/integrations/prometheus_client.py (NEW)

import requests
from typing import List, Dict, Any
import json

class PrometheusIncidentDetector:
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Fetch active alerts from Alertmanager"""
        response = requests.get(
            f"{self.prometheus_url}/api/v1/alerts",
            params={"state": "firing"}
        )
        return response.json().get("data", [])
    
    def query_metric(self, query: str) -> List[Dict[str, Any]]:
        """Execute Prometheus query"""
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query",
            params={"query": query}
        )
        return response.json().get("data", {}).get("result", [])

# Usage in system.py
detector = PrometheusIncidentDetector()
alerts = detector.get_active_alerts()  # Real-time incidents!
```

**Connection Points:**
- Modify `incident.py` model to accept Prometheus alerts
- Update `create_incident()` to parse alert metadata

#### Option B: ELK Stack (Elasticsearch)

```python
# it_incident_response/integrations/elasticsearch_client.py (NEW)

from elasticsearch import Elasticsearch

class ElasticsearchIncidentDetector:
    def __init__(self, es_url: str = "http://localhost:9200"):
        self.es = Elasticsearch([es_url])
    
    def detect_incidents(self, query: Dict) -> List[Dict[str, Any]]:
        """Find incident patterns in logs"""
        results = self.es.search(index="logs-*", body=query)
        return self._parse_results(results)
```

---

### Phase 2: Log Analysis (Replace log_data.py)

#### Real Log Sources

**Option A: ELK Stack**
```python
# it_incident_response/tools/log_analyzer.py (MODIFY)

class LogAnalyzerTool(MCPTool):
    def __init__(self, elasticsearch_url: str = None):
        super().__init__(...)
        if elasticsearch_url:
            self.es = Elasticsearch([elasticsearch_url])
            self.use_real_logs = True
        else:
            self.use_real_logs = False
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        incident_id = params.get("incident_id")
        
        if self.use_real_logs:
            # REAL: Query Elasticsearch for logs
            logs = self.query_elasticsearch_logs(incident_id)
        else:
            # SIMULATED: Use hardcoded logs
            from it_incident_response.simulation.log_data import get_logs_for_incident
            logs = get_logs_for_incident(incident)
        
        return self.analyze_patterns(logs)
    
    def query_elasticsearch_logs(self, incident_id: str) -> List[Dict]:
        """Query real logs from Elasticsearch"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"incident_id": incident_id}},
                        {"range": {"@timestamp": {"gte": "now-1h"}}}
                    ]
                }
            }
        }
        results = self.es.search(index="logs-*", body=query)
        return results["hits"]["hits"]
```

**Option B: Splunk**
```python
# Use Splunk SDK
from splunk_sdk import Client

class SplunkLogAnalyzer:
    def __init__(self, splunk_url: str, username: str, password: str):
        self.client = Client(
            host=splunk_url,
            username=username,
            password=password
        )
    
    def search_logs(self, query: str) -> List[Dict]:
        """Execute Splunk search"""
        response = self.client.jobs.oneshot(query)
        return list(response)
```

---

### Phase 3: System Metrics (Replace system_data.py)

#### Real Metric Sources

**Option A: Prometheus**
```python
# it_incident_response/tools/system_monitor.py (MODIFY)

class SystemMonitorTool(MCPTool):
    def __init__(self, prometheus_url: str = None):
        super().__init__(...)
        self.prometheus_url = prometheus_url
        self.use_real_metrics = prometheus_url is not None
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        servers = params.get("servers", [])
        
        if self.use_real_metrics:
            # REAL: Query Prometheus for metrics
            metrics = self._query_prometheus(servers)
        else:
            # SIMULATED: Generate random metrics
            incident = get_incident_by_id(params["incident_id"])
            metrics = generate_system_metrics_for_incident(incident)
        
        return self.analyze_metrics(metrics)
    
    def _query_prometheus(self, servers: List[str]) -> List[Dict]:
        """Query real metrics from Prometheus"""
        queries = {
            "cpu_usage": 'node_cpu_seconds_total{instance=~".*"}',
            "memory_usage": 'node_memory_MemAvailable_bytes{instance=~".*"}',
            "disk_usage": 'node_filesystem_avail_bytes{instance=~".*"}',
            "network_latency": 'probe_duration_seconds{instance=~".*"}'
        }
        
        metrics = []
        for server in servers:
            for metric_name, query in queries.items():
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": f'{query}[5m]'}
                )
                metrics.append(response.json())
        return metrics
```

**Option B: Grafana + Datasources**
```python
# Use Grafana API to fetch dashboard data
import requests

class GrafanaMetricsClient:
    def __init__(self, grafana_url: str, api_key: str):
        self.grafana_url = grafana_url
        self.api_key = api_key
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict:
        """Fetch real metrics from Grafana dashboard"""
        response = requests.get(
            f"{self.grafana_url}/api/dashboards/uid/{dashboard_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
```

---

### Phase 4: Enhanced Diagnostic Analysis

#### Replace Pattern Matching with Real ML/Rules

**Current approach (Simulated):**
```python
# diagnostic.py - Current simple pattern matching
if any("connection timeout" in pattern for pattern in log_patterns):
    root_cause = "Database connection timeout"
    confidence = 0.92
```

**Replace with:**

**Option A: Rule Engine (Easy)**
```python
# it_incident_response/analysis/rules_engine.py (NEW)

from dataclasses import dataclass
from typing import List, Callable

@dataclass
class DiagnosticRule:
    name: str
    condition: Callable  # Function that checks logs/metrics
    root_cause: str
    confidence_base: float
    remediation_actions: List[str]

# Define rules based on real patterns
DATABASE_TIMEOUT_RULE = DiagnosticRule(
    name="Database Timeout Detection",
    condition=lambda logs: any(
        "timeout" in log.get("message", "").lower() and 
        log.get("level") == "ERROR"
        for log in logs
    ),
    root_cause="Database connection timeout",
    confidence_base=0.92,
    remediation_actions=[
        "Increase connection pool size",
        "Tune database connection timeout",
        "Check network latency"
    ]
)

MEMORY_LEAK_RULE = DiagnosticRule(
    name="Memory Leak Detection",
    condition=lambda metrics: any(
        metric.get("memory_usage") > 90 and
        metric.get("trend") == "increasing"
        for metric in metrics
    ),
    root_cause="Memory leak in application",
    confidence_base=0.87,
    remediation_actions=[
        "Restart service",
        "Review code changes",
        "Monitor memory heap"
    ]
)

class RulesEngine:
    def __init__(self):
        self.rules = [DATABASE_TIMEOUT_RULE, MEMORY_LEAK_RULE]
    
    def diagnose(self, logs: List[Dict], metrics: List[Dict]):
        """Apply rules to find root cause"""
        for rule in self.rules:
            if rule.condition(logs) or rule.condition(metrics):
                return {
                    "root_cause": rule.root_cause,
                    "confidence": rule.confidence_base,
                    "remediation": rule.remediation_actions,
                    "rule_matched": rule.name
                }
        return None
```

**Option B: ML-Based (Advanced)**
```python
# Train a classifier on historical incident data
from sklearn.ensemble import RandomForestClassifier
import joblib

class MLDiagnosticModel:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)
    
    def diagnose(self, logs: List[Dict], metrics: List[Dict]) -> Dict:
        """Use trained ML model for diagnosis"""
        features = self._extract_features(logs, metrics)
        
        prediction = self.model.predict(features)
        confidence = self.model.predict_proba(features)
        
        return {
            "root_cause": self._label_to_cause(prediction[0]),
            "confidence": float(confidence[0].max()),
            "remediation": self._get_remediation(prediction[0])
        }
    
    def _extract_features(self, logs: List[Dict], metrics: List[Dict]):
        """Convert logs/metrics to ML features"""
        return [
            len([l for l in logs if l["level"] == "ERROR"]),
            max([m.get("cpu_usage", 0) for m in metrics]),
            max([m.get("memory_usage", 0) for m in metrics]),
            # ... more features
        ]
```

---

### Phase 5: Real Remediation Execution

#### Execute Real Commands via MCP Tools

**Current (Simulated):**
```python
# resolution.py - Current simulated execution
result = self.execute_mcp_tool("deployment-system", {
    "action": "restart_service",
    "target": system
})
# Returns fake {"status": "success"}
```

**Real Implementation:**

```python
# it_incident_response/tools/deployment.py (ENHANCE)

class DeploymentSystemTool(MCPTool):
    def __init__(self, use_real_deployment: bool = False):
        super().__init__(...)
        self.use_real = use_real_deployment
        if use_real:
            self.ssh_client = self._init_ssh()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        
        if action == "restart_service":
            if self.use_real:
                # REAL: Execute via SSH
                return self._restart_service_real(params)
            else:
                # SIMULATED: Return fake success
                return self._restart_service_simulated(params)
    
    def _restart_service_real(self, params: Dict) -> Dict:
        """Actually restart the service on real servers"""
        target = params.get("target")
        service_name = self._map_target_to_service(target)
        
        try:
            # SSH to server and restart service
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"sudo systemctl restart {service_name}"
            )
            
            if stdout.channel.recv_exit_status() == 0:
                return {"status": "success", "message": f"Restarted {service_name}"}
            else:
                return {"status": "error", "message": stderr.read().decode()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _init_ssh(self):
        """Initialize SSH client with credentials"""
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Load credentials from env or config
        return client
```

**Better: Use Ansible/Terraform**
```python
# it_incident_response/tools/infrastructure_automation.py (NEW)

import subprocess
import json

class AnsibleAutomationTool:
    """Execute real infrastructure changes via Ansible"""
    
    def __init__(self, playbook_dir: str):
        self.playbook_dir = playbook_dir
    
    def restart_service(self, target: str, service: str) -> Dict:
        """Restart service on target using Ansible"""
        playbook = f"{self.playbook_dir}/restart_service.yml"
        
        cmd = [
            "ansible-playbook", playbook,
            "-i", f"{target},",  # Single host
            "-e", f"service_name={service}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "errors": result.stderr
        }
    
    def scale_service(self, service: str, replicas: int) -> Dict:
        """Scale service using Kubernetes"""
        cmd = [
            "kubectl", "scale", "deployment",
            f"{service}", f"--replicas={replicas}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout
        }
```

---

## Integration Implementation Roadmap

### Step 1: Setup Infrastructure Connectors
```python
# New file: it_incident_response/integrations/__init__.py

from .prometheus_client import PrometheusIncidentDetector
from .elasticsearch_client import ElasticsearchLogAnalyzer
from .grafana_client import GrafanaMetricsClient

# Config from environment
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
GRAFANA_URL = os.getenv("GRAFANA_URL")
```

### Step 2: Update system.py
```python
# it_incident_response/system.py (MODIFY)

def __init__(self, use_real_data: bool = False):
    # ... existing code ...
    
    if use_real_data:
        # Use real integrations
        self.incident_detector = PrometheusIncidentDetector(PROMETHEUS_URL)
        jira_config = self._load_jira_config()  # Already exists
    else:
        # Use simulated data
        self.incident_detector = SimulatedIncidentDetector()
    
    self._register_mcp_tools()
```

### Step 3: Update tools to check for real vs simulated
```python
# Each tool (LogAnalyzerTool, SystemMonitorTool) needs:

def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
    if self.use_real_data:
        return self._execute_real(params)
    else:
        return self._execute_simulated(params)
```

---

## Configuration File for Real-Time Integration

```yaml
# config/real_integration_config.yaml

infrastructure:
  monitoring:
    prometheus:
      url: "http://prometheus.example.com:9090"
      alert_manager_url: "http://alertmanager.example.com:9093"
  
  logging:
    elasticsearch:
      url: "http://elasticsearch.example.com:9200"
      index_pattern: "logs-*"
    splunk:
      url: "https://splunk.example.com:8089"
      api_key: "${SPLUNK_API_KEY}"
  
  visualization:
    grafana:
      url: "https://grafana.example.com"
      api_key: "${GRAFANA_API_KEY}"

automation:
  deployment:
    ansible:
      inventory_file: "/etc/ansible/hosts"
      playbook_dir: "/opt/playbooks"
    kubernetes:
      kubeconfig: "${HOME}/.kube/config"
  
  remediation:
    ssh:
      username: "${SSH_USER}"
      private_key: "${SSH_KEY_PATH}"
      timeout: 30
    terraform:
      state_dir: "/opt/terraform"
      auto_approve: false

agents:
  diagnostic:
    use_ml_model: false
    ml_model_path: "/opt/models/diagnostic_model.pkl"
    use_rules_engine: true
  
  resolution:
    execute_real_commands: false
    require_approval: true  # Require human approval before execution
    dry_run: true  # Test run without actual changes

ticketing:
  jira:
    enabled: true
    url: "${JIRA_URL}"
    username: "${JIRA_USERNAME}"
    token: "${JIRA_TOKEN}"
```

---

## Environment Variables for Real Integration

```bash
# .env for real integration

# Infrastructure
PROMETHEUS_URL=http://localhost:9090
ELASTICSEARCH_URL=http://localhost:9200
GRAFANA_URL=https://localhost:3000
GRAFANA_API_KEY=your_grafana_api_key

# JIRA (already in your .env)
JIRA_BASE_URL=https://jira.example.com
JIRA_USERNAME=user@example.com
JIRA_TOKEN=your_jira_token

# SSH/Ansible
ANSIBLE_INVENTORY=/etc/ansible/hosts
SSH_KEY_PATH=/home/user/.ssh/id_rsa
SSH_USER=deployment

# Kubernetes (optional)
KUBECONFIG=$HOME/.kube/config

# Feature Flags
USE_REAL_DATA=false
EXECUTE_REAL_REMEDIATION=false
REQUIRE_APPROVAL_FOR_CHANGES=true
DRY_RUN_MODE=true
```

---

## Testing Strategy for Real Integration

### 1. Gradual Rollout
```
Phase 1: Real incident detection + simulated analysis + JIRA logging
Phase 2: Real logs + real analysis + simulated remediation
Phase 3: Real remediation with approval required
Phase 4: Full automation with monitoring
```

### 2. Safety Guards
```python
# it_incident_response/safety/approval_manager.py (NEW)

class ApprovalManager:
    def __init__(self, require_approval: bool = True):
        self.require_approval = require_approval
    
    def request_approval(self, incident: Dict, actions: List[str]) -> bool:
        """Request human approval before executing real changes"""
        if not self.require_approval:
            return True
        
        # Send Slack/Email notification
        self._notify_oncall(incident, actions)
        
        # Wait for approval (with timeout)
        return self._wait_for_approval(timeout=300)

class DryRunExecutor:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
    
    def execute(self, command: str, **kwargs) -> Dict:
        """Execute command or preview what would happen"""
        if self.dry_run:
            return {"status": "dry_run", "command": command, "args": kwargs}
        else:
            return self._execute_real(command, **kwargs)
```

---

## Expected Outcomes

### With Real Integration, Your System Can:

✅ **Detect incidents automatically** from Prometheus alerts  
✅ **Analyze real logs** from ELK/Splunk instead of predefined patterns  
✅ **Monitor actual system metrics** from Prometheus/Grafana  
✅ **Apply ML/rules** based on real incident history  
✅ **Execute real remediations** via Ansible/Kubernetes  
✅ **Track changes in JIRA** with actual incident details  
✅ **Provide audit trail** of all actions taken  

### Transition Timeline:

- **Week 1**: Set up infrastructure connectors
- **Week 2**: Integrate Prometheus/ELK for incident detection
- **Week 3**: Implement real diagnostic analysis
- **Week 4**: Enable real remediation with approval gates
- **Week 5**: Monitoring and fine-tuning

---

## Key Advantages of This Approach

1. **Non-Breaking**: Existing simulated system continues to work
2. **Progressive**: Switch to real data incrementally
3. **Safe**: Approval gates and dry-run modes prevent accidents
4. **Flexible**: Mix simulated and real data as needed
5. **MCP-Compatible**: Real tools can be wrapped as MCP tools
6. **A2A-Compatible**: Agents work with both simulated and real data

---

## Example: Complete Real-Time Flow

```python
# run_real_demo.py (NEW)

from it_incident_response.system import IncidentResponseSystem
from it_incident_response.integrations import PrometheusIncidentDetector
import os

# Enable real integration
os.environ["USE_REAL_DATA"] = "true"
os.environ["EXECUTE_REAL_REMEDIATION"] = "false"  # Still simulated
os.environ["REQUIRE_APPROVAL_FOR_CHANGES"] = "true"

# Initialize system with real data
system = IncidentResponseSystem(use_real_data=True)

# Fetch real incidents from Prometheus
prometheus = PrometheusIncidentDetector(
    os.getenv("PROMETHEUS_URL")
)
active_alerts = prometheus.get_active_alerts()

print(f"Found {len(active_alerts)} active alerts")

for alert in active_alerts:
    # Create incident from real alert
    incident_id = system.create_incident(
        title=alert["labels"]["alertname"],
        description=alert["annotations"]["description"],
        severity=alert["labels"]["severity"],
        affected_systems=alert["labels"].get("instance", "").split(",")
    )
    
    print(f"Created incident: {incident_id}")
    
    # Analyze with real logs and metrics
    diagnostic_report = system.analyze_incident(incident_id)
    print(f"Root cause: {diagnostic_report['root_cause']}")
    
    # Request approval before remediation
    approval = input("Execute remediation? (y/n): ")
    if approval.lower() == 'y':
        system.implement_resolution(incident_id)
    
    # Track in JIRA
    system.update_incident_status(
        incident_id,
        status="resolved",
        remediation_steps=diagnostic_report.get("recommended_actions", [])
    )

system.cleanup()
```

---

## Next Steps

1. **Choose your infrastructure stack** (Prometheus, ELK, Grafana, Kubernetes)
2. **Set up connectors** for each component
3. **Test with real data** in a sandbox environment
4. **Implement approval gates** for safety
5. **Monitor and iterate** based on real incident patterns

Your A2A + MCP architecture is perfectly suited for this evolution!
