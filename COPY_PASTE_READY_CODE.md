# Ready-to-Use: Copy-Paste Real-Time Integration Files

These are complete, copy-paste-ready Python files you can use immediately.

## File 1: Enhanced Metrics Exporter
**Location**: `monitoring/metrics_exporter.py`
**Just copy and paste this entire file**

```python
#!/usr/bin/env python3
"""
Prometheus metrics exporter that simulates infrastructure issues
Serves metrics on http://localhost:8000/metrics
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time
import random
import threading
import json
from flask import Flask, request, jsonify

# ============================================
# Metrics Definitions (Prometheus format)
# ============================================

# Database metrics
db_connection_timeout = Counter(
    'db_connection_timeout_total',
    'Database connection timeouts',
    ['instance', 'database']
)

db_query_time = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['instance', 'database'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

db_connections = Gauge(
    'db_connections_active',
    'Active database connections',
    ['instance', 'database']
)

# Application metrics
process_memory = Gauge(
    'process_resident_memory_bytes',
    'Process resident memory',
    ['instance', 'service']
)

process_cpu_seconds = Counter(
    'process_cpu_seconds_total',
    'Process CPU seconds',
    ['instance', 'service']
)

# HTTP/API metrics
http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['instance', 'method', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['instance', 'method'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# System metrics
disk_usage = Gauge(
    'node_filesystem_avail_bytes',
    'Available disk space',
    ['instance', 'mountpoint']
)

disk_total = Gauge(
    'node_filesystem_size_bytes',
    'Total disk space',
    ['instance', 'mountpoint']
)

# ============================================
# Scenario Manager
# ============================================

class ScenarioManager:
    """Manages active incident scenarios"""
    
    def __init__(self):
        self.active_scenarios = {}
        self.scenario_lock = threading.Lock()
    
    def start_scenario(self, name: str, duration: int = 60):
        """Start a scenario that runs for duration seconds"""
        with self.scenario_lock:
            self.active_scenarios[name] = {
                'start_time': time.time(),
                'duration': duration,
                'active': True
            }
        print(f"✅ Started scenario: {name} (duration: {duration}s)")
    
    def stop_scenario(self, name: str):
        """Stop a scenario"""
        with self.scenario_lock:
            if name in self.active_scenarios:
                del self.active_scenarios[name]
        print(f"⏹️  Stopped scenario: {name}")
    
    def is_active(self, name: str) -> bool:
        """Check if scenario is active"""
        with self.scenario_lock:
            if name not in self.active_scenarios:
                return False
            
            scenario = self.active_scenarios[name]
            elapsed = time.time() - scenario['start_time']
            
            # Check if duration expired
            if elapsed > scenario['duration']:
                del self.active_scenarios[name]
                return False
            
            return True
    
    def get_all_active(self) -> list:
        """Get all active scenarios"""
        with self.scenario_lock:
            return list(self.active_scenarios.keys())

# Global scenario manager
scenarios = ScenarioManager()

# ============================================
# Metrics Update Functions
# ============================================

def update_metrics():
    """Main loop that updates metrics every 5 seconds"""
    while True:
        try:
            # Database metrics
            if scenarios.is_active("database_timeout"):
                # Simulate high timeout rate
                db_connection_timeout.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).inc(random.uniform(2, 5))
                
                db_query_time.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).observe(random.uniform(5, 30))
                
                db_connections.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).set(random.randint(150, 200))
            else:
                # Normal database metrics
                db_connection_timeout.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).inc(random.uniform(0, 0.1))
                
                db_query_time.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).observe(random.uniform(0.01, 0.5))
                
                db_connections.labels(
                    instance='db-server-01',
                    database='customer_db'
                ).set(random.randint(20, 50))

            # Memory metrics
            if scenarios.is_active("memory_leak"):
                scenario = scenarios.active_scenarios.get("memory_leak", {})
                elapsed = time.time() - scenario.get('start_time', time.time())
                # Memory increases by 10MB per second
                memory = 200000000 + (elapsed * 10000000)
                
                process_memory.labels(
                    instance='app-server-01',
                    service='order_service'
                ).set(memory)
            else:
                process_memory.labels(
                    instance='app-server-01',
                    service='order_service'
                ).set(random.uniform(100000000, 300000000))

            process_cpu_seconds.labels(
                instance='app-server-01',
                service='order_service'
            ).inc(random.uniform(0.1, 0.8))

            # HTTP metrics
            if scenarios.is_active("api_503"):
                # High 503 error rate
                for _ in range(random.randint(10, 20)):
                    http_requests.labels(
                        instance='api-gateway-01',
                        method='GET',
                        status='503'
                    ).inc()
                
                for _ in range(random.randint(5, 15)):
                    http_requests.labels(
                        instance='api-gateway-01',
                        method='POST',
                        status='200'
                    ).inc()
            else:
                # Normal traffic
                for _ in range(random.randint(10, 50)):
                    http_requests.labels(
                        instance='api-gateway-01',
                        method='GET',
                        status='200'
                    ).inc()
                
                for _ in range(random.randint(5, 20)):
                    http_requests.labels(
                        instance='api-gateway-01',
                        method='POST',
                        status='200'
                    ).inc()

            http_request_duration.labels(
                instance='api-gateway-01',
                method='GET'
            ).observe(random.uniform(0.01, 0.5))

            # Disk metrics
            if scenarios.is_active("disk_full"):
                disk_usage.labels(
                    instance='storage-node-01',
                    mountpoint='/data'
                ).set(500000000)  # 500MB available
                disk_total.labels(
                    instance='storage-node-01',
                    mountpoint='/data'
                ).set(5000000000)  # 5GB total
            else:
                disk_usage.labels(
                    instance='storage-node-01',
                    mountpoint='/data'
                ).set(3000000000)  # 3GB available
                disk_total.labels(
                    instance='storage-node-01',
                    mountpoint='/data'
                ).set(5000000000)  # 5GB total

        except Exception as e:
            print(f"Error updating metrics: {e}")
        
        time.sleep(5)

# ============================================
# Flask API for Controlling Scenarios
# ============================================

app = Flask(__name__)

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint (handled by prometheus_client)"""
    # This is handled automatically by prometheus_client's WSGI middleware
    # But we need to include the registry explicitly
    from prometheus_client import generate_latest
    return generate_latest()

@app.route('/trigger/<scenario>', methods=['POST'])
def trigger_scenario(scenario):
    """Trigger a scenario"""
    data = request.get_json() or {}
    duration = data.get('duration', 60)
    
    valid_scenarios = ['database_timeout', 'memory_leak', 'api_503', 'disk_full']
    
    if scenario not in valid_scenarios:
        return {"error": f"Unknown scenario. Valid: {valid_scenarios}"}, 400
    
    scenarios.start_scenario(scenario, duration)
    
    return {
        "status": "ok",
        "scenario": scenario,
        "duration": duration,
        "message": f"Scenario '{scenario}' will run for {duration} seconds"
    }, 200

@app.route('/stop/<scenario>', methods=['POST'])
def stop_scenario(scenario):
    """Stop a scenario"""
    scenarios.stop_scenario(scenario)
    return {"status": "ok", "scenario": scenario}, 200

@app.route('/status', methods=['GET'])
def get_status():
    """Get current status"""
    return {
        "status": "running",
        "active_scenarios": scenarios.get_all_active(),
        "metrics": {
            "prometheus": "http://localhost:9090/metrics",
            "this_exporter": "http://localhost:8000/metrics"
        }
    }, 200

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("🚀 Starting Prometheus Metrics Exporter...")
    print("📊 Metrics available at: http://localhost:8000/metrics")
    print("🎮 Control scenarios at: http://localhost:8000/trigger/<scenario>")
    print("")
    print("Available scenarios:")
    print("  - database_timeout: Simulates DB connection timeouts")
    print("  - memory_leak: Simulates memory usage spike")
    print("  - api_503: Simulates API Gateway 503 errors")
    print("  - disk_full: Simulates low disk space")
    print("")
    
    # Start metrics update thread
    metrics_thread = threading.Thread(target=update_metrics, daemon=True)
    metrics_thread.start()
    
    # Start Flask app (without built-in Prometheus app)
    from prometheus_client import make_wsgi_app
    from werkzeug.serving import run_simple
    
    # Wrap Flask app with Prometheus WSGI middleware
    wsgi_app = make_wsgi_app(app)
    
    # Run Flask directly
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
```

