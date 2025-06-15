#!/usr/bin/env python3
"""
Music plan generation for video production.
Creates AI music prompts based on biography scripts.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from agents import Agent, Runner, ModelSettings
from openai.types.shared import Reasoning
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MusicPlanGenerator:
    """
    Generates AI music prompts for biography videos.
    """
    
    # Music plan generation prompt
    MUSIC_PROMPT_TEMPLATE = """You are an elite AI music supervisor for fast-paced YouTube biography videos (target audience: men 45 – 65, mostly U.S./U.K.).

##################  TASK  ##################
1. READ the full SCRIPT immediately following the delimiter.
2. REASON deeply:
   • Identify the subject's peak decades, signature works, core persona, and dominant moods.  
   • Note pacing clues (hook length, montage density, emotional highs/lows).
3. DESIGN exactly **three DISTINCT Suno "Custom-mode" instrumental prompts** that:
   • Feel naturally upbeat for narration (≈100-120 BPM unless the script clearly demands another tempo).  
   • Remain **100 % instrumental** (no vocals).  
   • Use clear structural tags **[Intro] [Verse] [Chorus] [Bridge] [Outro]**, total ≤120 s, loop-friendly, with open midrange for voice-over.  
   • Include a **track title, BPM, key, and concise genre label**—written *once* at the start of each prompt.  
   • Style requirements:  
     – **Prompt 1:** strong rock influence drawn from the decade of rock that best fits the actor's peak era.  
     – **Prompt 2:** moderate rock influence from whichever decade suits the actor.  
     – **Prompt 3:** any other style you deem most effective for the script.

################  OUTPUT FORMAT  ################
Return **one JSON array** and nothing else.  
Each of the three objects must contain **exactly one key, `suno_prompt`**, whose value is a **single-line string (no newline characters)** formatted like this:

{{
"suno_prompt": "<Track Title> | <BPM> BPM | <Key> | <Genre Label> | [Intro] … [Outro]"
}}

Formatting rules for each `suno_prompt` value  
• Separate the four header items with the pipe symbol (`|`).  
• Write musical keys in full words (e.g., "E minor", never "E-min").  
• Do **not** repeat BPM, key, or genre later in the prompt.  
• Avoid abbreviations that could be misread (e.g., "E-min" can be parsed as "Eminem").  
• Keep everything on one line—no `\n`.

SCRIPT TO PROCESS:
{script_content}
"""
    
    def __init__(self, model_name: str = "o3-2025-04-16"):
        """Initialize the music plan generator with o3 model."""
        self.model_name = model_name
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the AI agent with high reasoning effort."""
        try:
            # Configure high reasoning effort
            model_settings = ModelSettings(
                reasoning=Reasoning(effort="high")
            )
            
            self.agent = Agent(
                name="MusicSupervisor",
                model=self.model_name,
                instructions="You are an expert music supervisor who creates instrumental music prompts for video production.",
                model_settings=model_settings
            )
            logger.info(f"Successfully initialized music plan agent with model: {self.model_name} (reasoning effort: high)")
        except Exception as e:
            logger.error(f"Failed to initialize music plan agent: {e}")
            raise
    
    def parse_json_response(self, response: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from the model.
        
        Args:
            response: The model's response
            
        Returns:
            Parsed JSON array
        """
        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON array from the response
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, log the error
            logger.error("Failed to parse JSON response")
            logger.debug(f"Response: {response[:500]}...")
            raise ValueError("Invalid JSON response from model")
    
    def validate_music_plan(self, music_plan: List[Dict[str, str]]) -> tuple[bool, List[str]]:
        """
        Validate the generated music plan.
        
        Args:
            music_plan: The generated music plan data
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check we have exactly 3 prompts
        if len(music_plan) != 3:
            issues.append(f"Expected 3 prompts, got {len(music_plan)}")
        
        # Check each prompt
        for i, prompt_obj in enumerate(music_plan):
            if "suno_prompt" not in prompt_obj:
                issues.append(f"Prompt {i+1} missing 'suno_prompt' key")
                continue
            
            prompt = prompt_obj["suno_prompt"]
            
            # Check for required components
            if "|" not in prompt:
                issues.append(f"Prompt {i+1} missing pipe separators")
            else:
                parts = prompt.split("|")
                if len(parts) < 4:
                    issues.append(f"Prompt {i+1} has insufficient components")
            
            # Check for structural tags
            required_tags = ["[Intro]", "[Outro]"]
            for tag in required_tags:
                if tag not in prompt:
                    issues.append(f"Prompt {i+1} missing {tag}")
            
            # Check for newlines
            if "\n" in prompt:
                issues.append(f"Prompt {i+1} contains newline characters")
        
        return len(issues) == 0, issues
    
    def generate_music_plan(self, script_content: str, actor_name: str) -> Dict[str, Any]:
        """
        Generate a music plan from the script content.
        
        Args:
            script_content: The full script content
            actor_name: Name of the actor
            
        Returns:
            Dictionary containing music plan data and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating music plan for: {actor_name}")
            
            # Format prompt
            prompt = self.MUSIC_PROMPT_TEMPLATE.format(script_content=script_content)
            
            # Generate music plan
            result = Runner.run_sync(self.agent, prompt)
            output = result.final_output
            
            # Extract token usage if available
            usage_data = {}
            if hasattr(result, 'context_wrapper') and result.context_wrapper and hasattr(result.context_wrapper, 'usage'):
                usage = result.context_wrapper.usage
                usage_data = {
                    'input_tokens': getattr(usage, 'input_tokens', None),
                    'output_tokens': getattr(usage, 'output_tokens', None),
                    'total_tokens': getattr(usage, 'total_tokens', None)
                }
                
                # Check for reasoning tokens
                if hasattr(usage, 'output_tokens_details') and usage.output_tokens_details:
                    usage_data['reasoning_tokens'] = getattr(usage.output_tokens_details, 'reasoning_tokens', 0)
            
            # Parse the JSON response
            music_plan_data = self.parse_json_response(output)
            
            # Validate the music plan
            is_valid, validation_issues = self.validate_music_plan(music_plan_data)
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Prepare response
            result_data = {
                "actor_name": actor_name,
                "music_prompts": music_plan_data,
                "model_used": self.model_name,
                "generation_time": round(generation_time, 2),
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid": is_valid,
                "validation_issues": validation_issues if not is_valid else None,
                "usage": usage_data if usage_data else None,
                "reasoning_effort": "high"
            }
            
            logger.info(f"Successfully generated music plan for {actor_name} "
                       f"({len(music_plan_data)} prompts in {generation_time:.1f}s)")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Music plan generation error: {e}", exc_info=True)
            return {
                "actor_name": actor_name,
                "error": str(e),
                "success": False,
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def estimate_cost(self, music_plan_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate the API cost for music plan generation.
        
        Returns:
            Dictionary with cost breakdown
        """
        # Use actual token data if available
        usage = music_plan_data.get("usage", {})
        
        if usage and usage.get("input_tokens") and usage.get("output_tokens"):
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            reasoning_tokens = usage.get("reasoning_tokens", 0)
        else:
            # Rough estimates
            input_tokens = 2000  # Script + prompt
            output_tokens = 500  # Three music prompts
            reasoning_tokens = 0
        
        # o3 pricing: $2/1M input, $8/1M output
        input_cost = (input_tokens / 1_000_000) * 2.0
        output_cost = (output_tokens / 1_000_000) * 8.0
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "total_cost_usd": f"${total_cost:.4f}"
        }