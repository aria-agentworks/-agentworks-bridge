#!/usr/bin/env python3
"""
Local Security Reconnaissance Script
Performs security analysis on 127.0.0.1
"""

import socket
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Set


class LocalSecurityRecon:
    """Security reconnaissance utility for local host analysis."""
    
    LOCALHOST = "127.0.0.1"
    
    def __init__(self):
        self.results = {
            "scan_timestamp": None,
            "target": None,
            "server_header_analysis": [],
            "port_scan": [],
            "exposed_endpoints": [],
            "summary": {}
        }
        
    def get_server_headers(self, port: int, timeout: float = 2.0) -> Dict:
        """Request server headers from the specified port."""
        headers = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.LOCALHOST, port))
            
            # Simple HTTP request to get headers
            request = f"GET / HTTP/1.1\r\nHost: {self.LOCALHOST}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            sock.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            lines = response_str.split("\r\n")
            
            # Parse headers after empty line
            header_section = False
            for line in lines:
                if line == "":
                    header_section = True
                    continue
                if header_section and ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
                    
        except Exception as e:
            headers = {"error": str(e)}
            
        return headers
    
    def analyze_server_header(self, port: int, headers: Dict) -> Dict:
        """Analyze server headers for security information."""
        analysis = {
            "port": port,
            "server_type": headers.get("server", "unknown"),
            "content_type": headers.get("content-type", "unknown"),
            "x_powered_by": headers.get("x-powered-by", "not specified"),
            "x_frame_options": headers.get("x-frame-options", "not set"),
            "x_content_type_options": headers.get("x-content-type-options", "not set"),
            "strict_transport_security": headers.get("strict-transport-security", "not set"),
            "content_security_policy": headers.get("content-security-policy", "not set"),
            "security_headers_set": self._check_security_headers(headers)
        }
        return analysis
    
    def _check_security_headers(self, headers: Dict) -> Dict:
        """Check for common security headers."""
        checks = {
            "x_frame_options": headers.get("x-frame-options") is not None and headers.get("x-frame-options") != "not set",
            "x_content_type_options": headers.get("x-content-type-options") is not None and headers.get("x-content-type-options") != "not set",
            "strict_transport_security": headers.get("strict-transport-security") is not None and headers.get("strict-transport-security") != "not set",
            "content_security_policy": headers.get("content-security-policy") is not None and headers.get("content-security-policy") != "not set",
            "x_xss_protection": headers.get("x-xss-protection") is not None and headers.get("x-xss-protection") != "not set"
        }
        
        total = len([v for v in checks.values() if v])
        checks["total_set"] = total
        checks["percentage"] = (total / len(checks)) * 100
        
        return checks
    
    def scan_port(self, port: int, timeout: float = 1.0) -> bool:
        """Scan if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.LOCALHOST, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def scan_local_services(self, port_range: range = range(1, 1024)) -> List[Dict]:
        """Scan common ports for listening services."""
        open_ports = []
        
        print(f"Scanning ports {port_range.start}-{port_range.stop-1}...")
        for port in port_range:
            if self.scan_port(port):
                open_ports.append(port)
                print(f"  Port {port}: OPEN")
        
        print(f"Scan complete. Found {len(open_ports)} open port(s).")
        return open_ports
    
    def check_exposed_endpoints(self, open_ports: List[int]) -> List[Dict]:
        """Check for exposed endpoints on open ports."""
        endpoints = []
        
        common_paths = ["/", "/admin", "/api", "/login", "/health", "/status", "/debug", "/actuator", "/dashboard", "/phpmyadmin", "/wp-admin"]
        
        for port in open_ports:
            headers = self.get_server_headers(port)
            
            if "error" not in headers:
                # Check common endpoints
                for path in common_paths:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2.0)
                        sock.connect((self.LOCALHOST, port))
                        request = f"GET {path} HTTP/1.1\r\nHost: {self.LOCALHOST}\r\nConnection: close\r\n\r\n"
                        sock.send(request.encode())
                        response = b""
                        while True:
                            data = sock.recv(4096)
                            if not data:
                                break
                            response += data
                        sock.close()
                        
                        response_str = response.decode('utf-8', errors='ignore')
                        
                        # Check response status
                        first_line = response_str.split("\r\n")[0]
                        if "200 OK" in first_line or "301 Moved" in first_line or "302 Found" in first_line:
                            endpoints.append({
                                "port": port,
                                "path": path,
                                "server_type": headers.get("server", "unknown"),
                                "exposed": True
                            })
                        elif "404" not in first_line:
                            endpoints.append({
                                "port": port,
                                "path": path,
                                "server_type": headers.get("server", "unknown"),
                                "exposed": True
                            })
                    except Exception:
                        pass
        
        return endpoints
    
    def run_full_scan(self) -> Dict:
        """Run complete security reconnaissance scan."""
        print("="*60)
        print("LOCAL SECURITY RECONNAISSANCE")
        print("="*60)
        print(f"Target: {self.LOCALHOST}")
        print(f"Scan started at: {datetime.now().isoformat()}")
        print("="*60)
        
        # Store scan metadata
        self.results["scan_timestamp"] = datetime.now().isoformat()
        self.results["target"] = self.LOCALHOST
        
        # Step 1: Scan for open ports
        print("\n[1/3] Port Scanning...")
        open_ports = self.scan_local_services(range(1, 1025))
        
        # Step 2: Analyze server headers on open ports
        print("\n[2/3] Analyzing Server Headers...")
        port_analysis = []
        for port in open_ports:
            print(f"  Analyzing port {port}...")
            headers = self.get_server_headers(port)
            analysis = self.analyze_server_header(port, headers)
            port_analysis.append(analysis)
            self.results["server_header_analysis"].append(analysis)
        
        # Step 3: Check exposed endpoints
        print("\n[3/3] Checking Exposed Endpoints...")
        exposed = self.check_exposed_endpoints(open_ports)
        self.results["exposed_endpoints"] = exposed
        
        # Generate summary
        print("\n" + "="*60)
        print("SECURITY REPORT SUMMARY")
        print("="*60)
        
        # Count security headers
        total_headers = sum([len(a["security_headers_set"])-2 for a in port_analysis])  # Exclude total_set and percentage
        secure_ports = sum([1 for a in port_analysis if a["security_headers_set"].get("percentage", 0) >= 60])
        
        summary = {
            "total_ports_scanned": 1024,
            "open_ports_found": len(open_ports),
            "open_port_list": open_ports,
            "ports_with_security_headers": secure_ports,
            "exposed_endpoints_found": len(exposed),
            "security_score": 100 - (len(open_ports) * 5) - (len(exposed) * 10),
            "recommendations": self._generate_recommendations(open_ports, exposed)
        }
        
        self.results["summary"] = summary
        
        print(f"Ports Scanned: 1024")
        print(f"Open Ports Found: {len(open_ports)}")
        print(f"Open Ports: {open_ports}")
        print(f"Ports with Good Security Headers: {secure_ports}/{len(open_ports)}")
        print(f"Exposed Endpoints: {len(exposed)}")
        print(f"Security Score: {summary['security_score']}/100")
        
        print("\nRECOMMENDATIONS:")
        for rec in summary["recommendations"]:
            print(f"  - {rec}")
        
        print("\nSCAN COMPLETE")
        print("="*60)
        
        return self.results
    
    def _generate_recommendations(self, open_ports: List[int], endpoints: List[Dict]) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        # Port scan recommendations
        sensitive_ports = [21, 22, 23, 25, 110, 139, 445, 3306, 5432, 6379, 27017]
        exposed_sensitive = [p for p in open_ports if p in sensitive_ports]
        if exposed_sensitive:
            recommendations.append(f"Consider restricting access to sensitive ports: {exposed_sensitive}")
        
        # Exposed endpoints recommendations
        admin_endpoints = [e for e in endpoints if "admin" in e["path"].lower()]
        if admin_endpoints:
            recommendations.append(f"Secure admin endpoints: {[e['path'] for e in admin_endpoints]}")
        
        # Missing security headers recommendations
        port_header_count = [a for a in self.results["server_header_analysis"] if a["security_headers_set"].get("percentage", 100) < 80]
        if port_header_count:
            recommendations.append("Implement comprehensive security headers (HSTS, CSP, X-Frame-Options, etc.)")
        
        # General recommendations
        if not recommendations:
            recommendations.append("No critical security issues detected. Continue monitoring.")
        
        return recommendations
    
    def save_report(self, filename: str = None) -> str:
        """Save scan results to a JSON file."""
        if filename is None:
            filename = f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nReport saved to: {filename}")
        return filename


def main():
    """Main entry point for the security reconnaissance script."""
    scanner = LocalSecurityRecon()
    results = scanner.run_full_scan()
    scanner.save_report()
    
    # Print full results
    print(f"\nFull JSON Report:\n")
    print(json.dumps(results, indent=2))
    
    return results


if __name__ == "__main__":
    main()
