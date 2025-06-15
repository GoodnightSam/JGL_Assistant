"""
Test the updated prompt with the new question format
"""

from production_script_generator import ProductionScriptGenerator
import json

# Initialize generator
generator = ProductionScriptGenerator(model_name="o3-2025-04-16")

# Test with one actor
print("Testing updated prompt with natural question format...")
print("=" * 60)

result = generator.generate_script("Nicolas Cage")

if result["success"]:
    print(f"✓ Script generated successfully")
    print(f"  Word count: {result['word_count']}")
    print(f"  Generation time: {result.get('generation_time', 'N/A')}s")
    
    # Save the result
    filepath = generator.save_script(result)
    print(f"  Saved to: {filepath}")
    
    # Display a preview of the script to check for the question
    script_text = result["full_script"]
    
    # Find the section around 80-90 seconds (approximately 200-250 words in)
    words = script_text.split()
    if len(words) > 250:
        # Get roughly the 200-250 word range
        preview_start = 200
        preview_end = min(300, len(words))
        preview = ' '.join(words[preview_start:preview_end])
        
        print(f"\n\nPreview of script around 80-90 second mark:")
        print("-" * 60)
        print(f"...{preview}...")
        print("-" * 60)
        
        # Check if there's a question mark in this section
        if '?' in preview:
            print("✓ Question found in the expected range!")
        else:
            print("⚠️  No question mark found in the preview range")
    
else:
    print(f"✗ Failed to generate script: {result['error']}")