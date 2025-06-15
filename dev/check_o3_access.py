import os
from agents import Agent, Runner
from dotenv import load_dotenv
import time

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

print("Checking o3 model access...")
success, message = check_o3_access()

if success:
    print(f"✅ SUCCESS! O3 is now accessible!")
    print(f"Response: {message}")
else:
    if "must be verified" in message:
        print(f"❌ Organization verification not yet propagated")
        print(f"Error: {message[:200]}...")
    else:
        print(f"❌ Error: {message}")