---

## File 2: Alertmanager Webhook Receiver
**Location**: `it_incident_response/integrations/alertmanager_receiver.py`
**Copy and paste this entire file**

```python
#!/usr/bin/env python3
"""
Receives Alertmanager webhooks and creates incidents
"""

from flask import Flask, request, jsonify
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("incident-response.alertmanager")

class AlertmanagerReceiver:
    """Receives and processes Alertmanager webhooks"""
    
    def __init__(self, incident_system):
        """
        Args:
            incident_system: IncidentResponseSystem instance
        """
        self.system = incident_system
        self.app = Flask(__name__)
        self.alert_to_incident = {}  # Map alert fingerprint to incident ID
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhooks/alertmanager', methods=['POST'])
        def handle_alert():
            """Main webhook endpoint"""
            try:
                payload = request.json
                logger.info(f"Received Alertmanager webhook")
                
                alerts = payload.get('alerts', [])
                
                for alert in alerts:
                    status = alert.get('status')
                    
                    if status == 'firing':
                        self._handle_firing_alert(alert)
                    elif status == 'resolved':
                        self._handle_resolved_alert(alert)
                
                return jsonify({"status": "ok"}), 200
            
            except Exception as e:
                logger.error(f"Error handling alert: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check"""
            return jsonify({"status": "healthy"}), 200
    
    def _handle_firing_alert(self, alert: Dict[str, Any]):
        """Handle a firing alert"""
        
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        fingerprint = alert.get('fingerprint')
        
        alert_name = labels.get('alertname', 'Unknown')
        instance = labels.get('instance', 'unknown')
        
        print(f"\n🔴 ALERT FIRING: {alert_name} on {instance}")
        
        # Map alert to incident
        incident_data = self._map_alert_to_incident(alert_name, labels, annotations)
        
        if not incident_data:
            logger.warning(f"No mapping for alert: {alert_name}")
            return
        
        # Create incident
        incident_id = self.system.create_incident(
            title=incident_data['title'],
            description=incident_data['description'],
            severity=incident_data['severity'],
            affected_systems=incident_data['affected_systems'],
            tags=incident_data['tags']
        )
        
        # Store mapping
        if fingerprint:
            self.alert_to_incident[fingerprint] = incident_id
        
        print(f"✅ Incident created: {incident_id}")
        print(f"   Title: {incident_data['title']}")
        print(f"   Severity: {incident_data['severity']}")
        
        # Auto-trigger analysis and resolution
        print(f"📊 Starting diagnostic analysis...")
        try:
            self.system.analyze_incident(incident_id)
            print(f"✅ Diagnostic analysis complete")
        except Exception as e:
            logger.error(f"Error analyzing incident: {e}")
        
        print(f"🔧 Starting resolution...")
        try:
            self.system.implement_resolution(incident_id)
            print(f"✅ Resolution implemented")
        except Exception as e:
            logger.error(f"Error implementing resolution: {e}")
    
    def _handle_resolved_alert(self, alert: Dict[str, Any]):
        """Handle a resolved alert"""
        
        fingerprint = alert.get('fingerprint')
        incident_id = self.alert_to_incident.get(fingerprint)
        
        if incident_id:
            print(f"\n✅ ALERT RESOLVED: {alert['labels'].get('alertname')}")
            
            # Update incident status
            self.system.update_incident_status(
                incident_id,
                status='resolved',
                notes='Alert resolved in Prometheus/Alertmanager'
            )
            
            print(f"✅ Incident marked as resolved: {incident_id}")
            
            # Clean up
            del self.alert_to_incident[fingerprint]
    
    def _map_alert_to_incident(self, alert_name: str, labels: Dict, 
                               annotations: Dict) -> Optional[Dict[str, Any]]:
        """Map Prometheus alert to incident structure"""
        
        instance = labels.get('instance', 'unknown')
        server_name = instance.split(':')[0] if ':' in instance else instance
        
        # Map each alert type
        mappings = {
            'DatabaseConnectionTimeout': {
                'title': f'Database Connection Timeout - {server_name}',
                'description': annotations.get(
                    'description', 
                    f'Database connection timeouts detected on {server_name}'
                ),
                'severity': 'high',
                'affected_systems': [server_name],
                'tags': ['database', 'connectivity', 'timeout']
            },
            'HighMemoryUsage': {
                'title': f'High Memory Usage - {server_name}',
                'description': annotations.get(
                    'description',
                    f'Memory usage exceeds threshold on {server_name}'
                ),
                'severity': 'warning',
                'affected_systems': [server_name],
                'tags': ['memory', 'resource', 'performance']
            },
            'HighCPUUsage': {
                'title': f'High CPU Usage - {server_name}',
                'description': annotations.get(
                    'description',
                    f'CPU usage exceeds threshold on {server_name}'
                ),
                'severity': 'warning',
                'affected_systems': [server_name],
                'tags': ['cpu', 'resource', 'performance']
            },
            'APIGateway503': {
                'title': f'API Gateway 503 Errors - {server_name}',
                'description': annotations.get(
                    'description',
                    f'High 503 error rate on {server_name}'
                ),
                'severity': 'critical',
                'affected_systems': [server_name],
                'tags': ['api', 'gateway', '503', 'availability']
            },
            'DiskSpaceCritical': {
                'title': f'Disk Space Critical - {server_name}',
                'description': annotations.get(
                    'description',
                    f'Disk space below threshold on {server_name}'
                ),
                'severity': 'critical',
                'affected_systems': [server_name],
                'tags': ['disk', 'storage', 'space']
            }
        }
        
        return mappings.get(alert_name)
    
    def start(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Start the Flask webhook server"""
        logger.info(f"Starting Alertmanager webhook receiver on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)

```

