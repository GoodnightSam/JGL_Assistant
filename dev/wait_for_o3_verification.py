import os
import time
from agents import Agent, Runner
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def check_o3_access():
    """Check if o3 model is accessible."""
    try:
        agent = Agent(
            name="TestAgent",
            model="o3-2025-04-16",
            instructions="You are a test agent."
        )
        result = Runner.run_sync(agent, "Say 'O3 access confirmed!'")
        return True, result.final_output
    except Exception as e:
        return False, str(e)

def wait_for_o3_verification(max_wait_minutes=15, check_interval_seconds=60):
    """
    Wait for o3 verification to propagate.
    
    Args:
        max_wait_minutes: Maximum time to wait in minutes
        check_interval_seconds: Time between checks in seconds
    """
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_count = 0
    
    print(f"Waiting for o3 verification to propagate...")
    print(f"Will check every {check_interval_seconds} seconds for up to {max_wait_minutes} minutes")
    print("-" * 60)
    
    while time.time() - start_time < max_wait_seconds:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\nCheck #{check_count} at {current_time}")
        
        success, message = check_o3_access()
        
        if success:
            print(f"✅ SUCCESS! O3 is now accessible!")
            print(f"Response: {message}")
            print(f"\nVerification completed after {int(time.time() - start_time)} seconds")
            return True
        else:
            if "must be verified" in message:
                elapsed = int(time.time() - start_time)
                print(f"⏳ Not yet propagated (elapsed: {elapsed}s)")
            else:
                print(f"❌ Unexpected error: {message[:200]}...")
        
        if time.time() - start_time + check_interval_seconds < max_wait_seconds:
            print(f"Waiting {check_interval_seconds} seconds before next check...")
            time.sleep(check_interval_seconds)
    
    print(f"\n❌ Timeout: Verification did not propagate within {max_wait_minutes} minutes")
    return False

if __name__ == "__main__":
    # Wait for up to 10 more minutes (since 5 have already passed)
    if wait_for_o3_verification(max_wait_minutes=10, check_interval_seconds=60):
        print("\n🎉 O3 model is ready to use!")
        print("You can now run: python dev/test_o3_script_generation.py")
    else:
        print("\n⚠️  Please check your organization verification status at:")
        print("https://platform.openai.com/settings/organization/general")