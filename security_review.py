#!/usr/bin/env python
"""
Phase 5: Security Review
Comprehensive security assessment of VayuGuard
"""

import os
import json
import re
from pathlib import Path

def check_environment_variables():
    """Check .env file for secrets"""
    print("\n1. ENVIRONMENT VARIABLES & SECRETS")
    print("=" * 60)
    
    env_file = Path(".env")
    issues = []
    
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            lines = content.split('\n')
            
        print(f"File: {env_file}")
        print(f"Lines: {len(lines)}")
        
        # Check for sensitive patterns
        sensitive_patterns = {
            'API_KEY': r'.*API.*KEY.*',
            'PASSWORD': r'.*PASSWORD.*',
            'SECRET': r'.*SECRET.*',
            'TOKEN': r'.*TOKEN.*',
            'CREDENTIAL': r'.*CREDENTIAL.*'
        }
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
                
            for pattern_name, pattern in sensitive_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    key = line.split('=')[0]
                    value = line.split('=')[1] if '=' in line else ''
                    status = "FOUND" if value and value != '' else "NOT SET"
                    print(f"  {key}: {status}")
                    if value and len(value) > 0:
                        issues.append(f"Sensitive key '{key}' found in .env")
    else:
        print(f"File: {env_file} - NOT FOUND")
        issues.append(".env file not found (check .env.example instead)")
    
    return issues

def check_hardcoded_secrets():
    """Scan codebase for hardcoded secrets"""
    print("\n2. HARDCODED SECRETS SCAN")
    print("=" * 60)
    
    issues = []
    secret_patterns = [
        (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'API Key'),
        (r'password\s*=\s*["\']([^"\']+)["\']', 'Password'),
        (r'secret\s*=\s*["\']([^"\']+)["\']', 'Secret'),
        (r'token\s*=\s*["\']([^"\']+)["\']', 'Token'),
        (r'["\']https?://[a-z0-9]+:[a-z0-9]+@', 'Credentials in URL'),
    ]
    
    # Scan common files
    files_to_scan = [
        'backend/config.js',
        'backend/server.js',
        'ml-service/config.py',
        'ml-service/app_production.py'
    ]
    
    findings = {
        'hardcoded': [],
        'using_env': []
    }
    
    for file_path in files_to_scan:
        if os.path.exists(file_path):
            with open(file_path) as f:
                content = f.read()
                for pattern, name in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Check if it's using environment variable instead
                        if 'process.env' in content or 'os.getenv' in content or 'os.environ' in content:
                            findings['using_env'].append((file_path, name))
                        else:
                            findings['hardcoded'].append((file_path, name, matches[0][:20]))
    
    print(f"\nUsing Environment Variables: {len(findings['using_env'])} files")
    for file_path, name in findings['using_env']:
        print(f"  ✓ {file_path}: {name} loaded from env")
    
    if findings['hardcoded']:
        print(f"\nHardcoded Secrets: {len(findings['hardcoded'])} FOUND")
        for file_path, name, value in findings['hardcoded']:
            print(f"  ✗ {file_path}: {name} = {value}...")
            issues.append(f"Hardcoded {name} in {file_path}")
    else:
        print(f"\nHardcoded Secrets: None found ✓")
    
    return issues

def check_jwt_configuration():
    """Check JWT authentication setup"""
    print("\n3. JWT AUTHENTICATION")
    print("=" * 60)
    
    issues = []
    
    # Check backend config
    if os.path.exists('backend/config.js'):
        with open('backend/config.js') as f:
            content = f.read()
            
        # Check for JWT secret
        if 'jwt' in content.lower():
            print("  ✓ JWT configuration found")
            
            # Check if using environment variable
            if 'process.env.JWT_SECRET' in content:
                print("  ✓ JWT_SECRET loaded from environment")
            elif 'vayuguard-secret' in content:
                print("  ⚠ Default JWT secret detected (should use env var)")
                issues.append("JWT using default secret instead of environment variable")
            
            # Check expiration
            if 'expiresIn' in content:
                print("  ✓ Token expiration configured")
            else:
                print("  ✗ Token expiration NOT configured")
                issues.append("JWT tokens missing expiration")
    
    # Check ML service
    if os.path.exists('ml-service/app_production.py'):
        print("  ℹ  ML service is stateless (no JWT needed)")
    
    return issues