---

## File 3: Integration into Your System
**Modify**: `it_incident_response/system.py`
**Add this to the __init__ method**:

```python
# Add these imports at the top
import os
from threading import Thread
from it_incident_response.integrations.alertmanager_receiver import AlertmanagerReceiver

# In IncidentResponseSystem.__init__, add this:

# Enable Alertmanager webhook receiver if configured
if os.getenv("ENABLE_ALERTMANAGER_WEBHOOK", "true").lower() == "true":
    try:
        self.webhook_receiver = AlertmanagerReceiver(self)
        webhook_thread = Thread(
            target=self.webhook_receiver.start,
            args=(
                os.getenv("WEBHOOK_HOST", "0.0.0.0"),
                int(os.getenv("WEBHOOK_PORT", "5000"))
            ),
            daemon=True
        )
        webhook_thread.start()
        logger.info("✅ Alertmanager webhook receiver enabled")
    except Exception as e:
        logger.warning(f"Could not start webhook receiver: {e}")
```

---

## File 4: Complete docker-compose.yml
**Location**: `docker-compose.yml` (in project root)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/rules.yml:/etc/prometheus/rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - monitoring
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 10s
      timeout: 5s
      retries: 5

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9093/-/ready"]
      interval: 10s
      timeout: 5s
      retries: 5

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring
    depends_on:
      - prometheus

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

