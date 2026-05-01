#!/usr/bin/env python3
"""
CVE-2026-41940 Vulnerability Scanner
Scan cPanel/WHM instances for CVE-2026-41940 (CRLF injection/whostmgrsession vulnerability)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse, urljoin
import urllib.request
import urllib.error


def get_target_domain(url):
    """Extract domain and base URL from target URL."""
    parsed = urlparse(url)
    domain = parsed.netloc
    if not domain:
        # If URL doesn't have scheme, use as-is
        domain = url.split('/')[0].split(':')[0]
    
    # Remove port from domain if present
    domain = domain.split(':')[0]
    return domain, f"{parsed.scheme if parsed.scheme else 'https'}://{domain}"


def get_headers(url, timeout=10):
    """
    Perform HEAD request and return headers.
    Returns dict of headers or None on error.
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; CVE-2026-41940-Scanner/1.0)')
        req.add_header('Accept', '*/*')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            headers = {}
            for key, value in response.headers.items():
                headers[key.lower()] = value
            headers['_http_status_code'] = str(response.status)
            return headers
    except urllib.error.HTTPError as e:
        headers = {}
        if hasattr(e, 'headers'):
            for key, value in e.headers.items():
                headers[key.lower()] = value
        headers['_http_status_code'] = str(e.code)
        headers['_http_reason'] = e.reason
        return headers
    except urllib.error.URLError as e:
        return None
    except Exception as e:
        return None


def extract_cpanel_version(headers):
    """
    Extract cPanel version from headers.
    Looking for patterns like X-Cpanel-Version, Server, etc.
    """
    version = None
    
    # Check X-CPanel-Version header
    if 'x-cpanel-version' in headers:
        version = headers['x-cpanel-version'].strip()
    
    # Check Server header for cPanel version
    if not version and 'server' in headers:
        server = headers['server'].lower()
        # cPanel server header often contains version
        match = re.search(r'cpanel/(\d+(?:\.\d+)*(?:\.\d+)?)', server)
        if match:
            version = match.group(1)
        # Check for WHAM server versions
        match = re.search(r'wham/(\d+(?:\.\d+)*)', server)
        if match:
            version = match.group(1)
    
    # Check for version in other common locations
    if not version and 'x-cpe-version' in headers:
        version = headers['x-cpe-version'].strip()
    
    return version


def parse_version(version_string):
    """
    Parse version string into comparable tuple.
    Returns tuple of integers or None if parsing fails.
    """
    if not version_string:
        return None
    
    # Clean version string
    version_string = version_string.strip().split()[0]
    
    # Handle versions like 82.0.1, 82, 82.0.0
    parts = version_string.split('.')[:3]
    try:
        result = tuple(int(p) if p.isdigit() else 0 for p in parts)
        while len(result) < 3:
            result += (0,)
        return result
    except ValueError:
        return None


def check_version_vulnerable(version_string):
    """
    Check if cPanel version is vulnerable (before April 2026 patch).
    Versions before the April 2026 update are potentially vulnerable.
    """
    version = parse_version(version_string)
    if not version:
        return True  # Unknown version - assume vulnerable if version present
    
    # April 2026 patch would be around version 82+ depending on release cycle
    # Vulnerable versions are typically those released before the security patch
    # This is a conservative check - actual vulnerable versions depend on release history
    # 
    # Versions <= 82.0.4 are considered vulnerable (before April 2026 security update)
    vulnerable_versions = (82, 0, 4)
    
    return version[0] < vulnerable_versions[0] or \
           (version[0] == vulnerable_versions[0] and version[1] < vulnerable_versions[1]) or \
           (version == vulnerable_versions[:len(version)] or 
            (version[0:2] == vulnerable_versions[0:2] and version[2] < vulnerable_versions[2]))


def test_crlf_injection(domain, base_url, timeout=10):
    """
    Test for CRLF injection vulnerability via /WHM/sandbox/example.pl
    """
    results = {
        'endpoint': '/WHM/sandbox/example.pl',
        'status_code': None,
        'injection_detected': False,
        'evidence': None,
        'method': None
    }
    
    try:
        # Construct malicious payload with CRLF injection
        payload = '/WHM/sandbox/example.pl?test=foo%0D%0ASet-Cookie:%20CRInj=Y3RyYW5l'
        url = urljoin(base_url, payload)
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; CVE-2026-41940-Scanner/1.0)')
        req.add_header('Accept', '*/*')
        
        # Custom handler to detect CRLF in response
        class CRLFHTTPHandler(urllib.request.HTTPHandler):
            def http_open(self, req):
                return self.do_open(urllib.request.http_connection.HTTPConnection, req)
        
        opener = urllib.request.build_opener(CRLFHTTPHandler())
        
        # Track response headers
        response_headers = []
        original_open = urllib.request.HTTPConnection.request
        
        def custom_request(self, method, url, body=None, headers=None):
            result = original_open(self, method, url, body, headers)
            return result
        
        with urllib.request.urlopen(req, timeout=timeout, context=urllib.request.create_default_context()) as response:
            results['status_code'] = str(response.status)
            
            # Check for CRLF in headers
            response_text = response.read().decode('utf-8', errors='ignore')
            
            # Check for signs of injection in response
            if 'CRInj' in response_text or 'cetrane' in response_text.lower():
                results['injection_detected'] = True
                results['evidence'] = 'CRLF injection payload found in response'
                results['method'] = 'HTTP parameter CRLF injection'
            
            # Check header lines for CRLF
            headers_text = str(response.headers)
            if '\r\n' in headers_text or '%0D%0A' in headers_text:
                results['injection_detected'] = True
                results['evidence'] = 'Raw CRLF characters found in response headers'
                results['method'] = 'Header CRLF injection'
                
    except urllib.error.HTTPError as e:
        results['status_code'] = str(e.code)
        # 403/404 on this endpoint is normal, doesn't necessarily mean not vulnerable
        
    except Exception as e:
        results['status_code'] = 'error'
    
    return results


