# Real-Time Integration Simulation: Complete Setup Guide

## Overview

This guide shows you how to **create a local real-time environment** that mimics production monitoring systems, then **automatically detect and resolve simulated incidents** using your A2A + MCP system.

---

## Architecture: Local Simulation Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL TEST ENVIRONMENT                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Prometheus  │ ←→ │  Alertmanager│ ←→ │   Grafana    │       │
│  │  (9090)      │    │   (9093)     │    │  (3000)      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│        ↑                    ↑                                      │
│        │                    │ (webhook)                           │
│  scrape│                    │                                      │
│  targets│                    ↓                                      │
│        │              ┌──────────────┐                            │
│        └─────→        │   YOUR SYSTEM │                           │
│               │       │  (MCP Host +  │                           │
│        ┌──────┴───────┤   A2A Agents) │                           │
│        │              │               │                           │
│        ↓              └──────────────┘                            │
│  ┌──────────────────────┐                                        │
│  │   Fake Metrics       │    ┌──────────────────┐               │
│  │   Generator          │───→│  Local Targets   │               │
│  │   (Python Script)    │    │  :9091, :9092    │               │
│  │   - Triggers alerts  │    │                  │               │
│  │   - Injects errors   │    └──────────────────┘               │
│  │   - Simulates issues │                                        │
│  └──────────────────────┘                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Set Up Local Prometheus + Alertmanager + Grafana

### Option A: Using Docker (Easiest - Recommended)

#### 1. Create docker-compose.yml

```yaml
# docker-compose.yml in your project root

version: '3.8'

services:
  # Prometheus - Metrics collection and alerting
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

  # Alertmanager - Alert management
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

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring

  # Fake metrics exporter - Simulates your servers
  fake-metrics:
    build:
      context: .
      dockerfile: monitoring/Dockerfile.metrics
    container_name: fake-metrics
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8002:8002"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

#### 2. Create Prometheus Configuration

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'incident-response-monitor'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Load alert rules
rule_files:
  - '/etc/prometheus/rules.yml'

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Database server metrics
  - job_name: 'database-server'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Application server metrics
  - job_name: 'app-server'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # API Gateway metrics
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

#### 3. Create Alert Rules

```yaml
# monitoring/rules.yml

groups:
  - name: incident_rules
    interval: 15s
    rules:
      # Database connection timeout alert
      - alert: DatabaseConnectionTimeout
        expr: rate(db_connection_timeout_total[1m]) > 0.5
        for: 1m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "Database connection timeouts detected"
          description: "{{ $labels.instance }} is experiencing database connection timeouts"

      # High memory usage alert
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 500000000  # 500MB
        for: 2m
        labels:
          severity: warning
          component: memory
        annotations:
          summary: "High memory usage detected"
          description: "{{ $labels.instance }} memory usage: {{ $value | humanize }}"

      # High CPU usage alert
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[1m]) > 0.8
        for: 2m
        labels:
          severity: warning
          component: cpu
        annotations:
          summary: "High CPU usage detected"
          description: "{{ $labels.instance }} CPU usage: {{ $value | humanize }}"

      # API Gateway 503 errors alert
      - alert: APIGateway503Errors
        expr: rate(http_requests_total{status="503"}[1m]) > 0.1
        for: 1m
        labels:
          severity: critical
          component: api_gateway
        annotations:
          summary: "API Gateway returning 503 errors"
          description: "{{ $labels.instance }} is returning too many 503 errors"

      # Disk space critical alert
      - alert: DiskSpaceCritical
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 1m
        labels:
          severity: critical
          component: disk
        annotations:
          summary: "Disk space critical"
          description: "{{ $labels.instance }} disk space is below 10%"
```

#### 4. Create Alertmanager Configuration

```yaml
# monitoring/alertmanager.yml

global:
  resolve_timeout: 5m
  http_config:
    tls_config:
      insecure_skip_verify: true

# The root route with all parameters, which are inherited by the child routes if they are not overwritten.
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  # Routes for specific alerts
  routes:
    - match:
        severity: critical
      receiver: 'incident-response-webhook'
      continue: true

    - match:
        severity: warning
      receiver: 'incident-response-webhook'

receivers:
  # Default receiver (silent)
  - name: 'default'

  # Send alerts to your incident response system via webhook
  - name: 'incident-response-webhook'
    webhook_configs:
      - url: 'http://localhost:5000/webhooks/alertmanager'
        send_resolved: true

