import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from agents import Agent, Runner
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dev/llm/script_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScriptGenerationError(Exception):
    """Custom exception for script generation errors."""
    pass


class APIError(ScriptGenerationError):
    """API-related errors."""
    pass


class ValidationError(ScriptGenerationError):
    """Input validation errors."""
    pass


class ProductionScriptGenerator:
    """
    Production-ready script generator with comprehensive error handling.
    """
    
    # Script generation prompt template
    SCRIPT_PROMPT_TEMPLATE = """You are writing a 5-minute biography video for **{actor_name}**.

========================  GLOBAL STORY GUIDELINES  ========================
1.  WORD COUNT & PACE  
   • 780–830 words (≈5 min @ 155 wpm).  
2.  TENSE RULE  
   • Action beats in historical-present ("he knocks," "she wins"); background may use past, **but never mix tenses in one sentence**.  
3.  VOICE & TARGET DEMO  
   • Confident "sports-doc storyteller": punchy, nostalgic, dry-witty.  
   • Lean on era-flavored verbs & metaphors that resonate with 45- to 65-year-olds; **no Gen-Z slang**.  
4.  DATES & AGES  
   • **Use 6–9 explicit year stamps** total, spread out—**max one date OR one age per sentence**.  
   • Reference the actor's age at least twice ("at 32," "now 47").  
5.  SUSPENSE MOMENT  
   • Around the 80–90 s mark, insert a naturally arising **question** that tees up tension; **do not label it** as a cliff-hanger.  
6.  CALLBACK ENGINE  
   • Choose a single tangible motif (prop, catch-phrase, vehicle). Mention it once early, then **exactly 3 humorous or poignant callbacks** later—each stronger than the last.  
7.  EMOTIONAL TRIP-WIRE  
   • End with a 1- or 2-sentence legacy reflection that references the motif and stirs quiet emotion. No outros, CTAs, or brand names.  
8.  LANGUAGE MUSIC  
   • Vary sentence lengths—staccato punch followed by a medium beat, then an occasional lyrical line.  
9.  OUTPUT SANITATION  
   • Narration only. No visuals, tables, scene headings, timelines, sound cues, or formatting notes beyond what is defined below.

========================  OUTPUT MARKDOWN FORMAT  ========================

**{actor_name} — 5-MINUTE BIO SCRIPT (~XXX words)**  

**HOOK**  
Fragment. Fragment. Fragment. And [surprise facet].  
{actor_name}'s [metaphor or superlative tied to a signature role]. **[Imperative callback — verb-first, 2–4 words from an iconic prop / phrase / setting], and let's get rollin'.**

**BIO**  
(Continuous paragraphs—birth to present-day epilogue; follow all guidelines above.)

=========================================================================

HOW TO PICK THE IMPERATIVE CALLBACK  
• Must start with a verb ("Spin the rotor," "Prime the proton pack," "Dust off the Stetson").  
• 2 – 4 words, no pronouns, ends with a comma so it flows: "…[callback], and let's get rollin'."  
• Anchor it to the actor's most recognizable prop, vehicle, or genre.

REMINDER CHECKLIST (self-verify before output)  
☐ 780–830 words  
☐ 6–9 year stamps, never >1 per sentence  
☐ ≥2 age mentions  
☐ Natural tension-raising question ~80-90 s  
☐ Single motif with 3 callbacks  
☐ Imperative callback flows into "…and let's get rollin'."  
☐ Emotional legacy close, no outros or brand plugs  
☐ Only spoken narration appears in final output"""
    
    # Configuration
    DEFAULT_MODEL = "o3-2025-04-16"
    FALLBACK_MODEL = "o3-mini-2025-01-31"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    OUTPUT_DIR = "dev/llm"
    
    # Validation rules
    MIN_WORD_COUNT = 780
    MAX_WORD_COUNT = 830
    REQUIRED_SECTIONS = ["HOOK", "BIO"]
    
    def __init__(self, model_name: Optional[str] = None, use_fallback: bool = True):
        """
        Initialize the script generator.
        
        Args:
            model_name: Specific model to use (defaults to o3)
            use_fallback: Whether to fallback to o3-mini if o3 fails
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.use_fallback = use_fallback
        self.agent = None
        self._ensure_output_dir()
        
        # Try to initialize agent
        try:
            self._initialize_agent()
        except Exception as e:
            logger.error(f"Failed to initialize agent with {self.model_name}: {e}")
            if self.use_fallback:
                logger.info(f"Attempting fallback to {self.FALLBACK_MODEL}")
                self.model_name = self.FALLBACK_MODEL
                self._initialize_agent()
            else:
                raise
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        Path(self.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    def _initialize_agent(self):
        """Initialize the AI agent with error handling."""
        try:
            self.agent = Agent(
                name="ScriptWriter",
                model=self.model_name,
                instructions="You are an expert biography script writer for YouTube videos. Follow the exact formatting and rules provided in each request."
            )
            logger.info(f"Successfully initialized agent with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise APIError(f"Could not initialize agent with model {self.model_name}: {str(e)}")
    
    def validate_actor_name(self, actor_name: str) -> str:
        """
        Validate and sanitize actor name.
        
        Args:
            actor_name: The actor's name to validate
            
        Returns:
            Sanitized actor name
            
        Raises:
            ValidationError: If the name is invalid
        """
        if not actor_name or not isinstance(actor_name, str):
            raise ValidationError("Actor name must be a non-empty string")
        
        # Remove excessive whitespace
        actor_name = ' '.join(actor_name.split())
        
        # Check length
        if len(actor_name) < 2:
            raise ValidationError("Actor name too short")
        if len(actor_name) > 100:
            raise ValidationError("Actor name too long")
        
        # Basic sanitization - allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", actor_name):
            raise ValidationError("Actor name contains invalid characters")
        
        return actor_name
    
    def _validate_script_output(self, output: str, actor_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that the script meets all requirements.
        
        Args:
            output: The generated script
            actor_name: The actor's name
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if output is empty
        if not output or not output.strip():
            issues.append("Output is empty")
            return False, issues
        
        # Check word count
        word_count = len(output.split())
        if word_count < self.MIN_WORD_COUNT:
            issues.append(f"Word count too low: {word_count} < {self.MIN_WORD_COUNT}")
        elif word_count > self.MAX_WORD_COUNT:
            issues.append(f"Word count too high: {word_count} > {self.MAX_WORD_COUNT}")
        
        # Check for required sections
        for section in self.REQUIRED_SECTIONS:
            if f"**{section}**" not in output:
                issues.append(f"Missing required section: {section}")
        
        # Check if actor name is mentioned
        if actor_name not in output:
            issues.append("Actor name not found in script")
        
        # Check for year stamps (should have 6-9)
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        years_found = len(re.findall(year_pattern, output))
        if years_found < 6:
            issues.append(f"Insufficient year stamps: {years_found} < 6")
        elif years_found > 9:
            issues.append(f"Too many year stamps: {years_found} > 9")
        
        return len(issues) == 0, issues
    
    def _parse_script_sections(self, output: str) -> Dict[str, str]:
        """
        Parse the script into sections.
        
        Args:
            output: The full script output
            
        Returns:
            Dictionary with parsed sections
        """
        sections = {}
        
        try:
            # Extract title/header
            title_match = re.search(r'\*\*(.+?)\s*—\s*5-MINUTE BIO SCRIPT[^*]*\*\*', output)
            if title_match:
                sections['title'] = title_match.group(0)
            
            # Extract HOOK section
            if "**HOOK**" in output and "**BIO**" in output:
                hook_start = output.index("**HOOK**") + len("**HOOK**")
                bio_start = output.index("**BIO**")
                sections['hook'] = output[hook_start:bio_start].strip()
                
                # Extract BIO section
                sections['bio'] = output[bio_start + len("**BIO**"):].strip()
            
        except Exception as e:
            logger.warning(f"Error parsing script sections: {e}")
        
        return sections
    
    def generate_script_with_retry(self, actor_name: str, max_retries: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a script with retry logic.
        
        Args:
            actor_name: Name of the actor
            max_retries: Override default max retries
            
        Returns:
            Dictionary with script data and metadata
        """
        max_retries = max_retries or self.MAX_RETRIES
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} for {actor_name}")
                result = self.generate_script(actor_name)
                
                # If successful and valid, return
                if result.get("success") and result.get("valid"):
                    return result
                
                # If generated but invalid, log issues
                if result.get("success") and not result.get("valid"):
                    logger.warning(f"Script generated but validation failed: {result.get('validation_issues')}")
                    
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = self.RETRY_DELAY * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        error_msg = f"Failed after {max_retries} attempts"
        if last_error:
            error_msg += f": {str(last_error)}"
        
        return {
            "actor_name": actor_name,
            "success": False,
            "error": error_msg,
            "attempts": max_retries
        }
    
    def generate_script(self, actor_name: str) -> Dict[str, Any]:
        """
        Generate a biography script for the given actor.
        
        Args:
            actor_name: Name of the actor
            
        Returns:
            Dictionary containing script data and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input
            actor_name = self.validate_actor_name(actor_name)
            logger.info(f"Generating script for: {actor_name}")
            
            # Format prompt
            prompt = self.SCRIPT_PROMPT_TEMPLATE.format(actor_name=actor_name)
            
            # Generate script
            result = Runner.run_sync(self.agent, prompt)
            output = result.final_output
            
            # Parse sections
            sections = self._parse_script_sections(output)
            
            # Validate output
            is_valid, validation_issues = self._validate_script_output(output, actor_name)
            
            # Calculate metrics
            word_count = len(output.split())
            generation_time = time.time() - start_time
            
            # Prepare response
            script_data = {
                "actor_name": actor_name,
                "full_script": output,
                "sections": sections,
                "word_count": word_count,
                "model_used": self.model_name,
                "generation_time": round(generation_time, 2),
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid": is_valid,
                "validation_issues": validation_issues if not is_valid else None
            }
            
            # Add individual sections if parsed
            if "hook" in sections:
                script_data["hook"] = sections["hook"]
            if "bio" in sections:
                script_data["bio"] = sections["bio"]
            
            # Log success
            logger.info(f"Successfully generated script for {actor_name} "
                       f"({word_count} words in {generation_time:.1f}s)")
            
            return script_data
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "actor_name": actor_name,
                "error": f"Validation error: {str(e)}",
                "error_type": "validation",
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            
            # Check for specific API errors
            error_str = str(e)
            error_type = "unknown"
            
            if "rate_limit" in error_str.lower():
                error_type = "rate_limit"
            elif "api_key" in error_str.lower():
                error_type = "authentication"
            elif "model_not_found" in error_str.lower():
                error_type = "model_access"
            elif "timeout" in error_str.lower():
                error_type = "timeout"
            
            return {
                "actor_name": actor_name,
                "error": str(e),
                "error_type": error_type,
                "success": False,
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def save_script(self, script_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save script data to file with error handling.
        
        Args:
            script_data: The script data to save
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        try:
            # Generate filename if not provided
            if not filename:
                actor_slug = script_data['actor_name'].lower().replace(' ', '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.model_name}_{actor_slug}_{timestamp}.json"
            
            filepath = os.path.join(self.OUTPUT_DIR, filename)
            
            # Save with pretty printing
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            raise
    
    def batch_generate(self, actor_names: List[str], save_results: bool = True) -> Dict[str, Any]:
        """
        Generate scripts for multiple actors with progress tracking.
        
        Args:
            actor_names: List of actor names
            save_results: Whether to save individual results
            
        Returns:
            Summary dictionary with results
        """
        logger.info(f"Starting batch generation for {len(actor_names)} actors")
        
        results = []
        successful = 0
        failed = 0
        total_cost = 0
        
        for i, actor_name in enumerate(actor_names, 1):
            logger.info(f"Processing {i}/{len(actor_names)}: {actor_name}")
            
            # Generate with retry
            result = self.generate_script_with_retry(actor_name)
            results.append(result)
            
            if result.get("success"):
                successful += 1
                
                # Save if requested
                if save_results:
                    try:
                        self.save_script(result)
                    except Exception as e:
                        logger.error(f"Failed to save script for {actor_name}: {e}")
                
                # Estimate cost (rough calculation)
                total_cost += self.estimate_cost(result)["total_cost"]
            else:
                failed += 1
            
            # Rate limiting pause
            if i < len(actor_names):
                time.sleep(1)
        
        # Summary
        summary = {
            "total": len(actor_names),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(actor_names) if actor_names else 0,
            "total_cost_usd": round(total_cost, 4),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save summary
        if save_results:
            summary_path = os.path.join(self.OUTPUT_DIR, f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Batch summary saved to: {summary_path}")
        
        return summary
    
    def estimate_cost(self, script_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate the API cost for the script generation.
        
        Returns:
            Dictionary with cost breakdown
        """
        # Token estimates
        input_tokens = 285  # Approximate prompt size
        output_tokens = script_data.get("word_count", 800) * 1.5
        
        # Model-specific pricing
        if "o3-mini" in self.model_name:
            input_price = 1.0  # $1 per 1M tokens (estimated)
            output_price = 4.0  # $4 per 1M tokens (estimated)
        else:  # o3
            input_price = 2.0  # $2 per 1M tokens
            output_price = 8.0  # $8 per 1M tokens
        
        # Calculate
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


