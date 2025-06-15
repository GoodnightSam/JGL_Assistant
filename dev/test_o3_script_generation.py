import os
from agents import Agent, Runner
from typing import Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# o3 Model Information (June 2025)
# o3 pricing: $2/1M input tokens, $8/1M output tokens
# Model name: "o3-2025-04-16"
# Requires organization verification

# Script generation prompt template
SCRIPT_PROMPT_TEMPLATE = """You are writing a 5-minute biography video for **{actor_name}**.

GLOBAL RULES  
• 780–830 words (≈5 min @ 155 wpm).  
• Action beats in historical-present; context may use past but never mix tenses in one sentence.  
• Voice = confident "sports-doc storyteller": punchy, nostalgic, dry-witty; no Gen-Z slang.  
• ≥ 8 explicit year stamps inside the narration; mention the actor's age at least twice.  
• Around the 80–90-second mark, drop a short tension-raising **question**—ask it plainly; never label it.  
• Weave one humorous callback in each later act.  
• **Output only the words the narrator speaks**—no outros, CTAs, visuals, music cues, section headers, timelines, or tables.

OUTPUT MARKDOWN FORMAT (exactly):  

**{actor_name} — 5-MINUTE BIO SCRIPT (~XXX words)**  

**HOOK**  
Fragment. Fragment. Fragment. And [surprise facet].  
{actor_name}'s [metaphor or superlative tied to a signature role]. **[Imperative callback, 2–4 words—verb-first, no pronouns], and let's get rollin'.**

**BIO**  
(Full narration here in continuous paragraphs—birth to present-day epilogue. No additional headings.)"""


class O3ScriptGenerator:
    """
    A class to handle script generation using OpenAI's o3 model.
    """
    
    def __init__(self):
        """Initialize the script generator with o3 model."""
        self.model_name = "o3-2025-04-16"  # Official o3 model
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the script writing agent with o3."""
        return Agent(
            name="O3ScriptWriter",
            model=self.model_name,
            instructions="You are an expert biography script writer for YouTube videos. Follow the exact formatting and rules provided in each request."
        )
    
    def generate_script(self, actor_name: str) -> Dict[str, Any]:
        """
        Generate a biography script for the given actor using o3.
        
        Args:
            actor_name: Name of the actor to write about
            
        Returns:
            Dictionary containing the script and metadata
        """
        prompt = SCRIPT_PROMPT_TEMPLATE.format(actor_name=actor_name)
        
        try:
            result = Runner.run_sync(self.agent, prompt)
            
            # Parse the output to extract sections
            output = result.final_output
            script_data = {
                "actor_name": actor_name,
                "full_script": output,
                "word_count": len(output.split()),
                "model_used": self.model_name,
                "success": True
            }
            
            # Try to extract hook and bio sections
            if "**HOOK**" in output and "**BIO**" in output:
                parts = output.split("**BIO**")
                hook_section = parts[0].split("**HOOK**")[1].strip() if "**HOOK**" in parts[0] else ""
                bio_section = parts[1].strip() if len(parts) > 1 else ""
                
                script_data["hook"] = hook_section
                script_data["bio"] = bio_section
            
            return script_data
            
        except Exception as e:
            return {
                "actor_name": actor_name,
                "error": str(e),
                "success": False,
                "model_used": self.model_name
            }
    
    def estimate_cost(self, script_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate the API cost for the script generation.
        
        Based on June 2025 pricing:
        - o3: $2/1M input tokens, $8/1M output tokens
        
        Returns:
            Dictionary with cost breakdown
        """
        # Rough token estimates
        input_tokens = 285  # Prompt template + actor name
        output_tokens = script_data.get("word_count", 800) * 1.5  # ~1.5 tokens per word
        
        # o3 pricing
        input_price = 2.0  # $2 per 1M input tokens
        output_price = 8.0  # $8 per 1M output tokens
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "total_cost_usd": f"${total_cost:.4f}"
        }


def test_o3_script_generation():
    """
    Test script generation with the o3 model.
    """
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    print("Testing OpenAI o3 Script Generation")
    print("=" * 60)
    print("Model: o3-2025-04-16")
    print("Pricing: $2/1M input tokens, $8/1M output tokens")
    print("Note: Requires organization verification")
    print("=" * 60)
    
    # Test configuration - start with one actor for o3 testing
    test_actors = ["Tom Hanks"]
    
    # Initialize generator with o3
    print("\nInitializing o3 Script Generator...")
    generator = O3ScriptGenerator()
    
    successful_scripts = 0
    total_cost = 0
    
    for actor in test_actors:
        print(f"\nGenerating script for: {actor}")
        print("-" * 40)
        
        # Generate script
        result = generator.generate_script(actor)
        
        if result["success"]:
            successful_scripts += 1
            print(f"✓ Script generated successfully with o3!")
            print(f"  Word count: {result['word_count']}")
            
            # Show first few lines of hook
            if "hook" in result:
                hook_preview = result["hook"][:150] + "..." if len(result["hook"]) > 150 else result["hook"]
                print(f"  Hook preview: {hook_preview}")
            
            # Estimate cost
            cost_estimate = generator.estimate_cost(result)
            total_cost += cost_estimate["total_cost"]
            print(f"  Estimated cost: {cost_estimate['total_cost_usd']}")
            print(f"  (Input: {cost_estimate['input_tokens']} tokens, Output: {cost_estimate['output_tokens']} tokens)")
            
            # Save to file for review in dev/llm folder
            filename = f"dev/llm/o3_script_{actor.replace(' ', '_').lower()}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  Saved to: {filename}")
            
        else:
            print(f"✗ Error: {result['error']}")
            if "organization must be verified" in str(result['error']):
                print("\n⚠️  ORGANIZATION VERIFICATION REQUIRED")
                print("Please verify your organization at:")
                print("https://platform.openai.com/settings/organization/general")
                print("\nSteps:")
                print("1. Click 'Verify Organization'")
                print("2. Complete verification with ID and business info")
                print("3. Wait 15 minutes for access to propagate")
                print("4. Run this script again")
                return
    
    # Summary
    if successful_scripts > 0:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Successfully generated: {successful_scripts}/{len(test_actors)} scripts")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"Average cost per script: ${total_cost/successful_scripts:.4f}")
        
        # Calculate monthly cost projections with o3
        print("\n" + "=" * 60)
        print("COST PROJECTIONS WITH O3")
        print("=" * 60)
        scripts_per_month = [100, 500, 1000, 5000]
        
        for count in scripts_per_month:
            # o3: ~285 input + 1,250 output tokens per script
            monthly_cost = count * ((285 / 1_000_000 * 2.0) + (1250 / 1_000_000 * 8.0))
            print(f"{count:>5} scripts/month: ${monthly_cost:>7.2f}")


if __name__ == "__main__":
    test_o3_script_generation()