inhibit_rules:
  # Mute warning if critical alert is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance', 'component']
```

#### 5. Create Fake Metrics Exporter

```python
# monitoring/fake_metrics_exporter.py

from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time
import random
from threading import Thread
import os

# Database metrics
db_connection_timeout = Counter(
    'db_connection_timeout_total',
    'Total database connection timeouts',
    ['instance', 'database']
)
db_query_time = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['instance', 'database']
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

# API Gateway metrics
http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['instance', 'method', 'status']
)
http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['instance', 'method']
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

class IncidentSimulator:
    def __init__(self):
        self.scenario = None
        self.scenario_start_time = None
    
    def trigger_database_timeout(self):
        """Simulate database connection timeout issue"""
        print("🔴 Triggering DATABASE TIMEOUT scenario...")
        self.scenario = "database_timeout"
        self.scenario_start_time = time.time()
    
    def trigger_memory_leak(self):
        """Simulate memory leak"""
        print("🔴 Triggering MEMORY LEAK scenario...")
        self.scenario = "memory_leak"
        self.scenario_start_time = time.time()
    
    def trigger_api_gateway_503(self):
        """Simulate API Gateway 503 errors"""
        print("🔴 Triggering API GATEWAY 503 scenario...")
        self.scenario = "api_503"
        self.scenario_start_time = time.time()
    
    def trigger_disk_full(self):
        """Simulate disk space issue"""
        print("🔴 Triggering DISK FULL scenario...")
        self.scenario = "disk_full"
        self.scenario_start_time = time.time()
    
    def resolve_scenario(self):
        """Stop the current scenario"""
        if self.scenario:
            print(f"✅ Resolving {self.scenario} scenario...")
        self.scenario = None
        self.scenario_start_time = None

# Global simulator instance
simulator = IncidentSimulator()

def update_metrics():
    """Update metrics based on current scenario"""
    while True:
        # Database metrics
        if simulator.scenario == "database_timeout":
            # High timeout rate
            db_connection_timeout.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).inc(random.uniform(2, 5))
            
            db_query_time.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).observe(random.uniform(5, 30))
            
            db_connections.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).set(random.randint(150, 200))
        else:
            # Normal database metrics
            db_connection_timeout.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).inc(random.uniform(0, 0.1))
            
            db_query_time.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).observe(random.uniform(0.01, 0.5))
            
            db_connections.labels(
                instance='db-server-01:9090',
                database='customer_db'
            ).set(random.randint(20, 50))

        # App server metrics
        if simulator.scenario == "memory_leak":
            # Increasing memory usage
            elapsed = time.time() - simulator.scenario_start_time
            memory = 500000000 + (elapsed * 10000000)  # 500MB + 10MB per second
            process_memory.labels(
                instance='app-server-01:9090',
                service='order_service'
            ).set(memory)
        else:
            process_memory.labels(
                instance='app-server-01:9090',
                service='order_service'
            ).set(random.uniform(100000000, 300000000))  # 100-300MB

        process_cpu_seconds.labels(
            instance='app-server-01:9090',
            service='order_service'
        ).inc(random.uniform(0.1, 0.8))

        # API Gateway metrics
        if simulator.scenario == "api_503":
            # High 503 error rate
            for _ in range(random.randint(10, 20)):
                http_requests.labels(
                    instance='api-gateway-01:9090',
                    method='GET',
                    status='503'
                ).inc()
            
            for _ in range(random.randint(5, 15)):
                http_requests.labels(
                    instance='api-gateway-01:9090',
                    method='POST',
                    status='200'
                ).inc()
        else:
            # Normal traffic
            for _ in range(random.randint(10, 50)):
                http_requests.labels(
                    instance='api-gateway-01:9090',
                    method='GET',
                    status='200'
                ).inc()
            
            for _ in range(random.randint(5, 20)):
                http_requests.labels(
                    instance='api-gateway-01:9090',
                    method='POST',
                    status='200'
                ).inc()

        http_request_duration.labels(
            instance='api-gateway-01:9090',
            method='GET'
        ).observe(random.uniform(0.01, 0.5))

        # Disk metrics
        if simulator.scenario == "disk_full":
            # Low disk space
            disk_usage.labels(
                instance='storage-node-01:9090',
                mountpoint='/data'
            ).set(500000000)  # 500MB
            disk_total.labels(
                instance='storage-node-01:9090',
                mountpoint='/data'
            ).set(5000000000)  # 5GB
        else:
            # Normal disk usage
            disk_usage.labels(
                instance='storage-node-01:9090',
                mountpoint='/data'
            ).set(3000000000)  # 3GB
            disk_total.labels(
                instance='storage-node-01:9090',
                mountpoint='/data'
            ).set(5000000000)  # 5GB

        time.sleep(5)