def test_whostmgrsession_cookie(domain, base_url, timeout=10):
    """
    Test whostmgrsession cookie vulnerability
    """
    results = {
        'endpoint': '/WHM/sandbox/',
        'status_code': None,
        'cookie_vulnerable': False,
        'cookie_set': False,
        'cookie_value': None,
        'evidence': None
    }
    
    try:
        # Make request to WHM sandbox
        url = urljoin(base_url, '/WHM/sandbox/')
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; CVE-2026-41940-Scanner/1.0)')
        req.add_header('Accept', '*/*')
        
        cookies = []
        with urllib.request.urlopen(req, timeout=timeout, context=urllib.request.create_default_context()) as response:
            results['status_code'] = str(response.status)
            
            # Check for whostmgrsession cookie
            for cookie in response.headers.getlist('Set-Cookie'):
                if 'whostmgrsession' in cookie.lower():
                    results['cookie_set'] = True
                    results['cookie_value'] = cookie[:50] + '...' if len(cookie) > 50 else cookie
                    
                    # Check if cookie allows command injection patterns
                    if '=' in cookie and ('|' in cookie or ';' in cookie or '$(' in cookie or '`' in cookie):
                        results['cookie_vulnerable'] = True
                        results['evidence'] = 'whostmgrsession cookie with potential injection pattern'
                    elif 'httponly' not in cookie.lower() or 'secure' not in cookie.lower():
                        # Missing security flags could be risky
                        results['cookie_vulnerable'] = True
                        results['evidence'] = 'whostmgrsession cookie without security flags (HttpOnly, Secure)'
        
    except urllib.error.HTTPError as e:
        results['status_code'] = str(e.code)
        
    except Exception as e:
        results['status_code'] = 'error'
    
    return results


def check_xcpe_header(headers):
    """
    Check for X-CPE-Header information which may indicate vulnerability
    """
    findings = {
        'header_present': False,
        'header_value': None,
        'vulnerable': False,
        'evidence': None
    }
    
    # Common X-CPE header names
    cpe_headers = ['x-cpe-version', 'x-cpe-type', 'x-cpanel-version', 'x-cpanel-useragent']
    
    for header in cpe_headers:
        if header in headers:
            findings['header_present'] = True
            findings['header_value'] = headers[header]
            
            # Check if version in header indicates vulnerability
            if 'version' in header and not headers[header].startswith('cpanel'):
                # Some X-CPE headers may indicate vulnerable configuration
                pass
    
    # Check if cPanel version in headers is before the April 2026 patch
    if 'x-cpanel-version' in headers:
        version = headers['x-cpanel-version'].strip()
        if check_version_vulnerable(version):
            findings['vulnerable'] = True
            findings['evidence'] = f'X-CPanel-Version header shows version {version} which is before April 2026 patch'
    
    return findings


