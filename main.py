#!/usr/bin/env python3
"""
JGL Assistant - AI-Powered Biography Script Generator
Main entry point for the application.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from production_script_generator import ProductionScriptGenerator
from phonetic_generator import PhoneticScriptGenerator
from storyboard_generator import StoryboardGenerator
from music_plan_generator import MusicPlanGenerator
from folder_manager import ActorFolderManager
from cost_tracker import CostTracker, format_cost_summary
from step3_image_search import proceed_to_step3

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = "output"
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")


def ensure_directories():
    """Ensure output directories exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    Path(SCRIPTS_DIR).mkdir(exist_ok=True)


def save_script_as_txt(script_data, filepath, is_phonetic=False):
    """
    Save the script data as a formatted text file.
    
    Args:
        script_data: Dictionary containing the script data
        filepath: Full path where to save the file
        is_phonetic: Whether this is a phonetic script
        
    Returns:
        Path to the saved file
    """
    if not script_data.get("success"):
        raise ValueError("Cannot save failed script generation")
    
    # Get the content
    if is_phonetic:
        content = script_data.get('phonetic_script', '')
    else:
        content = script_data.get('full_script', '')
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def print_header():
    """Print application header."""
    print("\n" + "=" * 60)
    print("JGL ASSISTANT - Biography Script Generator")
    print("Using OpenAI o3 Model with High Reasoning")
    print("=" * 60 + "\n")


def get_actor_name():
    """Get actor name from user with validation."""
    while True:
        actor_name = input("Enter actor name (or 'quit' to exit): ").strip()
        
        if actor_name.lower() == 'quit':
            return None
            
        if not actor_name:
            print("❌ Actor name cannot be empty. Please try again.")
            continue
            
        # Basic validation - allow letters, spaces, hyphens, apostrophes, periods
        if all(c.isalpha() or c in " -'." for c in actor_name):
            return actor_name
        else:
            print("❌ Actor name contains invalid characters. Please use only letters, spaces, hyphens, and apostrophes.")
            continue


def check_existing_script(folder_manager, actor_name):
    """
    Check if script exists and prompt user for action.
    
    Args:
        folder_manager: ActorFolderManager instance
        actor_name: The actor's name
        
    Returns:
        Tuple of (action, existing_script_path)
        action can be: 'use_existing', 'generate_new', or 'new_actor'
    """
    existing_script = folder_manager.get_latest_script(actor_name)
    
    if existing_script:
        # Get script info
        script_time = datetime.fromtimestamp(os.path.getmtime(existing_script))
        time_str = script_time.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n📁 Found existing script for {actor_name}")
        print(f"   Created: {time_str}")
        print("\nOptions:")
        print("1. Use existing script and proceed to Step 2")
        print("2. Generate new script (will overwrite existing)")
        print("3. Cancel")
        
        while True:
            choice = input("\nSelect option (1-3): ").strip()
            if choice == '1':
                return 'use_existing', existing_script
            elif choice == '2':
                confirm = input("⚠️  This will overwrite the existing script. Continue? (y/n): ").strip().lower()
                if confirm == 'y':
                    return 'generate_new', None
                else:
                    print("Cancelled.")
                    continue
            elif choice == '3':
                return 'cancel', None
            else:
                print("Invalid option. Please enter 1, 2, or 3.")
    
    return 'new_actor', None


def check_existing_storyboard(folder_manager, actor_name):
    """
    Check if storyboard exists and prompt user for action.
    
    Args:
        folder_manager: ActorFolderManager instance
        actor_name: The actor's name
        
    Returns:
        Tuple of (action, existing_storyboard_path)
        action can be: 'use_existing', 'generate_new', or 'no_storyboard'
    """
    existing_storyboard = folder_manager.get_latest_storyboard(actor_name)
    
    if existing_storyboard:
        # Get storyboard info
        sb_time = datetime.fromtimestamp(os.path.getmtime(existing_storyboard))
        time_str = sb_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Load and show basic info
        try:
            with open(existing_storyboard, 'r') as f:
                sb_data = json.load(f)
            shot_count = sb_data.get('shot_count', len(sb_data.get('storyboard', [])))
            
            print(f"\n📋 Found existing storyboard for {actor_name}")
            print(f"   Created: {time_str}")
            print(f"   Shots: {shot_count}")
            print("\nOptions:")
            print("1. Use existing storyboard (proceed to Step 3)")
            print("2. Generate new storyboard (will overwrite existing)")
            print("3. Skip storyboard")
            
            while True:
                choice = input("\nSelect option (1-3): ").strip()
                if choice == '1':
                    return 'use_existing', existing_storyboard
                elif choice == '2':
                    confirm = input("⚠️  This will overwrite the existing storyboard. Continue? (y/n): ").strip().lower()
                    if confirm == 'y':
                        return 'generate_new', None
                    else:
                        print("Cancelled.")
                        continue
                elif choice == '3':
                    return 'skip', None
                else:
                    print("Invalid option. Please enter 1, 2, or 3.")
        except Exception as e:
            logger.warning(f"Could not read existing storyboard: {e}")
    
    return 'no_storyboard', None


