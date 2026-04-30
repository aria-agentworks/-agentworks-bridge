#!/usr/bin/env python3
"""
Aria-Ghost Security Header Fingerprinting Tool

Perform non-intrusive security header analysis on target domains.
Part of the Aria Security Platform infrastructure visibility suite.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
from requests.exceptions import (
    DNSLookupError,
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException
)

# Configure logging
LOG_FILE = "fingerprint_results.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# Security headers to extract
SECURITY_HEADERS = [
    "Server",
    "X-Powered-By",
    "ORACLE_EBS_VERSION",
    "X-Oracle-Version",
    "X-Frame-Options",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "Cache-Control",
    "X-Content-Security-Policy",
    "X-WebKit-CSP",
    "P3P"
]

DEFAULT_USER_AGENT = "Aria-Ghost-Fingerprinting/1.0 (Infrastructure Security Scanner)"


def load_domains_from_file(file_path: str) -> List[str]:
    """Load target domains from a file, one per line."""
    domains = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Domain file not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith(("http://", "https://")):
                    from urllib.parse import urlparse
                    domain = urlparse(line).netloc
                    if domain:
                        domains.append(domain)
                else:
                    domains.append(line)
    
    return domains


def sanitize_domain(domain: str) -> str:
    """Sanitize domain string and ensure protocol."""
    domain = domain.strip()
    
    if domain.startswith("http://") or domain.startswith("https://"):
        from urllib.parse import urlparse
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    return f"https://{domain}"


def fetch_security_headers(domain: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch HTTP response headers for a target domain."""
    result = {
        "target": domain,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status_code": None,
        "headers": {},
        "security_headers": {},
        "errors": [],
        "success": False
    }
    
    sanitized_domain = sanitize_domain(domain)
    
    try:
        head_response = requests.head(
            sanitized_domain,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
            verify=True
        )
        
        if head_response.status_code >= 400:
            get_response = requests.get(
                sanitized_domain,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                timeout=timeout,
                allow_redirects=True,
                verify=True
            )
            response = get_response
        else:
            response = head_response
        
        result["status_code"] = response.status_code
        result["success"] = 200 <= response.status_code < 400
        result["headers"] = dict(response.headers)
        
        for header in SECURITY_HEADERS:
            if header in response.headers:
                result["security_headers"][header] = response.headers[header]
        
        logger.info(
            f"Successfully scanned {domain}: "
            f"Status {response.status_code}, "
            f"{len(result['security_headers'])} security headers found"
        )
        
        return result
        
    except DNSLookupError as e:
        error_msg = f"DNS lookup failed for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
        return result
        
    except Timeout as e:
        error_msg = f"Connection timeout for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
        return result
        
    except ConnectionError as e:
        error_msg = f"Connection error for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
        return result
        
    except HTTPError as e:
        error_msg = f"HTTP error for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.warning(error_msg)
        result["status_code"] = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0
        return result
        
    except RequestException as e:
        error_msg = f"Request exception for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error for {domain}: {str(e)}"
        result["errors"].append(error_msg)
        logger.exception(error_msg)
        return result


def scan_domain(domain: str, timeout: int = 10) -> Dict[str, Any]:
    """Wrapper for fetch_security_headers with consistent output."""
    return fetch_security_headers(domain, timeout)


def scan_multiple(domains: List[str], timeout: int = 10) -> List[Dict[str, Any]]:
    """Scan multiple domains and return results."""
    results = []
    for domain in domains:
        result = scan_domain(domain, timeout)
        results.append(result)
    return results


def print_json_result(results: List[Dict[str, Any]], pretty: bool = True):
    """Print results as JSON to stdout."""
    output = json.dumps(
        {"results": results, "scan_summary": {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success"))
        }},
        indent=2 if pretty else None,
        ensure_ascii=False
    )
    print(output)


def generate_scan_summary(results: List[Dict[str, Any]]) -> str:
    """Generate a human-readable summary of scan results."""
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    
    summary_lines = [
        "=" * 60,
        "SCAN SUMMARY",
        "=" * 60,
        f"Total Domains Scanned: {len(results)}",
        f"Successful: {successful}",
        f"Failed: {failed}",
        "=" * 60
    ]
    
    domains_with_issues = []
    for r in results:
        if not r.get("errors"):
            missing = set(SECURITY_HEADERS) - set(r.get("security_headers", {}).keys())
            critical = [h for h in ["Strict-Transport-Security", "X-Frame-Options"] if h in missing]
            if critical:
                domains_with_issues.append(r["target"])
    
    if domains_with_issues:
        summary_lines.append("")
        summary_lines.append("Critical Security Headers Missing:")
        for domain in domains_with_issues:
            summary_lines.append(f"  - {domain}")
    
    summary_lines.append("=" * 60)
    
    return "\n".join(summary_lines)


def main():
    """Main entry point for the fingerprinting tool."""
    parser = argparse.ArgumentParser(
        description="Aria-Ghost Security Header Fingerprinting Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s example.com api.example.com
  %(prog)s -f targets.txt
  %(prog)s --json --timeout 15 example.com

Security headers monitored:
  %(prog)s --list-headers
        """
    )
    
    parser.add_argument(
        "domains",
        nargs="*",
        help="Target domains or URLs to scan"
    )
    
    parser.add_argument(
        "-f", "--file",
        help="File containing domains (one per line)"
    )
    
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        help="Disable pretty-printing of JSON output"
    )
    
    parser.add_argument(
        "--list-headers",
        action="store_true",
        help="List all monitored security headers and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.list_headers:
        print("Monitored Security Headers:")
        for i, header in enumerate(SECURITY_HEADERS, 1):
            print(f"  {i:2d}. {header}")
        return 0
    
    domains = []
    
    if args.domains:
        domains.extend(args.domains)
    
    if args.file:
        try:
            file_domains = load_domains_from_file(args.file)
            domains.extend(file_domains)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading domain file: {e}", file=sys.stderr)
            return 1
    
    if not domains:
        parser.print_help()
        print("\nError: No domains to scan. Provide domains as arguments or use -f/--file", file=sys.stderr)
        return 1
    
    domains = sorted(set(domains))
    
    print(f"Aria-Ghost Security Header Fingerprinting")
    print(f"Scan started at: {datetime.utcnow().isoformat()}Z")
    print(f"Scanning {len(domains)} domain(s)...\n")
    
    results = scan_multiple(domains, args.timeout)
    
    print_json_result(results, not args.no_pretty)
    
    logger.info(generate_scan_summary(results))
    
    exit_code = 1 if any(not r.get("success") for r in results) else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())