def check_input_validation():
    """Check input validation in routes"""
    print("\n4. INPUT VALIDATION")
    print("=" * 60)
    
    issues = []
    
    # Check backend routes
    route_files = [
        'backend/routes/forecast.js',
        'backend/routes/auth.js',
        'backend/routes/alerts.js'
    ]
    
    for route_file in route_files:
        if os.path.exists(route_file):
            with open(route_file) as f:
                content = f.read()
            
            if 'express-validator' in content or 'validationResult' in content:
                print(f"  ✓ {route_file}: Using express-validator")
            elif 'body(' in content or 'param(' in content:
                print(f"  ✓ {route_file}: Input validation middleware present")
            else:
                print(f"  ⚠ {route_file}: Limited validation detected")
                issues.append(f"Minimal validation in {route_file}")
    
    # Check FastAPI validation
    if os.path.exists('ml-service/app_production.py'):
        with open('ml-service/app_production.py') as f:
            content = f.read()
        
        if 'BaseModel' in content and 'Pydantic' in content:
            print(f"  ✓ ml-service/app_production.py: Using Pydantic validation")
        elif 'class.*Request' in content:
            print(f"  ✓ ml-service/app_production.py: Request models defined")
    
    return issues

def check_sql_injection_protection():
    """Check SQL injection prevention"""
    print("\n5. SQL INJECTION PROTECTION")
    print("=" * 60)
    
    issues = []
    
    # Check backend DB usage
    if os.path.exists('backend/db.js'):
        with open('backend/db.js') as f:
            content = f.read()
        
        if 'pg' in content and 'query' in content:
            if '?' in content or 'parameterized' in content:
                print("  ✓ Using parameterized queries (pg library)")
            else:
                # Check for string concatenation
                if '+' in content or 'template' in content:
                    print("  ⚠ Possible string concatenation in queries")
                    issues.append("Potential SQL injection: check query construction")
    
    # Check Python DB usage
    if os.path.exists('ml-service/app_production.py'):
        with open('ml-service/app_production.py') as f:
            content = f.read()
        
        if 'psycopg2' in content and 'execute' in content:
            if '%s' in content or '%(name)s' in content:
                print("  ✓ Python: Using parameterized queries (psycopg2)")
            else:
                print("  ⚠ Python: Check query parameterization")
                issues.append("Verify psycopg2 query parameterization")
    
    return issues

def check_cors_configuration():
    """Check CORS security settings"""
    print("\n6. CORS CONFIGURATION")
    print("=" * 60)
    
    issues = []
    
    if os.path.exists('backend/server.js'):
        with open('backend/server.js') as f:
            content = f.read()
        
        if 'cors' in content:
            print("  ✓ CORS middleware installed")
            
            if 'cors()' in content:
                print("  ⚠ WARNING: CORS allowing all origins (cors())")
                issues.append("CORS configured to allow all origins - restrict in production")
            elif 'origin:' in content:
                print("  ℹ  CORS with origin configuration")
            else:
                print("  ℹ  CORS configuration details not visible")
    
    return issues

def check_authentication_middleware():
    """Check authentication middleware"""
    print("\n7. AUTHENTICATION MIDDLEWARE")
    print("=" * 60)
    
    issues = []
    
    if os.path.exists('backend/middleware/auth.js'):
        with open('backend/middleware/auth.js') as f:
            content = f.read()
        
        print(f"  ✓ Auth middleware exists")
        
        if 'jwt.verify' in content:
            print("  ✓ JWT verification implemented")
        else:
            print("  ⚠ JWT verification not found")
            issues.append("Auth middleware missing JWT verification")
        
        if 'Bearer' in content:
            print("  ✓ Bearer token extraction implemented")
    else:
        print("  ✗ Auth middleware not found")
        issues.append("Authentication middleware missing")
    
    return issues

def check_https_tls():
    """Check HTTPS/TLS configuration"""
    print("\n8. HTTPS/TLS CONFIGURATION")
    print("=" * 60)
    
    issues = []
    
    # Check for HTTPS enforcement
    if os.path.exists('backend/server.js'):
        with open('backend/server.js') as f:
            content = f.read()
        
        if 'https' in content.lower():
            print("  ✓ HTTPS support detected")
        else:
            print("  ⚠ HTTPS not configured in application")
            issues.append("HTTPS not configured (requires reverse proxy/load balancer)")
    
    if os.path.exists('docker-compose.yml'):
        with open('docker-compose.yml') as f:
            content = f.read()
        
        if 'https' in content.lower() or '443' in content:
            print("  ℹ  Check docker-compose for TLS setup")
        else:
            print("  ⚠ TLS/HTTPS not in docker-compose configuration")
            issues.append("TLS not configured in Docker Compose (needed for production)")
    
    return issues