def check_existing_music_plan(folder_manager, actor_name):
    """
    Check if music plan exists and prompt user for action.
    
    Args:
        folder_manager: ActorFolderManager instance
        actor_name: The actor's name
        
    Returns:
        Tuple of (action, existing_music_plan_path)
        action can be: 'use_existing', 'generate_new', or 'no_music_plan'
    """
    existing_music_plan = folder_manager.get_latest_music_plan(actor_name)
    
    if existing_music_plan:
        # Get music plan info
        mp_time = datetime.fromtimestamp(os.path.getmtime(existing_music_plan))
        time_str = mp_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Load and show basic info
        try:
            with open(existing_music_plan, 'r') as f:
                mp_data = json.load(f)
            prompt_count = len(mp_data.get('music_prompts', []))
            
            print(f"\n🎵 Found existing music plan for {actor_name}")
            print(f"   Created: {time_str}")
            print(f"   Music prompts: {prompt_count}")
            print("\nOptions:")
            print("1. Use existing music plan")
            print("2. Generate new music plan (will overwrite existing)")
            print("3. Skip music plan")
            
            while True:
                choice = input("\nSelect option (1-3): ").strip()
                if choice == '1':
                    return 'use_existing', existing_music_plan
                elif choice == '2':
                    confirm = input("⚠️  This will overwrite the existing music plan. Continue? (y/n): ").strip().lower()
                    if confirm == 'y':
                        return 'generate_new', None
                    else:
                        print("Cancelled.")
                        continue
                elif choice == '3':
                    return 'skip', None
                else:
                    print("Invalid option. Please enter 1, 2, or 3.")
        except Exception as e:
            logger.warning(f"Could not read existing music plan: {e}")
    
    return 'no_music_plan', None


