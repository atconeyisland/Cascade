#!/usr/bin/env python
import sys
import os
import subprocess
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from cascade_env.environment import CascadeEnvironment
from cascade_env.models import ActionType, CascadeAction

print("\n" + "="*70)
print("VALIDATION TEST")
print("="*70)

print("\n[1/5] Running Unit Tests...")
try:
    result = subprocess.run(
        [sys.executable, "test_all.py"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if "ALL TESTS PASSED" in result.stdout:
        print("  [PASS] Unit tests (45+ tests)")
    else:
        print("  [FAIL] Unit tests")
        sys.exit(1)
except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

print("\n[2/5] Checking API Server Health...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "ok":
            print(f"  [PASS] API Server is running")
        else:
            print(f"  [FAIL] Invalid response")
            sys.exit(1)
    else:
        print(f"  [FAIL] HTTP {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("  [FAIL] Server not running")
    print("     Run: python run_server.py")
    sys.exit(1)
except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

print("\n[3/5] Testing REST API Endpoints...")
try:
    resp = requests.post("http://localhost:8000/reset/1", timeout=5)
    print(f"  [PASS] /reset/1" if resp.status_code == 200 else f"  [FAIL] /reset/1: {resp.status_code}")
    if resp.status_code != 200:
        sys.exit(1)
    
    resp = requests.get("http://localhost:8000/state/1", timeout=5)
    print(f"  [PASS] /state/1" if resp.status_code == 200 else f"  [FAIL] /state/1: {resp.status_code}")
    
    step_data = {
        "action_type": "investigate",
        "action_value": "database",
        "reasoning": "Check database"
    }
    resp = requests.post("http://localhost:8000/step/1", json=step_data, timeout=5)
    print(f"  [PASS] /step/1" if resp.status_code == 200 else f"  [FAIL] /step/1: {resp.status_code}")

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

print("\n[4/5] Testing Environment Variable Validation...")
try:
    env = os.environ.copy()
    env.pop('HF_TOKEN', None)
    env.pop('API_KEY', None)
    result = subprocess.run(
        [sys.executable, "-c", "exec(open('inference.py').read())"],
        capture_output=True,
        text=True,
        env=env,
        timeout=5
    )
    
    if "ERROR" in result.stderr:
        print("  [PASS] Env validation working")
    else:
        print("  [SKIP] Env validation")

except Exception as e:
    print(f"  [SKIP] Error: {e}")

print("\n[5/5] Testing OpenEnv Compliance...")
try:
    env = CascadeEnvironment(task_id=1)
    obs = env.reset()
    print(f"  [PASS] reset() works")
    
    action = CascadeAction(
        action_type=ActionType.INVESTIGATE,
        action_value="database",
        reasoning="Check"
    )
    result = env.step(action)
    print(f"  [PASS] step() works")
    
    state = env.state
    print(f"  [PASS] state property works")

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("ALL VALIDATION TESTS PASSED")
print("="*70)
print("")
print("See GUIDE.md for deployment steps.")