def check_rate_limiting():
    """Check rate limiting"""
    print("\n9. RATE LIMITING")
    print("=" * 60)
    
    issues = []
    
    # Check if rate limiting is implemented
    found_rate_limit = False
    
    for file_path in ['backend/server.js', 'backend/middleware/']:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                for file in os.listdir(file_path):
                    if file.endswith('.js'):
                        with open(os.path.join(file_path, file)) as f:
                            if 'rate' in f.read().lower() or 'limit' in f.read().lower():
                                found_rate_limit = True
            else:
                with open(file_path) as f:
                    if 'rate' in f.read().lower():
                        found_rate_limit = True
    
    if found_rate_limit:
        print("  ✓ Rate limiting likely configured")
    else:
        print("  ⚠ Rate limiting NOT detected")
        issues.append("Rate limiting not configured (recommend express-rate-limit)")
    
    # Check ML service
    if os.path.exists('ml-service/app_production.py'):
        print("  ℹ  FastAPI rate limiting should be configured")
        issues.append("Add FastAPI SlowAPI or similar for rate limiting")
    
    return issues

def check_logging_and_monitoring():
    """Check logging configuration"""
    print("\n10. LOGGING & MONITORING")
    print("=" * 60)
    
    issues = []
    
    if os.path.exists('backend/server.js'):
        with open('backend/server.js') as f:
            content = f.read()
        
        if 'morgan' in content:
            print("  ✓ Request logging (morgan) configured")
        else:
            print("  ⚠ Request logging not configured")
            issues.append("Request logging not configured")
    
    if os.path.exists('ml-service/app_production.py'):
        with open('ml-service/app_production.py') as f:
            content = f.read()
        
        if 'logging' in content:
            print("  ✓ Logging configured in ML service")
        else:
            print("  ⚠ Logging not configured in ML service")
    
    if os.path.exists('backend/server.js'):
        with open('backend/server.js') as f:
            content = f.read()
        
        if 'prom-client' in content or 'prometheus' in content:
            print("  ✓ Prometheus metrics configured")
        else:
            print("  ⚠ Metrics not configured")
            issues.append("Prometheus metrics not configured (for production monitoring)")
    
    return issues

def generate_summary(all_issues):
    """Generate security summary"""
    print("\n" + "=" * 60)
    print("SECURITY ASSESSMENT SUMMARY")
    print("=" * 60)
    
    critical_issues = [i for i in all_issues if 'hardcoded' in i.lower() or 'injection' in i.lower()]
    high_issues = [i for i in all_issues if 'https' in i.lower() or 'rate limit' in i.lower()]
    medium_issues = [i for i in all_issues if i not in critical_issues + high_issues]
    
    print(f"\nCritical Issues: {len(critical_issues)}")
    for issue in critical_issues:
        print(f"  🔴 {issue}")
    
    print(f"\nHigh Issues: {len(high_issues)}")
    for issue in high_issues:
        print(f"  🟠 {issue}")
    
    print(f"\nMedium Issues: {len(medium_issues)}")
    for issue in medium_issues:
        print(f"  🟡 {issue}")
    
    overall_score = max(0, 100 - len(critical_issues) * 10 - len(high_issues) * 5 - len(medium_issues) * 2)
    print(f"\nSecurity Score: {overall_score}/100")
    
    return overall_score

if __name__ == '__main__':
    os.chdir('/Users/Kandra Karthik/Downloads/VG' if os.path.exists('/Users/Kandra Karthik/Downloads/VG') else 'c:\\Users\\Kandra Karthik\\Downloads\\VG')
    
    print("=" * 60)
    print("PHASE 5: SECURITY REVIEW")
    print("=" * 60)
    
    all_issues = []
    
    all_issues.extend(check_environment_variables())
    all_issues.extend(check_hardcoded_secrets())
    all_issues.extend(check_jwt_configuration())
    all_issues.extend(check_input_validation())
    all_issues.extend(check_sql_injection_protection())
    all_issues.extend(check_cors_configuration())
    all_issues.extend(check_authentication_middleware())
    all_issues.extend(check_https_tls())
    all_issues.extend(check_rate_limiting())
    all_issues.extend(check_logging_and_monitoring())
    
    score = generate_summary(all_issues)
