import os
from agents import Agent, Runner
from typing import Dict, Any

# Script generation prompt template
SCRIPT_PROMPT_TEMPLATE = """You are writing a 5-minute biography video for **{actor_name}**.

GLOBAL RULES  
• 780–830 words (≈5 min @ 155 wpm).  
• Action beats in historical-present; context may use past but never mix tenses in one sentence.  
• Voice = confident "sports-doc storyteller": punchy, nostalgic, dry-witty; no Gen-Z slang.  
• ≥ 8 explicit year stamps inside the narration; mention the actor's age at least twice.  
• Insert one mini cliff-hanger around the 80–90 s mark; weave a humorous callback in each later act.  
• **Output only the words the narrator speaks**—no outros, CTAs, visuals, music cues, section headers, timelines, or tables.

OUTPUT MARKDOWN FORMAT (exactly):  

**{actor_name} — 5-MINUTE BIO SCRIPT (~XXX words)**  

**HOOK**  
Fragment. Fragment. Fragment. And [surprise facet].  
{actor_name}'s [metaphor or superlative tied to a signature role]. **[Custom, hook-relevant action phrase], and let's get rollin'.**

**BIO**  
(Full narration here in continuous paragraphs—from birth to present-day epilogue. No additional headings.)"""


def create_script_agent(use_persistent_instructions: bool = True) -> Agent:
    """
    Create an agent for script generation.
    
    Args:
        use_persistent_instructions: If True, creates agent with built-in instructions.
                                   If False, instructions must be passed with each query.
    
    Returns:
        Agent configured for script generation
    """
    if use_persistent_instructions:
        # Agent with pre-configured instructions
        return Agent(
            name="ScriptWriter",
            model="o3-mini",  # Using o3-mini as specified in project notes
            instructions="You are an expert biography script writer for YouTube videos. Follow the exact formatting and rules provided in each request."
        )
    else:
        # Basic agent that requires full prompt each time
        return Agent(
            name="ScriptWriter",
            model="o3-mini"
        )


def generate_script_with_persistent_agent(agent: Agent, actor_name: str) -> str:
    """
    Generate script using an agent with persistent instructions.
    """
    prompt = SCRIPT_PROMPT_TEMPLATE.format(actor_name=actor_name)
    result = Runner.run_sync(agent, prompt)
    return result.final_output


def generate_script_with_basic_agent(agent: Agent, actor_name: str) -> str:
    """
    Generate script using a basic agent (full prompt each time).
    """
    prompt = SCRIPT_PROMPT_TEMPLATE.format(actor_name=actor_name)
    result = Runner.run_sync(agent, prompt)
    return result.final_output


def test_script_generation():
    """
    Test script generation with different approaches.
    """
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Test actor name
    actor_name = "Tom Hanks"
    
    print("Testing OpenAI Agents SDK for Script Generation")
    print("=" * 50)
    
    # Test 1: Agent with persistent instructions
    print("\n1. Testing with persistent instructions agent...")
    try:
        persistent_agent = create_script_agent(use_persistent_instructions=True)
        script1 = generate_script_with_persistent_agent(persistent_agent, actor_name)
        print(f"Script generated successfully (length: {len(script1)} chars)")
        print("\nFirst 200 characters of script:")
        print(script1[:200] + "...")
    except Exception as e:
        print(f"Error with persistent agent: {e}")
    
    # Test 2: Basic agent (full prompt each time)
    print("\n\n2. Testing with basic agent (full prompt)...")
    try:
        basic_agent = create_script_agent(use_persistent_instructions=False)
        script2 = generate_script_with_basic_agent(basic_agent, actor_name)
        print(f"Script generated successfully (length: {len(script2)} chars)")
        print("\nFirst 200 characters of script:")
        print(script2[:200] + "...")
    except Exception as e:
        print(f"Error with basic agent: {e}")


if __name__ == "__main__":
    test_script_generation()