def proceed_to_step2(storyboard_generator, music_plan_generator, folder_manager, actor_name, script_path, cost_tracker=None):
    """
    Execute Step 2: Generate storyboard from script.
    
    Args:
        storyboard_generator: StoryboardGenerator instance
        music_plan_generator: MusicPlanGenerator instance
        folder_manager: ActorFolderManager instance
        actor_name: The actor's name
        script_path: Path to the script file
        cost_tracker: Optional CostTracker instance
        
    Returns:
        Success boolean
    """
    print(f"\n🎬 Step 2: Generating storyboard for {actor_name}...")
    print("This may take 60-120 seconds...\n")
    
    try:
        # Check for existing storyboard
        action, existing_sb_path = check_existing_storyboard(folder_manager, actor_name)
        
        if action == 'use_existing':
            print(f"\n✓ Using existing storyboard")
            print(f"   Location: {existing_sb_path}")
            # Continue to music plan even with existing storyboard
        elif action == 'skip':
            print("\n⏭️  Skipping storyboard generation")
            # Continue to Step 3 without storyboard
            paths = folder_manager.get_script_paths(actor_name)
            proceed_to_step3(folder_manager, actor_name, None, cost_tracker)
            return True
        else:
            # Extract script content
            script_content = storyboard_generator.extract_script_content(script_path)
            
            # Generate storyboard
            result = storyboard_generator.generate_storyboard(script_content, actor_name)
            
            if result.get("success"):
                print(f"✓ Storyboard generated successfully!")
                print(f"  Shot count: {result['shot_count']} shots")
                print(f"  Generation time: {result.get('generation_time', 'N/A')}s")
            
                # Save storyboard
                paths = folder_manager.get_script_paths(actor_name)
                storyboard_path = paths['storyboard']
            
                storyboard_data = {
                    "actor_name": actor_name,
                    "storyboard": result['storyboard'],
                    "shot_count": result['shot_count'],
                    "generation_metadata": {
                        "model": result['model_used'],
                        "timestamp": result['timestamp'],
                        "generation_time": result['generation_time'],
                        "usage": result.get('usage', {}),
                        "valid": result.get('valid', True),
                        "validation_issues": result.get('validation_issues', [])
                    }
                }
            
                with open(storyboard_path, 'w', encoding='utf-8') as f:
                    json.dump(storyboard_data, f, indent=2)
                print(f"  Saved to: {storyboard_path}")
            
                # Show cost analysis
                if result.get("usage"):
                    cost = storyboard_generator.estimate_cost(result)
                    usage = result["usage"]
                    print("\n💰 Storyboard Generation Cost:")
                    print(f"  Token Usage:")
                    print(f"    - Input tokens: {usage.get('input_tokens', 'N/A'):,}")
                    print(f"    - Output tokens: {usage.get('output_tokens', 'N/A'):,}")
                    if usage.get('reasoning_tokens'):
                        print(f"    - Reasoning tokens: {usage.get('reasoning_tokens', 'N/A'):,}")
                    print(f"  Cost: {cost['total_cost_usd']}")
                
                    # Track storyboard cost if tracker available
                    if cost_tracker:
                        cost_tracker.add_entry(
                            step="storyboard_generation",
                            model=result.get('model_used', 'o3-2025-04-16'),
                            cost=cost['total_cost'],
                            usage_data=result.get('usage'),
                            additional_info={
                                "shot_count": result.get('shot_count'),
                                "generation_time": result.get('generation_time'),
                                "reasoning_effort": "high"
                            }
                        )
            
                # Show validation warnings if any
                if result.get("valid") is False:
                    print("\n⚠️  Validation warnings:")
                    for issue in result.get("validation_issues", []):
                        print(f"  - {issue}")
            else:
                print(f"❌ Failed to generate storyboard: {result.get('error', 'Unknown error')}")
                return False
        
        # At this point we either have a new storyboard or are using an existing one
        # Continue to music plan generation
        print("\n🎵 Step 2B: Generating music plan...")
        print("This may take 30-60 seconds...\n")
        
        # Check for existing music plan
        mp_action, existing_mp_path = check_existing_music_plan(folder_manager, actor_name)
            
        if mp_action == 'use_existing':
            print(f"\n✓ Using existing music plan")
            print(f"   Location: {existing_mp_path}")
        elif mp_action == 'skip':
            print("\n⏭️  Skipping music plan generation")
        else:
            # Generate new music plan
            # Extract script content
            script_content = storyboard_generator.extract_script_content(script_path)
            
            # Generate music plan
            mp_result = music_plan_generator.generate_music_plan(script_content, actor_name)
                
            if mp_result.get("success"):
                print(f"✓ Music plan generated successfully!")
                print(f"  Music prompts: {len(mp_result.get('music_prompts', []))}")
                print(f"  Generation time: {mp_result.get('generation_time', 'N/A')}s")
                    
                # Save music plan
                paths = folder_manager.get_script_paths(actor_name)
                music_plan_path = paths['music_plan']
                    
                music_plan_data = {
                    "actor_name": actor_name,
                    "music_prompts": mp_result['music_prompts'],
                    "generation_metadata": {
                        "model": mp_result['model_used'],
                        "timestamp": mp_result['timestamp'],
                        "generation_time": mp_result['generation_time'],
                        "usage": mp_result.get('usage', {}),
                        "valid": mp_result.get('valid', True),
                        "validation_issues": mp_result.get('validation_issues', [])
                    }
                }
                    
                with open(music_plan_path, 'w', encoding='utf-8') as f:
                    json.dump(music_plan_data, f, indent=2)
                print(f"  Saved to: {music_plan_path}")
                    
                # Show cost analysis
                if mp_result.get("usage"):
                    mp_cost = music_plan_generator.estimate_cost(mp_result)
                    usage = mp_result["usage"]
                    print("\n💰 Music Plan Generation Cost:")
                    print(f"  Token Usage:")
                    print(f"    - Input tokens: {usage.get('input_tokens', 'N/A'):,}")
                    print(f"    - Output tokens: {usage.get('output_tokens', 'N/A'):,}")
                    if usage.get('reasoning_tokens'):
                        print(f"    - Reasoning tokens: {usage.get('reasoning_tokens', 'N/A'):,}")
                    print(f"  Cost: {mp_cost['total_cost_usd']}")
                        
                    # Track music plan cost if tracker available
                    if cost_tracker:
                        cost_tracker.add_entry(
                            step="music_plan_generation",
                            model=mp_result.get('model_used', 'o3-2025-04-16'),
                            cost=mp_cost['total_cost'],
                            usage_data=mp_result.get('usage'),
                            additional_info={
                                "prompt_count": len(mp_result.get('music_prompts', [])),
                                "generation_time": mp_result.get('generation_time'),
                                "reasoning_effort": "high"
                            }
                        )
                    
                # Show validation warnings if any
                if mp_result.get("valid") is False:
                    print("\n⚠️  Validation warnings:")
                    for issue in mp_result.get("validation_issues", []):
                        print(f"  - {issue}")
            else:
                print(f"❌ Failed to generate music plan: {mp_result.get('error', 'Unknown error')}")
        
        # Show final cost summary if tracker available
        if cost_tracker:
            print("\n📊 Final Cost Tracking Summary:")
            summary = format_cost_summary(cost_tracker)
            for line in summary.split('\n'):
                print(f"  {line}")
        
        # Continue to Step 3: Image Search
        paths = folder_manager.get_script_paths(actor_name)
        storyboard_path = paths['storyboard']
        if os.path.exists(storyboard_path):
            proceed_to_step3(folder_manager, actor_name, storyboard_path, cost_tracker)
        else:
            print("\n⚠️  No storyboard found. Skipping image search.")
        
        print("\n🚀 Ready for Step 4 (AI image generation - coming soon...)")
        return True
            
    except Exception as e:
        print(f"❌ Error in Step 2: {e}")
        logger.error(f"Step 2 error: {e}", exc_info=True)
        return False


