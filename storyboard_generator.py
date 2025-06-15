#!/usr/bin/env python3
"""
Storyboard generation for video production planning.
Breaks down scripts into shots with AI prompts for images and videos.
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


class StoryboardGenerator:
    """
    Generates storyboard JSON with shot breakdown and AI prompts.
    """
    
    # Storyboard generation prompt
    STORYBOARD_PROMPT_TEMPLATE = """You are a senior storyboard + multimodal-prompt architect.

TASK  
From the SCRIPT below, create a shot list (≥ 45 shots) for a YouTube biography aimed at men 55–70.  
• Shots 1-6 = HOOK stingers (2 s each).  
• Remaining shots = BIO micro-shots (5 s each).  
• Break whenever the idea, location, or era shifts.  
• If the total is < 45, subdivide until you reach ≥ 45.  
• **Every word** of the SCRIPT must appear verbatim in exactly one **script** field—no overlap, no omissions.

FACE & LIKENESS RULE  
• It's best if most AI generated images are not of the actor. But if it's best for the actor human subject to be part of the AI generated image, the images must **avoid a full, clearly recognizable adult face** of the actor. Use silhouettes, back-of-head, side-profile, oblique angles, heavy rim-light, or foreground objects that obscure facial detail.  
• If the actor needs to be depicted **under 18**, you may specify age ("young 6-year-old Michael Landon", "teenage Michael Landon") to guide style, since likeness risk is lower.  
• Do **not** include "portrait," "close-up," or front-facing facial terms for adult shots.

OUTPUT  
Return **one JSON array**. Each element must use **exactly** these keys:

```json
{{
  "shot": <integer>,                  // sequential, starting at 1
  "script": "<verbatim script chunk>",// full chunk this shot covers
  "image_search": "<5-8 keyword phrase>",
  "flux_prompt": "<≈35-word FLUX Pro 1.1 prompt ending with --raw --aspect 16:9 --negative 'text, watermark, logo, disfigured face'>",
  "ai_video_prompt": "<1-2 vivid sentences for a 5-second loop>",
  "youtube_search": "<5-10 keyword phrase>"
}}```

COLUMN GUIDELINES
• image_search – actor/era/context + medium (e.g., "Michael Landon javelin 1954 black-and-white photo").
• flux_prompt – craft cinematic, dramatic, eye-locking imagery:
– Start with a camera move (low-angle dolly, crane, push-in, Dutch tilt, macro, aerial, etc.).
– State lens / format (35 mm anamorphic, 70 mm IMAX, f/1.8 bokeh, macro 100 mm).
– Specify lighting & mood (golden-hour rim light, chiaroscuro, neon-noir, tungsten practicals, stormy low-key).
– Add color / film stock (Kodachrome, Technicolor, VHS fuzz, Fuji Velvia).
– Include composition hooks (rule-of-thirds silhouette, leading lines, layered depth, dramatic negative space).
– Keep faces obscured unless the actor is ≤ 18 (use age labels as allowed).
– Finish with: --raw --aspect 16:9 --negative "text, watermark, logo, disfigured face" to enforce photoreal RAW mode, widescreen, and clean output.
• ai_video_prompt – describe the 5-s loop: motion path, atmosphere, overlays (film grain, scan-lines), optional sound cue.
• youtube_search – actor/title/year + scene or B-roll descriptor.
• Vary vocabulary; avoid repeating identical words across prompts.
• Output no headings, commentary, or extra keys—just the pure JSON array.

