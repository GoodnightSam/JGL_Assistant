from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("Checking available models...")
print("=" * 60)

try:
    models = client.models.list()
    
    # Filter for relevant models
    relevant_models = []
    for model in models:
        if any(keyword in model.id.lower() for keyword in ['gpt', 'o3', 'o1']):
            relevant_models.append(model.id)
    
    # Sort and display
    relevant_models.sort()
    print(f"Found {len(relevant_models)} relevant models:")
    for model in relevant_models:
        print(f"  - {model}")
        
except Exception as e:
    print(f"Error: {e}")