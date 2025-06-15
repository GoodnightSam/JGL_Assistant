#!/usr/bin/env python3
"""
JGL Assistant - AI-Powered Biography Script Generator
Main entry point for the application.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from production_script_generator import ProductionScriptGenerator
from phonetic_generator import PhoneticScriptGenerator
from folder_manager import ActorFolderManager

# Load environment variables
load_dotenv()

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
    print("Initializing script generators...")
    try:
        generator = ProductionScriptGenerator(model_name="o3-2025-04-16", use_fallback=True)
        phonetic_generator = PhoneticScriptGenerator()
        folder_manager = ActorFolderManager()
        print("✓ Script generators ready\n")
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
        
        # Handle existing script
        if action == 'use_existing':
            print(f"\n✓ Using existing script for {actor_name}")
            # Load existing script data
            try:
                with open(existing_script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # TODO: Proceed to Step 2
                print("\n🚀 Ready for Step 2 (coming soon...)")
                print(f"   Script location: {existing_script_path}")
                print(f"   Actor folder: {paths['folder']}")
                
            except Exception as e:
                print(f"❌ Error loading existing script: {e}")
            
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
                
                print(f"  Phonetic conversion cost: ~$0.001")
                print(f"  Total cost: ~${cost['total_cost'] + 0.001:.4f}")
                
                # Show validation warnings if any
                if result.get("valid") is False:
                    print("\n⚠️  Validation warnings:")
                    for issue in result.get("validation_issues", []):
                        print(f"  - {issue}")
                
                # Ready for Step 2
                print("\n✅ Script generation complete!")
                print(f"📁 Actor folder: {paths['folder']}")
                print("\n🚀 Ready for Step 2 (coming soon...)")
                
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