if __name__ == '__main__':
    # Start Prometheus metrics server
    start_http_server(int(os.getenv('METRICS_PORT', '8000')))
    
    print(f"Prometheus metrics exporter started on port {os.getenv('METRICS_PORT', '8000')}")
    
    # Start metrics update thread
    metrics_thread = Thread(target=update_metrics, daemon=True)
    metrics_thread.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
```

#### 6. Create Dockerfile for Metrics Exporter

```dockerfile
# monitoring/Dockerfile.metrics

FROM python:3.11-slim

WORKDIR /app

RUN pip install prometheus-client

COPY monitoring/fake_metrics_exporter.py .

CMD python fake_metrics_exporter.py
```

#### 7. Start the Stack

```bash
# In your project root

# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f prometheus
docker-compose logs -f alertmanager
docker-compose logs -f fake-metrics

# Access services
# Prometheus: http://localhost:9090
# Alertmanager: http://localhost:9093
# Grafana: http://localhost:3000 (admin/admin)
```

---

## Part 2: Connect Your Incident Response System

### Create Webhook Receiver for Alertmanager

```python
# it_incident_response/integrations/alertmanager_webhook.py (NEW)

from flask import Flask, request, jsonify
from typing import Dict, List, Any
import logging
import json

logger = logging.getLogger("incident-response.alertmanager")