---

## Quick Start: Copy-Paste Commands

```bash
# 1. Create monitoring directory
mkdir monitoring

# 2. Copy the configuration files (from REAL_TIME_SIMULATION_SETUP.md)
# Copy prometheus.yml to monitoring/
# Copy rules.yml to monitoring/
# Copy alertmanager.yml to monitoring/
# Copy docker-compose.yml to project root

# 3. Install Python dependencies
pip install prometheus-client flask

# 4. Start the stack
docker-compose up -d

# 5. Run metrics exporter
python monitoring/metrics_exporter.py

# 6. In another terminal, run your incident response system
python run_demo.py

# 7. In another terminal, trigger an incident
curl -X POST http://localhost:8000/trigger/database_timeout \
  -H "Content-Type: application/json" \
  -d '{"duration": 60}'

# 8. Watch the magic happen! 🎉
# - Prometheus collects metrics
# - Alert fires after ~1-2 minutes
# - Alertmanager sends webhook
# - Your system creates incident
# - Diagnostic agent analyzes
# - Resolution agent fixes it
# - Incident closes automatically
```

---

## Expected Output

```
$ curl -X POST http://localhost:8000/trigger/database_timeout ...
{"status": "ok", "scenario": "database_timeout", "duration": 60, ...}

# Your system output:
🔴 ALERT FIRING: DatabaseConnectionTimeout on db-server-01:9090
✅ Incident created: 12345-67890-abcdef
   Title: Database Connection Timeout - db-server-01
   Severity: high
📊 Starting diagnostic analysis...
✅ Diagnostic analysis complete
🔧 Starting resolution...
✅ Resolution implemented

# After metrics normalize:
✅ ALERT RESOLVED: DatabaseConnectionTimeout
✅ Incident marked as resolved: 12345-67890-abcdef
```

---

## Architecture Visualization

```
Your Code (triggers) → Metrics Exporter (port 8000)
                             ↓
                      Prometheus (port 9090)
                             ↓
                      Evaluates Rules (every 15s)
                             ↓
                      Alertmanager (port 9093)
                             ↓
                      Sends Webhook to:
                      http://localhost:5000/webhooks/alertmanager
                             ↓
                      Your Incident System
                             ↓
                      Create → Analyze → Resolve
```

That's it! You now have a complete real-time incident response system! 🚀
