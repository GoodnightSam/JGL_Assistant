"""
Test the updated prompt with imperative callback (verb-first, no pronouns)
"""

from production_script_generator import ProductionScriptGenerator

# Initialize generator
generator = ProductionScriptGenerator(model_name="o3-2025-04-16")

# Test with an actor who has iconic catchphrases
print("Testing updated prompt with imperative callback format (verb-first, no pronouns)...")
print("=" * 60)

result = generator.generate_script("Arnold Schwarzenegger")

if result["success"]:
    print(f"✓ Script generated successfully")
    print(f"  Word count: {result['word_count']}")
    
    # Save the result
    filepath = generator.save_script(result)
    print(f"  Saved to: {filepath}")
    
    # Display the hook to see the signature callback
    if "hook" in result:
        print(f"\n\nHOOK Section:")
        print("-" * 60)
        print(result["hook"])
        print("-" * 60)
        
        # Check if it includes an imperative callback (should be 2-4 words, verb-first, no pronouns)
        hook_text = result["hook"]
        if "**" in hook_text and "let's get rollin'" in hook_text:
            # Extract the callback phrase
            import re
            callback_match = re.search(r'\*\*([^*]+), and let\'s get rollin\'\.\*\*', hook_text)
            if callback_match:
                callback = callback_match.group(1)
                word_count = len(callback.split())
                print(f"\n✓ Imperative callback found: '{callback}'")
                print(f"  Word count: {word_count} words")
                if 2 <= word_count <= 4:
                    print(f"  ✓ Meets 2-4 word requirement")
                else:
                    print(f"  ⚠️  Outside 2-4 word range")
                
                # Check if it's verb-first (basic check)
                first_word = callback.split()[0].lower()
                print(f"  First word: '{first_word}' (should be an imperative verb)")
                
                # Check for pronouns (should not have any)
                pronouns = ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'theirs']
                words = callback.lower().split()
                found_pronouns = [w for w in words if w in pronouns]
                if found_pronouns:
                    print(f"  ⚠️  Contains pronouns: {found_pronouns}")
                else:
                    print(f"  ✓ No pronouns found")
    
else:
    print(f"✗ Failed to generate script: {result['error']}")