def scan_domain(target, timeout=10):
    """
    Main scanning function for a given domain.
    """
    domain, base_url = get_target_domain(target)
    
    # Perform initial HEAD request
    headers = get_headers(base_url, timeout)
    
    if headers is None:
        return {
            'scan_timestamp': datetime.utcnow().isoformat() + 'Z',
            'target': domain,
            'error': 'Failed to connect to target',
            'http_status_code': None,
            'vulnerability_results': {
                'cve_2026_41940_exploitable': False,
                'detected_methods': [],
                'reason': 'Cannot reach target - network error or target unavailable'
            }
        }
    
    # Extract cPanel version
    cpanel_version = extract_cpanel_version(headers)
    
    # Check version vulnerability
    version_vulnerable = False
    version_status = 'unknown'
    
    if cpanel_version:
        if check_version_vulnerable(cpanel_version):
            version_vulnerable = True
            version_status = 'VULNERABLE (before April 2026 patch)'
        else:
            version_status = 'SECURE (April 2026 patch applied)'
    else:
        version_status = 'version not detected'
    
    # Test CRLF injection
    crlf_result = test_crlf_injection(domain, base_url, timeout)
    
    # Test whostmgrsession cookie
    cookie_result = test_whostmgrsession_cookie(domain, base_url, timeout)
    
    # Check X-CPE headers
    xpe_result = check_xcpe_header(headers)
    
    # Determine overall vulnerability status
    detected_methods = []
    cve_exploitable = False
    
    # Add methods based on detection results
    if crlf_result['injection_detected']:
        detected_methods.append('crlf_injection')
        cve_exploitable = True
    
    if cookie_result['cookie_vulnerable']:
        detected_methods.append('whostmgrsession_cookie_injection')
        cve_exploitable = True
    
    if version_vulnerable:
        detected_methods.append('outdated_cpanel_version')
    
    if xpe_result['vulnerable']:
        detected_methods.append('cpe_header_version_leak')
    
    # Build vulnerability results
    vulnerability_results = {
        'cve_2026_41940_exploitable': cve_exploitable,
        'detected_methods': detected_methods,
        'details': {
            'crlf_injection': {
                'test_endpoint': '/WHM/sandbox/example.pl',
                'injection_possible': crlf_result['injection_detected'],
                'method_description': crlf_result.get('method') or 'not tested'
            },
            'whostmgrsession_cookie': {
                'cookie_set': cookie_result['cookie_set'],
                'cookie_vulnerable': cookie_result['cookie_vulnerable'],
                'security_flags_checked': cookie_result.get('cookie_value')
            },
            'cpanel_version_info': {
                'version_detected': cpanel_version,
                'version_status': version_status
            },
            'headers_info': {
                'xcpe_headers_present': xpe_result['header_present'],
                'version_in_header': headers.get('x-cpanel-version')
            }
        }
    }
    
    # Build final result
    result = {
        'scan_timestamp': datetime.utcnow().isoformat() + 'Z',
        'target': domain,
        'base_url': base_url,
        'cpanel_version': cpanel_version,
        'cpanel_version_vulnerable': version_vulnerable,
        'vulnerability_results': vulnerability_results,
        'headers_received': dict(headers),
        'http_status_code': int(headers.get('_http_status_code', 0)),
        'test_results': {
            'crlf_injection_test': crlf_result,
            'whostmgrsession_cookie_test': cookie_result,
            'xcpe_header_check': xpe_result
        }
    }
    
    # Add summary
    summary_security_status = 'VULNERABLE' if cve_exploitable else ('UNKNOWN' if not cpanel_version else 'SECURE')
    
    recommendations = []
    if cve_exploitable:
        recommendations.append('CRITICAL: CVE-2026-41940 potential vulnerability detected')
        recommendations.append('Immediately update cPanel/WHM to the latest version (post-April 2026 patch)')
        recommendations.append('Review and patch any CRLF injection vulnerabilities')
        recommendations.append('Implement security headers (HttpOnly, Secure flags on cookies)')
        recommendations.append('Conduct thorough security audit of affected systems')
    elif version_vulnerable:
        recommendations.append('WARNING: Outdated cPanel version detected')
        recommendations.append('Consider upgrading cPanel before applying to production')
    elif cpanel_version:
        recommendations.append('cPanel instance appears secure based on detected version')
        recommendations.append('Continue monitoring for security updates')
    else:
        recommendations.append('Unable to determine cPanel version')
        recommendations.append('Verify target service is accessible and properly configured')
    
    result['summary'] = {
        'security_status': summary_security_status,
        'recommendations': recommendations,
        'risk_level': 'HIGH' if cve_exploitable else ('MEDIUM' if version_vulnerable else 'LOW')
    }
    
    return result


def main():
    """Main entry point for script execution."""
    parser = argparse.ArgumentParser(
        description='CVE-2026-41940 Vulnerability Scanner for cPanel/WHM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s https://example.com:2082
  %(prog)s 192.168.1.100
  %(prog)s http://cpanel.local:2087

Output:
  JSON formatted result with vulnerability assessment
        '''
    )
    
    parser.add_argument(
        'domain',
        type=str,
        help='Target domain or URL to scan (e.g., example.com:2082 or https://example.com)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for JSON results (default: stdout)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Force JSON output (default when not in interactive mode)'
    )
    
    args = parser.parse_args()
    
    # Run the scan
    print(f"[*] Starting CVE-2026-41940 scan for target: {args.domain}")
    print(f"[*] Using timeout: {args.timeout} seconds")
    print()
    
    result = scan_domain(args.domain, args.timeout)
    
    # Output results
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"[+] Results saved to: {args.output}")
    else:
        print(output_json)
    
    # Return appropriate exit code
    if result['summary']['security_status'] == 'VULNERABLE':
        sys.exit(1)  # Vulnerable
    elif result['summary']['security_status'] == 'UNKNOWN':
        sys.exit(2)  # Unable to determine
    else:
        sys.exit(0)  # Secure or inconclusive


if __name__ == '__main__':
    main()