SCRIPT TO PROCESS:
{script_content}
"""
    
    def __init__(self, model_name: str = "o3-2025-04-16"):
        """Initialize the storyboard generator with o3 model."""
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
                name="StoryboardArchitect",
                model=self.model_name,
                instructions="You are an expert storyboard architect who creates detailed shot lists with AI prompts for video production.",
                model_settings=model_settings
            )
            logger.info(f"Successfully initialized storyboard agent with model: {self.model_name} (reasoning effort: high)")
        except Exception as e:
            logger.error(f"Failed to initialize storyboard agent: {e}")
            raise
    
    def extract_script_content(self, script_path: str) -> str:
        """
        Extract just the HOOK and BIO content from a script file.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            The extracted script content
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the HOOK section
            hook_match = re.search(r'\*\*HOOK\*\*\s*\n(.*?)(?=\*\*BIO\*\*)', content, re.DOTALL)
            bio_match = re.search(r'\*\*BIO\*\*\s*\n(.*?)$', content, re.DOTALL)
            
            if hook_match and bio_match:
                hook_content = hook_match.group(1).strip()
                bio_content = bio_match.group(1).strip()
                return f"**HOOK**\n{hook_content}\n\n**BIO**\n{bio_content}"
            else:
                # Fallback: return full content if parsing fails
                logger.warning("Could not parse HOOK/BIO sections, using full content")
                return content
                
        except Exception as e:
            logger.error(f"Error reading script file: {e}")
            raise
    
    def parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the JSON response from the model, handling potential formatting issues.
        
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
    
    def validate_storyboard(self, storyboard: List[Dict[str, Any]], script_content: str) -> tuple[bool, List[str]]:
        """
        Validate the generated storyboard.
        
        Args:
            storyboard: The generated storyboard data
            script_content: The original script content
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check shot count
        if len(storyboard) < 45:
            issues.append(f"Insufficient shots: {len(storyboard)} < 45")
        
        # Check required fields
        required_fields = ["shot", "script", "image_search", "flux_prompt", "ai_video_prompt", "youtube_search"]
        for i, shot in enumerate(storyboard):
            for field in required_fields:
                if field not in shot:
                    issues.append(f"Shot {i+1} missing field: {field}")
        
        # Check shot numbering
        for i, shot in enumerate(storyboard):
            if shot.get("shot") != i + 1:
                issues.append(f"Shot numbering error at position {i+1}")
        
        # Collect all script chunks
        all_chunks = ' '.join(shot.get("script", "") for shot in storyboard)
        
        # Basic check for script coverage (simplified)
        if len(all_chunks) < len(script_content) * 0.8:
            issues.append("Script coverage appears incomplete")
        
        return len(issues) == 0, issues
    
    def generate_storyboard(self, script_content: str, actor_name: str) -> Dict[str, Any]:
        """
        Generate a storyboard from the script content.
        
        Args:
            script_content: The full script content
            actor_name: Name of the actor
            
        Returns:
            Dictionary containing storyboard data and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating storyboard for: {actor_name}")
            
            # Format prompt
            prompt = self.STORYBOARD_PROMPT_TEMPLATE.format(script_content=script_content)
            
            # Generate storyboard
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
            storyboard_data = self.parse_json_response(output)
            
            # Validate the storyboard
            is_valid, validation_issues = self.validate_storyboard(storyboard_data, script_content)
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Prepare response
            result_data = {
                "actor_name": actor_name,
                "storyboard": storyboard_data,
                "shot_count": len(storyboard_data),
                "model_used": self.model_name,
                "generation_time": round(generation_time, 2),
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid": is_valid,
                "validation_issues": validation_issues if not is_valid else None,
                "usage": usage_data if usage_data else None,
                "reasoning_effort": "high"
            }
            
            logger.info(f"Successfully generated storyboard for {actor_name} "
                       f"({len(storyboard_data)} shots in {generation_time:.1f}s)")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Storyboard generation error: {e}", exc_info=True)
            return {
                "actor_name": actor_name,
                "error": str(e),
                "success": False,
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def estimate_cost(self, storyboard_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate the API cost for storyboard generation.
        
        Returns:
            Dictionary with cost breakdown
        """
        # Use actual token data if available
        usage = storyboard_data.get("usage", {})
        
        if usage and usage.get("input_tokens") and usage.get("output_tokens"):
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            reasoning_tokens = usage.get("reasoning_tokens", 0)
        else:
            # Rough estimates
            input_tokens = 3000  # Script + prompt
            output_tokens = 10000  # Large JSON output
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