def main():
    """Main application loop."""
    # Ensure directories exist
    ensure_directories()
    
    # Print header
    print_header()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your API key in the .env file or as an environment variable.")
        sys.exit(1)
    
    # Initialize generators and folder manager
    print("Initializing generators...")
    try:
        generator = ProductionScriptGenerator(model_name="o3-2025-04-16", use_fallback=True)
        phonetic_generator = PhoneticScriptGenerator()
        storyboard_generator = StoryboardGenerator()
        music_plan_generator = MusicPlanGenerator()
        folder_manager = ActorFolderManager()
        print("✓ All generators ready\n")
    except Exception as e:
        print(f"❌ Failed to initialize generators: {e}")
        sys.exit(1)
    
    # Main loop
    while True:
        # Get actor name
        actor_name = get_actor_name()
        if actor_name is None:
            print("\nThank you for using JGL Assistant!")
            break
        
        # Check for existing script
        action, existing_script_path = check_existing_script(folder_manager, actor_name)
        
        if action == 'cancel':
            print("\n" + "-" * 60)
            print("Ready for next actor or type 'quit' to exit.")
            print("-" * 60 + "\n")
            continue
        
        # Get script paths for this actor
        paths = folder_manager.get_script_paths(actor_name)
        
        # Initialize cost tracker for this actor
        cost_tracker = CostTracker(paths['cost_tracking'])
        cost_tracker.set_actor_name(actor_name)
        
        # Handle existing script
        if action == 'use_existing':
            print(f"\n✓ Using existing script for {actor_name}")
            # Initialize cost tracker for existing actor
            paths = folder_manager.get_script_paths(actor_name)
            cost_tracker = CostTracker(paths['cost_tracking'])
            cost_tracker.set_actor_name(actor_name)
            
            # Proceed to Step 2
            proceed_to_step2(storyboard_generator, music_plan_generator, folder_manager, actor_name, existing_script_path, cost_tracker)
            
            print("\n" + "-" * 60)
            print("Ready for next actor or type 'quit' to exit.")
            print("-" * 60 + "\n")
            continue
        
        # Generate new script
        print(f"\n📝 Generating script for {actor_name}...")
        print("This may take 30-60 seconds...\n")
        
        try:
            # Generate the original script
            result = generator.generate_script_with_retry(actor_name, max_retries=2)
            
            if result.get("success"):
                print(f"✓ Original script generated successfully!")
                print(f"  Word count: {result['word_count']} words")
                print(f"  Generation time: {result.get('generation_time', 'N/A')}s")
                
                # Save original script to actor folder
                try:
                    txt_path = save_script_as_txt(result, paths['script'], is_phonetic=False)
                    print(f"  Saved to: {txt_path}")
                    
                    # Save JSON to actor folder
                    with open(paths['json'], 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2)
                    print(f"  JSON backup: {paths['json']}")
                    
                except Exception as e:
                    print(f"❌ Error saving original script: {e}")
                
                # Generate phonetic version
                print(f"\n📝 Generating phonetic script...")
                try:
                    phonetic_result = phonetic_generator.generate_with_retry(
                        result['full_script'], 
                        actor_name,
                        max_retries=2
                    )
                    
                    if phonetic_result.get("success"):
                        print(f"✓ Phonetic script generated successfully!")
                        print(f"  Generation time: {phonetic_result.get('generation_time', 'N/A')}s")
                        
                        # Save phonetic script to actor folder
                        phonetic_path = save_script_as_txt(phonetic_result, paths['phonetic'], is_phonetic=True)
                        print(f"  Saved to: {phonetic_path}")
                        
                    else:
                        print(f"❌ Failed to generate phonetic script: {phonetic_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Error generating phonetic script: {e}")
                
                # Show actual cost tracking
                cost = generator.estimate_cost(result)
                print("\n💰 Cost Analysis:")
                
                # Check if we have actual token usage
                if result.get("usage") and result["usage"].get("input_tokens"):
                    usage = result["usage"]
                    print(f"  Token Usage (from OpenAI API):")
                    print(f"    - Input tokens: {usage.get('input_tokens', 'N/A'):,}")
                    print(f"    - Output tokens: {usage.get('output_tokens', 'N/A'):,}")
                    if usage.get('reasoning_tokens'):
                        print(f"    - Reasoning tokens: {usage.get('reasoning_tokens', 'N/A'):,}")
                        reasoning_pct = (usage['reasoning_tokens'] / usage['output_tokens']) * 100
                        print(f"    - Reasoning percentage: {reasoning_pct:.1f}%")
                    print(f"  Script generation cost: {cost['total_cost_usd']}")
                else:
                    print(f"  Estimated script cost: {cost['total_cost_usd']}")
                
                # Track script generation cost
                cost_tracker.add_entry(
                    step="script_generation",
                    model=result.get('model_used', 'o3-2025-04-16'),
                    cost=cost['total_cost'],
                    usage_data=result.get('usage'),
                    additional_info={
                        "word_count": result.get('word_count'),
                        "generation_time": result.get('generation_time'),
                        "reasoning_effort": "high"
                    }
                )
                
                # Track phonetic cost if generated
                if phonetic_result and phonetic_result.get("success"):
                    phonetic_cost = 0.001  # Rough estimate for o4-mini
                    cost_tracker.add_entry(
                        step="phonetic_conversion",
                        model="o4-mini",
                        cost=phonetic_cost,
                        additional_info={
                            "generation_time": phonetic_result.get('generation_time')
                        }
                    )
                    print(f"  Phonetic conversion cost: ~${phonetic_cost:.4f}")
                
                print(f"  Total cost: ${cost_tracker.get_total_cost():.4f}")
                
                # Show validation info if any (but don't treat as failure)
                if result.get("validation_issues"):
                    print("\n📝 Script notes:")
                    for issue in result.get("validation_issues", []):
                        print(f"  - {issue}")
                
                # Ready for Step 2
                print("\n✅ Script generation complete!")
                print(f"📁 Actor folder: {paths['folder']}")
                
                # Proceed to Step 2
                proceed_to_step2(storyboard_generator, music_plan_generator, folder_manager, actor_name, paths['script'], cost_tracker)
                
                # Show cost summary
                print("\n📊 Cost Tracking Summary:")
                summary = format_cost_summary(cost_tracker)
                for line in summary.split('\n'):
                    print(f"  {line}")
                
            else:
                print(f"❌ Failed to generate script: {result.get('error', 'Unknown error')}")
                if result.get('error_type') == 'rate_limit':
                    print("💡 Tip: Wait a few minutes before trying again.")
                elif result.get('error_type') == 'authentication':
                    print("💡 Tip: Check your API key in the .env file.")
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("\n" + "-" * 60)
        print("Ready for next script or type 'quit' to exit.")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()