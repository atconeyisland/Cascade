#!/usr/bin/env python3
"""
Simple test script to verify Cascade environment server is running.
Run this while the server is active to test basic functionality.

Usage:
    python test_client.py
"""

import sys
sys.path.insert(0, 'src')

from cascade_env.client import CascadeEnv
from cascade_env.models import CascadeAction, ActionType

def test_server():
    """Test basic server connectivity and functionality."""
    try:
        env = CascadeEnv(base_url="http://localhost:8000", timeout=5.0)
        
        print("✓ Connected to server at http://localhost:8000")
        health = env.health()
        print(f"✓ Health check: {health}")
        
        print("\n📋 Running Task 1 (Database CPU Spike)...")
        obs = env.reset(task_id=1)
        print(f"✓ Reset complete")
        print(f"  Alert: {obs.alert_message[:80]}...")
        print(f"  Services: {', '.join(obs.affected_services)}")
        print(f"  Priority: {obs.priority_level}")
        print(f"  Runbooks available: {', '.join(obs.available_runbooks)}")

        
        print("\n🔧 Taking action: Investigate database...")
        action = CascadeAction(
            action_type=ActionType.INVESTIGATE,
            action_value="database",
            reasoning="High CPU usage detected in logs"
        )
        result = env.step(action, task_id=1)
        print(f"✓ Step completed")
        print(f"  Reward: {result.reward:.2f}")
        print(f"  Done: {result.done}")
        print(f"  Info: {result.info}")
        
       
        print("\n🔧 Taking action: Select db-cpu-runbook...")
        action = CascadeAction(
            action_type=ActionType.SELECT_RUNBOOK,
            action_value="db-cpu-runbook",
            reasoning="Database CPU is the root cause"
        )
        result = env.step(action, task_id=1)
        print(f"✓ Step completed")
        print(f"  Reward: {result.reward:.2f}")
        print(f"  Episode progress: step {result.observation.current_step}/{env.get_state(task_id=1)['current_step']}")
        
        
        print("\n📊 Current state:")
        state = env.get_state(task_id=1)
        print(f"  Task ID: {state['task_id']}")
        print(f"  Current step: {state['current_step']}")
        print(f"  Episode done: {state['episode_done']}")
        print(f"  Accumulated reward: {state['accumulated_reward']:.2f}")
        
        print("\n✅ All tests passed! Server is working correctly.")
        print("\nTip: Now run 'python inference.py' to test with an LLM agent.")
        print("(Make sure to set HF_TOKEN and MODEL_NAME environment variables)")
        
        env.close()
        return True
        
    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nMake sure the server is running:")
        print("  powershell -Command \"$env:PYTHONPATH='src'; uvicorn server.app:app --reload --host 0.0.0.0 --port 8000\"")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
