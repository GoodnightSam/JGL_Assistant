"""
Simple test for the updated prompt - just verify hook exists
"""

from production_script_generator import ProductionScriptGenerator

# Initialize generator
generator = ProductionScriptGenerator(model_name="o3-2025-04-16")

# Test with one actor
print("Testing updated prompt...")
print("=" * 60)

result = generator.generate_script("Robert Downey Jr.")

if result["success"]:
    print(f"✓ Script generated successfully")
    print(f"  Word count: {result['word_count']}")
    print(f"  Generation time: {result.get('generation_time', 'N/A')}s")
    
    # Check if hook exists
    if "hook" in result and result["hook"]:
        print(f"  ✓ Hook section found")
    else:
        print(f"  ⚠️  No hook section found")
    
    # Save the result
    filepath = generator.save_script(result)
    print(f"  Saved to: {filepath}")
    
else:
    print(f"✗ Failed to generate script: {result['error']}")