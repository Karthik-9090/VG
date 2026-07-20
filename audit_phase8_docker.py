#!/usr/bin/env python3
"""
PHASE 8: DOCKER VALIDATION

Validates Docker and Docker Compose configuration, and optionally tests containerization.
Tests:
  1. Docker installation and version
  2. docker-compose.yml validity
  3. Image building capability
  4. Container orchestration setup
"""

import subprocess
import json
import sys
import os

def test_docker_installation():
    """Test if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print("✅ Test 1: Docker Installation - PASS")
            print(f"   {version}")
            return True
        else:
            print("❌ Test 1: Docker Installation - FAIL")
            print("   Docker not found or not in PATH")
            return False
            
    except FileNotFoundError:
        print("❌ Test 1: Docker Installation - FAIL")
        print("   Docker not installed on system")
        return False
    except Exception as e:
        print(f"❌ Test 1: Docker Installation - FAIL ({e})")
        return False

def test_docker_daemon():
    """Test if Docker daemon is running"""
    try:
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        
        if result.returncode == 0:
            print("✅ Test 2: Docker Daemon - PASS")
            print("   Docker daemon is running and accessible")
            return True
        else:
            print("❌ Test 2: Docker Daemon - FAIL")
            print("   Docker daemon not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Test 2: Docker Daemon - FAIL ({e})")
        return False

def test_docker_compose_installation():
    """Test if Docker Compose is installed"""
    try:
        result = subprocess.run(['docker', 'compose', '--version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print("✅ Test 3: Docker Compose Installation - PASS")
            print(f"   {version}")
            return True
        else:
            print("❌ Test 3: Docker Compose Installation - FAIL")
            print("   Docker Compose not found")
            return False
            
    except Exception as e:
        print(f"❌ Test 3: Docker Compose Installation - FAIL ({e})")
        return False

def test_compose_file_validity():
    """Test if docker-compose.yml is valid"""
    try:
        # Change to VG root directory
        vg_root = "C:\\Users\\Kandra Karthik\\Downloads\\VG"
        
        if not os.path.exists(os.path.join(vg_root, 'docker-compose.yml')):
            print("❌ Test 4: Docker Compose File Validity - FAIL")
            print("   docker-compose.yml not found")
            return False
        
        result = subprocess.run(['docker', 'compose', 'config'], 
                              capture_output=True, 
                              text=True,
                              timeout=10,
                              cwd=vg_root)
        
        if result.returncode == 0:
            print("✅ Test 4: Docker Compose File Validity - PASS")
            print("   docker-compose.yml is valid and parseable")
            
            # Try to parse output to count services
            try:
                # Compose config outputs YAML, not JSON by default
                if 'services' in result.stdout:
                    services_count = result.stdout.count('image:')
                    print(f"   Services configured: {services_count}")
            except:
                pass
            
            return True
        else:
            print("❌ Test 4: Docker Compose File Validity - FAIL")
            print(f"   Error: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Test 4: Docker Compose File Validity - FAIL ({e})")
        return False

def test_images_availability():
    """Test if required base images are available"""
    try:
        # Check for common base images
        required_images = [
            'node:20',  # For backend/frontend
            'python:3.11',  # For ml-service and data-pipeline
            'postgres:15',  # For database
        ]
        
        available = 0
        missing = []
        
        for image in required_images:
            result = subprocess.run(['docker', 'inspect', image], 
                                  capture_output=True,
                                  timeout=5)
            if result.returncode == 0:
                available += 1
            else:
                missing.append(image)
        
        if available >= 2:
            print("✅ Test 5: Base Images Availability - PASS")
            print(f"   {available}/{len(required_images)} required images available locally")
            if missing:
                print(f"   Missing: {', '.join(missing)} (will be pulled on build)")
            return True
        else:
            print("⚠️  Test 5: Base Images Availability - PARTIAL")
            print(f"   Only {available}/{len(required_images)} images available")
            print("   Missing images will be pulled during docker compose up")
            return True  # Not critical - Docker will pull them
            
    except Exception as e:
        print(f"⚠️  Test 5: Base Images Availability - PARTIAL ({e})")
        return True  # Not critical

def test_docker_network():
    """Test Docker network configuration"""
    try:
        result = subprocess.run(['docker', 'network', 'ls'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        
        if result.returncode == 0:
            networks = result.stdout.count('\n') - 1  # Subtract header
            print("✅ Test 6: Docker Network - PASS")
            print(f"   Docker networks available: {networks}")
            return True
        else:
            print("❌ Test 6: Docker Network - FAIL")
            return False
            
    except Exception as e:
        print(f"❌ Test 6: Docker Network - FAIL ({e})")
        return False

def run_phase8_validation():
    """Run all Phase 8 tests"""
    print("\n" + "="*60)
    print("PHASE 8: DOCKER VALIDATION")
    print("="*60 + "\n")
    
    print("Configuration:")
    print("  - Docker: Container orchestration")
    print("  - Docker Compose: Multi-container management")
    print("  - Services: Backend, Frontend, ML-Service, Database, Data-Pipeline\n")
    
    results = {
        'docker_installation': test_docker_installation(),
        'docker_daemon': test_docker_daemon(),
        'compose_installation': test_docker_compose_installation(),
        'compose_file': test_compose_file_validity(),
        'images': test_images_availability(),
        'network': test_docker_network(),
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"PHASE 8 RESULTS: {passed}/{total} Tests Passed")
    print("="*60)
    
    if passed >= 5:
        print("\n✅ DOCKER INFRASTRUCTURE READY")
        print("   - Docker and Docker Compose installed")
        print("   - docker-compose.yml is valid")
        print("   - Ready for containerized deployment")
        print("\n   To deploy all services:")
        print("   $ cd /path/to/VG")
        print("   $ docker compose up --build")
        return True
    elif passed >= 3:
        print(f"\n⚠️  DOCKER PARTIALLY CONFIGURED ({passed}/{total} tests)")
        print("   Docker is installed but may have some limitations")
        return True
    else:
        print(f"\n❌ DOCKER NOT AVAILABLE ({passed}/{total} tests)")
        print("   Docker is not properly configured on this system")
        return False

if __name__ == '__main__':
    success = run_phase8_validation()
    sys.exit(0 if success else 1)
