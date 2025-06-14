#!/usr/bin/env python3
"""
JGL Assistant - AI-Powered Biography Script Generator
Main entry point for the application.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from production_script_generator import ProductionScriptGenerator
from phonetic_generator import PhoneticScriptGenerator

# Load environment variables
load_dotenv()

# Constants
OUTPUT_DIR = "output"
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")


def ensure_directories():
    """Ensure output directories exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    Path(SCRIPTS_DIR).mkdir(exist_ok=True)


def save_script_as_txt(script_data, output_dir=SCRIPTS_DIR, is_phonetic=False):
    """
    Save the script data as a formatted text file.
    
    Args:
        script_data: Dictionary containing the script data
        output_dir: Directory to save the file
        is_phonetic: Whether this is a phonetic script
        
    Returns:
        Path to the saved file
    """
    if not script_data.get("success"):
        raise ValueError("Cannot save failed script generation")
    
    # Generate filename
    actor_slug = script_data['actor_name'].lower().replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_type = "PHONETIC_script" if is_phonetic else "script"
    filename = f"{actor_slug}_{script_type}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
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
    print("Using OpenAI o3 Model")
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
    
    # Initialize generators
    print("Initializing script generators...")
    try:
        generator = ProductionScriptGenerator(model_name="o3-2025-04-16", use_fallback=True)
        phonetic_generator = PhoneticScriptGenerator()
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
        
        # Generate script
        print(f"\n📝 Generating script for {actor_name}...")
        print("This may take 30-60 seconds...\n")
        
        try:
            # Generate the original script
            result = generator.generate_script_with_retry(actor_name, max_retries=2)
            
            if result.get("success"):
                print(f"✓ Original script generated successfully!")
                print(f"  Word count: {result['word_count']} words")
                print(f"  Generation time: {result.get('generation_time', 'N/A')}s")
                
                # Save original script
                try:
                    txt_path = save_script_as_txt(result, is_phonetic=False)
                    print(f"  Saved to: {txt_path}")
                    
                    # Also save JSON for debugging
                    json_path = generator.save_script(result)
                    print(f"  JSON backup: {json_path}")
                    
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
                        
                        # Save phonetic script
                        phonetic_path = save_script_as_txt(phonetic_result, is_phonetic=True)
                        print(f"  Saved to: {phonetic_path}")
                        
                    else:
                        print(f"❌ Failed to generate phonetic script: {phonetic_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Error generating phonetic script: {e}")
                
                # Show cost estimate for both
                cost = generator.estimate_cost(result)
                print(f"\n💰 Total estimated cost: {cost['total_cost_usd']} (original) + ~$0.001 (phonetic)")
                
                # Show validation warnings if any
                if result.get("valid") is False:
                    print("\n⚠️  Validation warnings:")
                    for issue in result.get("validation_issues", []):
                        print(f"  - {issue}")
                
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