class AlertmanagerWebhookReceiver:
    """Receives alerts from Alertmanager and creates incidents"""
    
    def __init__(self, system):
        """
        Args:
            system: IncidentResponseSystem instance
        """
        self.system = system
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/webhooks/alertmanager', methods=['POST'])
        def handle_alert():
            """Handle incoming Alertmanager webhook"""
            payload = request.json
            
            logger.info(f"Received Alertmanager webhook: {json.dumps(payload, indent=2)}")
            
            alerts = payload.get('alerts', [])
            
            for alert in alerts:
                status = alert.get('status')
                
                if status == 'firing':
                    self._handle_firing_alert(alert)
                elif status == 'resolved':
                    self._handle_resolved_alert(alert)
            
            return jsonify({"status": "ok"}), 200
    
    def _handle_firing_alert(self, alert: Dict[str, Any]):
        """Handle a firing alert by creating an incident"""
        
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        alert_name = labels.get('alertname')
        severity = labels.get('severity', 'medium')
        component = labels.get('component', 'unknown')
        
        # Map Prometheus alert to incident
        incident_data = self._map_alert_to_incident(alert_name, labels, annotations)
        
        # Create incident in system
        incident_id = self.system.create_incident(
            title=incident_data['title'],
            description=incident_data['description'],
            severity=incident_data['severity'],
            affected_systems=incident_data['affected_systems'],
            tags=incident_data['tags']
        )
        
        logger.info(f"✅ Created incident {incident_id} from alert {alert_name}")
        
        # Store alert fingerprint to link back
        alert_fingerprint = alert.get('fingerprint')
        self._store_alert_fingerprint(incident_id, alert_fingerprint)
        
        return incident_id
    
    def _handle_resolved_alert(self, alert: Dict[str, Any]):
        """Handle a resolved alert by updating incident"""
        
        alert_fingerprint = alert.get('fingerprint')
        incident_id = self._get_incident_by_fingerprint(alert_fingerprint)
        
        if incident_id:
            # Update incident status to resolved
            self.system.update_incident_status(
                incident_id,
                status='resolved',
                notes='Alert resolved in Prometheus'
            )
            logger.info(f"✅ Resolved incident {incident_id}")
    
    def _map_alert_to_incident(self, alert_name: str, labels: Dict, 
                               annotations: Dict) -> Dict[str, Any]:
        """Map Prometheus alert to incident data"""
        
        instance = labels.get('instance', 'unknown')
        component = labels.get('component', 'unknown')
        
        mapping = {
            'DatabaseConnectionTimeout': {
                'title': f'Database Connection Timeout on {instance}',
                'description': annotations.get('description', 'Database connection timeout detected'),
                'severity': 'high',
                'affected_systems': [instance.split(':')[0]],
                'tags': ['database', 'connectivity', 'timeout']
            },
            'HighMemoryUsage': {
                'title': f'High Memory Usage on {instance}',
                'description': annotations.get('description', 'Memory usage exceeds threshold'),
                'severity': 'warning',
                'affected_systems': [instance.split(':')[0]],
                'tags': ['memory', 'resource']
            },
            'HighCPUUsage': {
                'title': f'High CPU Usage on {instance}',
                'description': annotations.get('description', 'CPU usage exceeds threshold'),
                'severity': 'warning',
                'affected_systems': [instance.split(':')[0]],
                'tags': ['cpu', 'resource']
            },
            'APIGateway503Errors': {
                'title': f'API Gateway 503 Errors on {instance}',
                'description': annotations.get('description', 'API Gateway returning 503 errors'),
                'severity': 'critical',
                'affected_systems': [instance.split(':')[0]],
                'tags': ['api', 'gateway', '503']
            },
            'DiskSpaceCritical': {
                'title': f'Disk Space Critical on {instance}',
                'description': annotations.get('description', 'Disk space below threshold'),
                'severity': 'critical',
                'affected_systems': [instance.split(':')[0]],
                'tags': ['disk', 'storage', 'space']
            }
        }
        
        return mapping.get(alert_name, {
            'title': alert_name,
            'description': annotations.get('description', alert_name),
            'severity': labels.get('severity', 'medium'),
            'affected_systems': [instance.split(':')[0]],
            'tags': [component]
        })
    
    def _store_alert_fingerprint(self, incident_id: str, fingerprint: str):
        """Store mapping of alert fingerprint to incident ID"""
        if not hasattr(self, '_alert_fingerprints'):
            self._alert_fingerprints = {}
        self._alert_fingerprints[fingerprint] = incident_id
    
    def _get_incident_by_fingerprint(self, fingerprint: str) -> str:
        """Get incident ID by alert fingerprint"""
        if not hasattr(self, '_alert_fingerprints'):
            return None
        return self._alert_fingerprints.get(fingerprint)
    
    def start(self, host: str = '0.0.0.0', port: int = 5000):
        """Start the Flask webhook server"""
        logger.info(f"Starting Alertmanager webhook receiver on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)
```

### Integrate Webhook into Your System

```python
# it_incident_response/system.py (MODIFY)

from it_incident_response.integrations.alertmanager_webhook import AlertmanagerWebhookReceiver
from threading import Thread
import os

class IncidentResponseSystem:
    def __init__(self, preload_incidents: bool = True, enable_webhooks: bool = True):
        # ... existing initialization ...
        
        # Enable Alertmanager webhook if requested
        self.webhook_receiver = None
        if enable_webhooks and os.getenv("ENABLE_WEBHOOKS", "true").lower() == "true":
            self.webhook_receiver = AlertmanagerWebhookReceiver(self)
            
            # Start webhook in background thread
            webhook_thread = Thread(
                target=self.webhook_receiver.start,
                args=(os.getenv("WEBHOOK_HOST", "0.0.0.0"), 
                      int(os.getenv("WEBHOOK_PORT", "5000"))),
                daemon=True
            )
            webhook_thread.start()
            logger.info("Alertmanager webhook receiver enabled")
```

---

## Part 3: Trigger Incidents and Auto-Resolve

### Create Incident Trigger Script

```python
# monitoring/trigger_incidents.py (NEW)

"""
Script to trigger simulated incidents for testing
"""

import requests
import time
import sys
from typing import List

class IncidentTrigger:
    def __init__(self, metrics_api: str = "http://localhost:8000"):
        self.metrics_api = metrics_api
        self.simulator = None
    
    def trigger_database_timeout(self, duration_seconds: int = 60):
        """
        Trigger database timeout incident
        
        1. Database connection timeouts start
        2. Prometheus detects within 1 minute
        3. Alertmanager fires DatabaseConnectionTimeout alert
        4. Your system creates incident via webhook
        5. Diagnostic agent analyzes logs
        6. Resolution agent restarts database
        """
        print("🔴 TRIGGERING: Database Connection Timeout")
        print(f"   Duration: {duration_seconds} seconds")
        print("   Expected flow:")
        print("   1. Metrics exporter generates timeout errors")
        print("   2. Prometheus evaluates alert rule")
        print("   3. Alertmanager sends webhook to incident response system")
        print("   4. Incident created automatically")
        print("   5. Diagnostic agent analyzes root cause")
        print("   6. Resolution agent implements fix")
        
        # Call metrics exporter API to start scenario
        try:
            response = requests.post(
                f"{self.metrics_api}/trigger/database_timeout",
                json={"duration": duration_seconds}
            )
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print(f"\n⏱️  Incident will auto-resolve in {duration_seconds} seconds...\n")
    
    def trigger_memory_leak(self, duration_seconds: int = 120):
        """Trigger memory leak incident"""
        print("🔴 TRIGGERING: Memory Leak")
        print(f"   Duration: {duration_seconds} seconds")
        try:
            response = requests.post(
                f"{self.metrics_api}/trigger/memory_leak",
                json={"duration": duration_seconds}
            )
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
    
    def trigger_api_gateway_503(self, duration_seconds: int = 90):
        """Trigger API Gateway 503 errors"""
        print("🔴 TRIGGERING: API Gateway 503 Errors")
        print(f"   Duration: {duration_seconds} seconds")
        try:
            response = requests.post(
                f"{self.metrics_api}/trigger/api_503",
                json={"duration": duration_seconds}
            )
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
    
    def trigger_disk_full(self, duration_seconds: int = 60):
        """Trigger disk space issue"""
        print("🔴 TRIGGERING: Disk Space Critical")
        print(f"   Duration: {duration_seconds} seconds")
        try:
            response = requests.post(
                f"{self.metrics_api}/trigger/disk_full",
                json={"duration": duration_seconds}
            )
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")

def print_menu():
    print("\n" + "="*60)
    print("         INCIDENT RESPONSE SYSTEM - TRIGGER MENU")
    print("="*60)
    print("\n1. Database Connection Timeout (60s)")
    print("2. Memory Leak (120s)")
    print("3. API Gateway 503 Errors (90s)")
    print("4. Disk Space Critical (60s)")
    print("5. Monitor Active Incidents")
    print("6. Exit")
    print("\n" + "="*60)

def main():
    trigger = IncidentTrigger()
    
    scenarios = {
        '1': lambda: trigger.trigger_database_timeout(),
        '2': lambda: trigger.trigger_memory_leak(),
        '3': lambda: trigger.trigger_api_gateway_503(),
        '4': lambda: trigger.trigger_disk_full(),
    }
    
    while True:
        print_menu()
        choice = input("\nSelect scenario (1-6): ").strip()
        
        if choice == '5':
            # Monitor active incidents
            try:
                response = requests.get("http://localhost:5000/api/incidents")
                incidents = response.json()
                print(f"\n📋 Active Incidents: {len(incidents)}")
                for incident in incidents:
                    print(f"  - {incident['title']} ({incident['status']})")
            except Exception as e:
                print(f"Error fetching incidents: {e}")
        
        elif choice == '6':
            print("Exiting...")
            break
        
        elif choice in scenarios:
            scenarios[choice]()
        
        else:
            print("Invalid choice")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Command line mode
        trigger = IncidentTrigger()
        scenario = sys.argv[1]
        
        if scenario == 'database_timeout':
            trigger.trigger_database_timeout()
        elif scenario == 'memory_leak':
            trigger.trigger_memory_leak()
        elif scenario == 'api_503':
            trigger.trigger_api_gateway_503()
        elif scenario == 'disk_full':
            trigger.trigger_disk_full()
    else:
        # Interactive menu
        main()
```

---

## Part 4: Complete End-to-End Flow

### Example: How Database Timeout Gets Detected and Resolved

```
┌──────────────────────────────────────────────────────────────────────┐
│                    1. TRIGGER INCIDENT (You Run)                      │
├──────────────────────────────────────────────────────────────────────┤
│ $ python monitoring/trigger_incidents.py database_timeout             │
│ 🔴 TRIGGERING: Database Connection Timeout                            │
│    Duration: 60 seconds                                              │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│              2. METRICS EXPORTER GENERATES ERRORS                      │
├──────────────────────────────────────────────────────────────────────┤
│ fake-metrics container starts generating:                            │
│ - db_connection_timeout_total increased                              │
│ - db_query_duration_seconds spike                                    │
│ - db_connections_active increased to 150-200                         │
│                                                                        │
│ Prometheus scrapes every 10 seconds and stores metrics               │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│           3. PROMETHEUS EVALUATES ALERT RULE (at 1 min)               │
├──────────────────────────────────────────────────────────────────────┤
│ Rule: rate(db_connection_timeout_total[1m]) > 0.5                    │
│                                                                        │
│ If True for 1 minute → ALERT FIRES                                   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│        4. ALERTMANAGER SENDS WEBHOOK (1-2 minutes)                    │
├──────────────────────────────────────────────────────────────────────┤
│ POST http://your-system:5000/webhooks/alertmanager                   │
│ {                                                                     │
│   "alerts": [                                                        │
│     {                                                                │
│       "status": "firing",                                            │
│       "labels": {                                                    │
│         "alertname": "DatabaseConnectionTimeout",                   │
│         "severity": "critical",                                     │
│         "component": "database",                                    │
│         "instance": "db-server-01:9090"                             │
│       },                                                             │
│       "annotations": {                                               │
│         "summary": "Database connection timeouts detected",          │
│         "description": "db-server-01 is experiencing timeouts"      │
│       }                                                              │
│     }                                                                │
│   ]                                                                  │
│ }                                                                     │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│              5. YOUR SYSTEM CREATES INCIDENT (AUTOMATIC)              │
├──────────────────────────────────────────────────────────────────────┤
│ AlertmanagerWebhookReceiver._handle_firing_alert()                   │
│                                                                        │
│ system.create_incident(                                              │
│   title="Database Connection Timeout on db-server-01:9090",          │
│   description="Database connection timeout detected",                │
│   severity="high",                                                   │
│   affected_systems=["db-server-01"],                                 │
│   tags=["database", "connectivity", "timeout"]                       │
│ )                                                                      │
│                                                                        │
│ ✅ INCIDENT CREATED: incident-uuid                                   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│         6. DIAGNOSTIC AGENT ANALYZES (AUTOMATIC)                      │
├──────────────────────────────────────────────────────────────────────┤
│ system.analyze_incident(incident_id)                                 │
│                                                                        │
│ 1. LogAnalyzerTool queries Prometheus for logs                       │
│ 2. SystemMonitorTool queries Prometheus for metrics                  │
│ 3. Diagnostic agent applies rules:                                   │
│    - Detects "connection timeout" pattern                            │
│    - Finds high db_query_duration_seconds                            │
│    - Root cause: "Database connection timeout due to..."             │
│    - Confidence: 92%                                                 │
│                                                                        │
│ 📊 DIAGNOSTIC REPORT COMPLETE                                        │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│      7. RESOLUTION AGENT IMPLEMENTS FIX (AUTOMATIC)                   │
├──────────────────────────────────────────────────────────────────────┤
│ system.implement_resolution(incident_id)                             │
│                                                                        │
│ 1. Based on root cause, resolution agent:                            │
│    - Increases connection timeout from 10s to 30s                    │
│    - Expands connection pool from 10 to 20                           │
│    - Restarts app-server-01 with new config                         │
│                                                                        │
│ 2. DeploymentSystemTool executes:                                    │
│    - Ansible playbook to update config                               │
│    - Kubernetes command to restart pod                               │
│    - Or SSH command to restart service                               │
│                                                                        │
│ ✅ REMEDIATION COMPLETE                                              │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│         8. METRICS RETURN TO NORMAL (After 60 seconds)                │
├──────────────────────────────────────────────────────────────────────┤
│ fake-metrics stops generating timeout errors                         │
│ db_connection_timeout_total rate decreases                           │
│ Prometheus evaluates rule again → FALSE                              │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│        9. ALERTMANAGER SENDS RESOLVED NOTIFICATION                    │
├──────────────────────────────────────────────────────────────────────┤
│ POST http://your-system:5000/webhooks/alertmanager                   │
│ {                                                                     │
│   "alerts": [                                                        │
│     {                                                                │
│       "status": "resolved",                                          │
│       "labels": {                                                    │
│         "alertname": "DatabaseConnectionTimeout",                   │
│         ...                                                          │
│       }                                                              │
│     }                                                                │
│   ]                                                                  │
│ }                                                                     │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│      10. INCIDENT MARKED RESOLVED (AUTOMATIC)                         │
├──────────────────────────────────────────────────────────────────────┤
│ AlertmanagerWebhookReceiver._handle_resolved_alert()                 │
│                                                                        │
│ system.update_incident_status(                                       │
│   incident_id,                                                       │
│   status="resolved",                                                 │
│   notes="Alert resolved in Prometheus"                               │
│ )                                                                      │
│                                                                        │
│ ✅ INCIDENT RESOLVED: status=resolved                                │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│          11. JIRA TICKET UPDATED (If configured)                      │
├──────────────────────────────────────────────────────────────────────┤
│ Ticketing tool updates JIRA with:                                    │
│ - Root cause: "Database connection timeout..."                       │
│ - Actions taken: 3 remediation steps                                 │
│ - Status: Resolved                                                   │
│ - Timeline: Started → Identified → Resolved                          │
│                                                                        │
│ 📝 JIRA TICKET: KAN-100                                              │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘

🎉 COMPLETE END-TO-END AUTOMATED INCIDENT RESPONSE!
Total Time: ~3-5 minutes (depends on alert evaluation time)
Human Involvement: 0 (fully automated)
```

---

## Part 5: Running Everything

### Quick Start Script

```bash
#!/bin/bash
# monitoring/start_everything.sh

echo "🚀 Starting Real-Time Incident Response Environment..."

# Start Docker services
echo "1️⃣  Starting Prometheus, Alertmanager, Grafana..."
docker-compose up -d
sleep 10

# Check if services are up
echo "2️⃣  Waiting for services to be ready..."
until curl -s http://localhost:9090/-/healthy > /dev/null; do
  echo "   Prometheus not ready yet..."
  sleep 5
done

until curl -s http://localhost:9093/-/healthy > /dev/null; do
  echo "   Alertmanager not ready yet..."
  sleep 5
done

echo "✅ All services running!"
echo ""
echo "📊 Access:"
echo "   Prometheus: http://localhost:9090"
echo "   Alertmanager: http://localhost:9093"
echo "   Grafana: http://localhost:3000"
echo ""
echo "3️⃣  Starting your incident response system..."
cd ..
python -m it_incident_response.system &
sleep 5
echo "✅ Incident response system started!"
echo ""
echo "4️⃣  Ready to trigger incidents!"
echo "   Run: python monitoring/trigger_incidents.py"
```

### Manual Testing

```bash
# Terminal 1: Start the stack
docker-compose up -d
sleep 10

# Terminal 2: Start your incident response system
python run_demo.py --use-real-data

# Terminal 3: Monitor Prometheus
curl http://localhost:9090/api/v1/alerts

# Terminal 4: Monitor Alertmanager
curl http://localhost:9093/api/v1/alerts

# Terminal 5: Trigger incidents
python monitoring/trigger_incidents.py
# Then select scenarios from menu

# Terminal 6: Check incidents in your system
curl http://localhost:5000/api/incidents
```

---

## Summary: Real-Time Simulation Workflow

| Step | Component | Action | Time |
|------|-----------|--------|------|
| 1 | You | Run trigger script | ~0s |
| 2 | fake-metrics | Generate error metrics | ~0-5s |
| 3 | Prometheus | Scrape and evaluate rules | ~10-15s |
| 4 | Alertmanager | Send webhook | ~15-20s |
| 5 | Your System | Create incident | ~20s |
| 6 | Diagnostic Agent | Analyze root cause | ~25s |
| 7 | Resolution Agent | Execute fix | ~30s |
| 8 | fake-metrics | Stop generating errors | ~60s |
| 9 | Prometheus | Evaluate rule again | ~70s |
| 10 | Alertmanager | Send resolved | ~75s |
| 11 | Your System | Close incident | ~75s |

**Total time: 3-5 minutes for full automated response!**

---

## Advantages of This Approach

✅ **Fully Local** - No external services needed  
✅ **Repeatable** - Trigger the same scenario multiple times  
✅ **Realistic** - Uses real Prometheus/Alertmanager  
✅ **Fast** - All in-process, no latency issues  
✅ **Controlled** - You control what errors are generated  
✅ **Observable** - Watch each step in the process  
✅ **Safe** - No risk to real systems  
✅ **Scalable** - Easy to add new scenarios  

This is production-grade simulation for testing your incident response system!
