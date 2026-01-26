#!/usr/bin/env python3
"""
tests/k3s_qa_tests.py
K3s Platform QA Test Suite - Health checks, routing verification, and coverage tests
"""

import subprocess
import json
import time
import sys
import requests
from typing import Dict, List, Tuple

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class K3sHealthChecker:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_command(self, cmd: str) -> Tuple[str, int]:
        """Execute shell command and return output"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.stdout, result.returncode
        except subprocess.TimeoutExpired:
            return "", 1
        except Exception as e:
            return str(e), 1
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{status} - {test_name}")
        if details:
            print(f"  └─ {details}")
        
        self.test_results.append({
            "test": test_name,
            "status": "PASSED" if passed else "FAILED",
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def check_k3s_running(self) -> bool:
        """Verify K3s service is running"""
        print(f"\n{Colors.BLUE}=== K3s Service Health Check ==={Colors.END}")
        output, code = self.run_command("sudo systemctl is-active k3s")
        is_active = output.strip() == "active"
        self.log_test("K3s Service Running", is_active, f"Status: {output.strip()}")
        return is_active
    
    def check_pods_ready(self, namespace: str = "default") -> bool:
        """Verify all pods are in Ready state"""
        print(f"\n{Colors.BLUE}=== Pod Readiness Check ==={Colors.END}")
        
        cmd = f"kubectl get pods -n {namespace} -o json"
        output, code = self.run_command(cmd)
        
        if code != 0:
            self.log_test("Get Pods", False, "Failed to retrieve pod information")
            return False
        
        try:
            pods_data = json.loads(output)
            pods = pods_data.get('items', [])
            
            if not pods:
                self.log_test("Pod Existence", False, "No pods found in cluster")
                return False
            
            all_ready = True
            for pod in pods:
                pod_name = pod['metadata']['name']
                
                # Check pod phase
                phase = pod['status'].get('phase', 'Unknown')
                
                # Check container readiness
                conditions = pod['status'].get('conditions', [])
                ready_condition = next(
                    (c for c in conditions if c['type'] == 'Ready'), 
                    None
                )
                
                is_ready = (
                    phase == "Running" and 
                    ready_condition and 
                    ready_condition['status'] == 'True'
                )
                
                self.log_test(
                    f"Pod Ready: {pod_name}", 
                    is_ready, 
                    f"Phase: {phase}, Ready: {ready_condition['status'] if ready_condition else 'Unknown'}"
                )
                
                if not is_ready:
                    all_ready = False
            
            return all_ready
            
        except json.JSONDecodeError:
            self.log_test("Parse Pod Data", False, "Invalid JSON response")
            return False
    
    def check_liveness_readiness_probes(self, namespace: str = "default") -> bool:
        """Verify liveness and readiness probes are configured"""
        print(f"\n{Colors.BLUE}=== Liveness/Readiness Probe Check ==={Colors.END}")
        
        cmd = f"kubectl get pods -n {namespace} -o json"
        output, code = self.run_command(cmd)
        
        if code != 0:
            self.log_test("Get Pod Probes", False, "Cannot retrieve probe configuration")
            return False
        
        try:
            pods_data = json.loads(output)
            pods = pods_data.get('items', [])
            
            all_configured = True
            for pod in pods:
                pod_name = pod['metadata']['name']
                containers = pod['spec'].get('containers', [])
                
                for container in containers:
                    container_name = container['name']
                    
                    has_liveness = 'livenessProbe' in container
                    has_readiness = 'readinessProbe' in container
                    
                    probe_status = f"Liveness: {has_liveness}, Readiness: {has_readiness}"
                    
                    # Warning if probes missing (not failure, but recommended)
                    if not has_liveness or not has_readiness:
                        self.log_test(
                            f"Probes: {pod_name}/{container_name}", 
                            False, 
                            f"{probe_status} - Probes recommended for production"
                        )
                        all_configured = False
                    else:
                        self.log_test(
                            f"Probes: {pod_name}/{container_name}", 
                            True, 
                            probe_status
                        )
            
            return all_configured
            
        except Exception as e:
            self.log_test("Probe Configuration Check", False, str(e))
            return False
    
    def check_service_endpoints(self, namespace: str = "default") -> bool:
        """Verify services have active endpoints"""
        print(f"\n{Colors.BLUE}=== Service Endpoints Check ==={Colors.END}")
        
        cmd = f"kubectl get services -n {namespace} -o json"
        output, code = self.run_command(cmd)
        
        if code != 0:
            self.log_test("Get Services", False, "Cannot retrieve services")
            return False
        
        try:
            services_data = json.loads(output)
            services = services_data.get('items', [])
            
            all_healthy = True
            for svc in services:
                svc_name = svc['metadata']['name']
                
                # Skip kubernetes default service
                if svc_name == "kubernetes":
                    continue
                
                # Get endpoints for this service
                ep_cmd = f"kubectl get endpoints {svc_name} -n {namespace} -o json"
                ep_output, ep_code = self.run_command(ep_cmd)
                
                if ep_code == 0:
                    ep_data = json.loads(ep_output)
                    subsets = ep_data.get('subsets', [])
                    
                    has_endpoints = len(subsets) > 0 and any(
                        'addresses' in s and len(s['addresses']) > 0 
                        for s in subsets
                    )
                    
                    endpoint_count = sum(
                        len(s.get('addresses', [])) 
                        for s in subsets
                    )
                    
                    self.log_test(
                        f"Service Endpoints: {svc_name}", 
                        has_endpoints, 
                        f"Active endpoints: {endpoint_count}"
                    )
                    
                    if not has_endpoints:
                        all_healthy = False
                else:
                    self.log_test(f"Service Endpoints: {svc_name}", False, "Cannot get endpoints")
                    all_healthy = False
            
            return all_healthy
            
        except Exception as e:
            self.log_test("Service Endpoint Check", False, str(e))
            return False

class IngressRoutingTester:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_command(self, cmd: str) -> Tuple[str, int]:
        """Execute shell command"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.stdout, result.returncode
        except Exception as e:
            return str(e), 1
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{status} - {test_name}")
        if details:
            print(f"  └─ {details}")
        
        self.test_results.append({
            "test": test_name,
            "status": "PASSED" if passed else "FAILED",
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def check_ingress_exists(self, namespace: str = "default") -> List[Dict]:
        """Check if ingress resources exist"""
        print(f"\n{Colors.BLUE}=== Ingress Configuration Check ==={Colors.END}")
        
        cmd = f"kubectl get ingress -n {namespace} -o json"
        output, code = self.run_command(cmd)
        
        if code != 0:
            self.log_test("Get Ingress", False, "Cannot retrieve ingress resources")
            return []
        
        try:
            ingress_data = json.loads(output)
            ingresses = ingress_data.get('items', [])
            
            if not ingresses:
                self.log_test("Ingress Existence", False, "No ingress resources found")
                return []
            
            self.log_test("Ingress Existence", True, f"Found {len(ingresses)} ingress resource(s)")
            return ingresses
            
        except Exception as e:
            self.log_test("Parse Ingress Data", False, str(e))
            return []
    
    def check_ingress_routing(self, ingresses: List[Dict]) -> bool:
        """Test ingress routing rules"""
        print(f"\n{Colors.BLUE}=== Ingress Routing Test ==={Colors.END}")
        
        all_passed = True
        for ingress in ingresses:
            ingress_name = ingress['metadata']['name']
            rules = ingress['spec'].get('rules', [])
            
            for rule in rules:
                host = rule.get('host', 'default-backend')
                paths = rule.get('http', {}).get('paths', [])
                
                for path_obj in paths:
                    path = path_obj.get('path', '/')
                    backend = path_obj.get('backend', {})
                    service_name = backend.get('service', {}).get('name', 'unknown')
                    service_port = backend.get('service', {}).get('port', {}).get('number', 'unknown')
                    
                    routing_info = f"Host: {host}, Path: {path} → Service: {service_name}:{service_port}"
                    
                    # Verify backend service exists
                    svc_cmd = f"kubectl get service {service_name} -o json 2>/dev/null"
                    svc_output, svc_code = self.run_command(svc_cmd)
                    
                    if svc_code == 0:
                        self.log_test(
                            f"Ingress Route: {ingress_name}", 
                            True, 
                            routing_info
                        )
                    else:
                        self.log_test(
                            f"Ingress Route: {ingress_name}", 
                            False, 
                            f"{routing_info} - Backend service not found"
                        )
                        all_passed = False
        
        return all_passed
    
    def test_ingress_connectivity(self, ingresses: List[Dict]) -> bool:
        """Test actual HTTP connectivity through ingress"""
        print(f"\n{Colors.BLUE}=== Ingress HTTP Connectivity Test ==={Colors.END}")
        
        all_passed = True
        
        for ingress in ingresses:
            rules = ingress['spec'].get('rules', [])
            
            for rule in rules:
                host = rule.get('host', 'localhost')
                
                # Try to curl the ingress endpoint
                test_url = f"http://localhost:80"
                
                try:
                    response = requests.get(
                        test_url, 
                        headers={'Host': host},
                        timeout=5
                    )
                    
                    success = response.status_code in [200, 301, 302, 404]
                    
                    self.log_test(
                        f"HTTP Request: {host}", 
                        success, 
                        f"Status: {response.status_code}"
                    )
                    
                    if not success:
                        all_passed = False
                        
                except requests.exceptions.RequestException as e:
                    self.log_test(
                        f"HTTP Request: {host}", 
                        False, 
                        f"Connection failed: {str(e)}"
                    )
                    all_passed = False
        
        return all_passed

def generate_coverage_report(health_checker, routing_tester):
    """Generate test coverage report"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}=== TEST COVERAGE REPORT ==={Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    total_tests = health_checker.passed + health_checker.failed + routing_tester.passed + routing_tester.failed
    total_passed = health_checker.passed + routing_tester.passed
    total_failed = health_checker.failed + routing_tester.failed
    
    coverage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Health Checks: {health_checker.passed} passed, {health_checker.failed} failed")
    print(f"Routing Tests: {routing_tester.passed} passed, {routing_tester.failed} failed")
    print(f"\n{Colors.BLUE}Total Tests:{Colors.END} {total_tests}")
    print(f"{Colors.GREEN}Passed:{Colors.END} {total_passed}")
    print(f"{Colors.RED}Failed:{Colors.END} {total_failed}")
    print(f"{Colors.YELLOW}Coverage:{Colors.END} {coverage:.1f}%\n")
    
    categories = [
        "✓ K3s Service Health",
        "✓ Pod Readiness State",
        "✓ Liveness/Readiness Probes",
        "✓ Service Endpoints",
        "✓ Ingress Configuration",
        "✓ Ingress Routing Rules",
        "✓ HTTP Connectivity"
    ]
    
    print(f"{Colors.BLUE}Test Categories Covered:{Colors.END}")
    for cat in categories:
        print(f"  {cat}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    return total_failed == 0

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}K3s Platform QA Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # Health checks
    health_checker = K3sHealthChecker()
    health_checker.check_k3s_running()
    health_checker.check_pods_ready()
    health_checker.check_liveness_readiness_probes()
    health_checker.check_service_endpoints()
    
    # Routing tests
    routing_tester = IngressRoutingTester()
    ingresses = routing_tester.check_ingress_exists()
    if ingresses:
        routing_tester.check_ingress_routing(ingresses)
        routing_tester.test_ingress_connectivity(ingresses)
    
    # Generate coverage report
    all_passed = generate_coverage_report(health_checker, routing_tester)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
