import os
import json
import time
import logging
from typing import Dict, Any, Optional
from agents import Agent, Runner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PhoneticScriptGenerator:
    """
    Converts scripts to phonetic versions for TTS using o4-mini.
    """
    
    # Phonetic conversion prompt
    PHONETIC_PROMPT_TEMPLATE = """You are converting a biography script for a 17-year-old narrator who is an excellent reader but lacks life experience with uncommon proper nouns (names, places, businesses, etc.).

TASK: Convert proper nouns that meet ALL these criteria:
1. A high school senior likely hasn't encountered it before
2. Sounding it out would NOT produce the correct pronunciation
3. It's a proper noun (person, place, business, group, etc.)

CONVERSION RULES:
- Replace ONLY the proper nouns that meet the above criteria with phonetic spelling
- Write phonetic versions as a 12-year-old would read them
- Use simple letter combinations, NO dashes or special characters
- Keep EVERYTHING else exactly the same (punctuation, formatting, structure)
- Common names like "Tom", "New York", "Hollywood" should NOT be changed
- Focus on: foreign names, historical figures, uncommon place names, specialized terms

EXAMPLES:
- "Saoirse Ronan" → "Seersha Ronan"
- "Joaquin Phoenix" → "Wahkeen Phoenix"
- "Gal Gadot" → "Gal Gahdoe"
- "Lupita Nyong'o" → "Loopeeta Nyongo"
- "Versailles" → "Vairsigh"
- "Leicester" → "Lester"
- "Siobhan" → "Shivawn"

ORIGINAL SCRIPT:
{script}

OUTPUT: The exact same script with ONLY the necessary proper nouns converted to phonetic spelling. Do not add any explanations or notes."""

    def __init__(self):
        """Initialize the phonetic generator with available model."""
        # Try different model options
        self.model_options = [
            "o4-mini",
            "gpt-4o",
            "o3-mini-2025-01-31",
            "gpt-4-turbo"
        ]
        self.model_name = None
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the AI agent with fallback models."""
        for model in self.model_options:
            try:
                self.agent = Agent(
                    name="PhoneticConverter",
                    model=model,
                    instructions="You are an expert at converting scripts to phonetic versions for text-to-speech systems. Follow the exact instructions provided in each request."
                )
                self.model_name = model
                logger.info(f"Successfully initialized phonetic agent with model: {self.model_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize with {model}: {e}")
                continue
        
        # If all models failed
        raise Exception(f"Failed to initialize phonetic agent with any available model: {self.model_options}")
    
    def generate_phonetic_script(self, original_script: str, actor_name: str) -> Dict[str, Any]:
        """
        Convert a script to phonetic version.
        
        Args:
            original_script: The original script text
            actor_name: The actor's name (for metadata)
            
        Returns:
            Dictionary with phonetic script and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating phonetic script for {actor_name}")
            
            # Format prompt
            prompt = self.PHONETIC_PROMPT_TEMPLATE.format(script=original_script)
            
            # Generate phonetic version
            result = Runner.run_sync(self.agent, prompt)
            phonetic_script = result.final_output
            
            # Calculate metrics
            generation_time = time.time() - start_time
            
            # Count conversions (rough estimate based on common patterns)
            conversions = self._estimate_conversions(original_script, phonetic_script)
            
            return {
                "actor_name": actor_name,
                "phonetic_script": phonetic_script,
                "original_script": original_script,
                "model_used": self.model_name,
                "generation_time": round(generation_time, 2),
                "estimated_conversions": conversions,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Phonetic generation error: {e}")
            return {
                "actor_name": actor_name,
                "error": str(e),
                "success": False,
                "model_used": self.model_name
            }
    
    def _estimate_conversions(self, original: str, phonetic: str) -> int:
        """Estimate number of conversions made."""
        # Simple heuristic: count significant differences
        if len(original) != len(phonetic):
            return -1  # Can't easily estimate if lengths differ
        
        conversions = 0
        i = 0
        while i < len(original):
            if original[i] != phonetic[i]:
                # Found a difference, skip ahead to find end of word
                while i < len(original) and original[i].isalpha():
                    i += 1
                conversions += 1
            else:
                i += 1
        
        return conversions
    
    def generate_with_retry(self, original_script: str, actor_name: str, max_retries: int = 2) -> Dict[str, Any]:
        """Generate phonetic script with retry logic."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Phonetic generation attempt {attempt + 1}/{max_retries}")
                result = self.generate_phonetic_script(original_script, actor_name)
                
                if result.get("success"):
                    return result
                    
            except Exception as e:
                last_error = e
                logger.error(f"Phonetic attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
        
        return {
            "actor_name": actor_name,
            "success": False,
            "error": f"Failed after {max_retries} attempts: {str(last_error)}"
        }