def test_production_generator():
    """Test the production script generator with various scenarios."""
    
    print("Testing Production Script Generator")
    print("=" * 60)
    
    # Initialize generator
    generator = ProductionScriptGenerator()
    
    # Test cases
    test_cases = [
        # Valid cases
        "Tom Hanks",
        "Meryl Streep",
        "Robert De Niro",
        
        # Edge cases
        "Mary-Kate Olsen",  # Hyphenated name
        "Samuel L. Jackson",  # Name with period
        "Lupita Nyong'o",  # Name with apostrophe
        
        # Invalid cases (should fail validation)
        "",  # Empty
        "A",  # Too short
        "123Actor",  # Contains numbers
        "Actor@Name",  # Invalid characters
    ]
    
    results = []
    
    for actor in test_cases:
        print(f"\nTesting: '{actor}'")
        print("-" * 40)
        
        try:
            result = generator.generate_script(actor)
            
            if result["success"]:
                print(f"✓ Success: {result['word_count']} words in {result.get('generation_time', 'N/A')}s")
                if not result.get("valid"):
                    print(f"  ⚠️  Validation issues: {result['validation_issues']}")
            else:
                print(f"✗ Failed: {result['error']} (type: {result.get('error_type', 'unknown')})")
            
            results.append(result)
            
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
            results.append({"actor_name": actor, "error": str(e), "success": False})
    
    # Test batch generation
    print("\n" + "=" * 60)
    print("Testing Batch Generation")
    print("=" * 60)
    
    valid_actors = ["Tom Cruise", "Julia Roberts", "Morgan Freeman"]
    batch_result = generator.batch_generate(valid_actors)
    
    print(f"\nBatch Results:")
    print(f"  Total: {batch_result['total']}")
    print(f"  Successful: {batch_result['successful']}")
    print(f"  Failed: {batch_result['failed']}")
    print(f"  Success Rate: {batch_result['success_rate']:.1%}")
    print(f"  Total Cost: ${batch_result['total_cost_usd']}")


if __name__ == "__main__":
    test_production_generator()