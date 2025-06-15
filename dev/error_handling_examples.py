"""
Error Handling Examples for Script Generation
============================================

This file demonstrates the key error handling patterns implemented
in the production script generator.
"""

from production_script_generator import ProductionScriptGenerator, ValidationError
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

def demonstrate_error_handling():
    """Demonstrate various error handling scenarios."""
    
    print("ERROR HANDLING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize generator with fallback enabled
    generator = ProductionScriptGenerator(use_fallback=True)
    
    # 1. Input Validation Errors
    print("\n1. INPUT VALIDATION ERRORS")
    print("-" * 40)
    
    invalid_names = [
        ("", "Empty name"),
        ("A", "Too short"),
        ("John123", "Contains numbers"),
        ("John@Doe", "Invalid characters"),
        ("x" * 101, "Too long"),
        (None, "None value"),
        (123, "Not a string"),
    ]
    
    for name, description in invalid_names:
        print(f"\nTesting {description}: '{name}'")
        result = generator.generate_script(name)
        if not result["success"]:
            print(f"✓ Correctly rejected: {result['error']}")
    
    # 2. API Error Handling with Retry
    print("\n\n2. RETRY LOGIC DEMONSTRATION")
    print("-" * 40)
    
    # This will use retry logic if there's a temporary failure
    result = generator.generate_script_with_retry("Tom Hanks", max_retries=3)
    if result["success"]:
        print(f"✓ Generated successfully after {result.get('attempts', 1)} attempt(s)")
    else:
        print(f"✗ Failed after retries: {result['error']}")
    
    # 3. Model Fallback
    print("\n\n3. MODEL FALLBACK")
    print("-" * 40)
    
    # Try to use a non-existent model, should fallback to o3-mini
    try:
        fallback_gen = ProductionScriptGenerator(
            model_name="o3-pro-2025-06-10",  # This model requires special access
            use_fallback=True
        )
        print(f"✓ Fallback successful, using: {fallback_gen.model_name}")
    except Exception as e:
        print(f"✗ Fallback failed: {e}")
    
    # 4. Output Validation
    print("\n\n4. OUTPUT VALIDATION")
    print("-" * 40)
    
    # Generate a script and check validation
    result = generator.generate_script("Brad Pitt")
    if result["success"]:
        if result.get("valid"):
            print("✓ Script passed all validation checks")
        else:
            print("⚠️  Script generated but has validation issues:")
            for issue in result.get("validation_issues", []):
                print(f"   - {issue}")
    
    # 5. Batch Processing with Error Recovery
    print("\n\n5. BATCH PROCESSING WITH ERROR RECOVERY")
    print("-" * 40)
    
    # Mix of valid and invalid actors
    mixed_actors = [
        "Leonardo DiCaprio",  # Valid
        "",  # Invalid - empty
        "Jennifer Lawrence",  # Valid
        "Actor@123",  # Invalid - bad characters
        "Chris Hemsworth",  # Valid
    ]
    
    batch_result = generator.batch_generate(mixed_actors, save_results=False)
    
    print(f"\nBatch Results:")
    print(f"  Total: {batch_result['total']}")
    print(f"  Successful: {batch_result['successful']}")
    print(f"  Failed: {batch_result['failed']}")
    print(f"  Success Rate: {batch_result['success_rate']:.1%}")
    
    # Show individual results
    print("\nIndividual Results:")
    for i, result in enumerate(batch_result['results']):
        status = "✓" if result['success'] else "✗"
        actor = mixed_actors[i] if i < len(mixed_actors) else "Unknown"
        error = f" - {result.get('error', '')}" if not result['success'] else ""
        print(f"  {status} {actor or '(empty)'}{error}")
    
    # 6. Cost Estimation with Error Handling
    print("\n\n6. SAFE COST ESTIMATION")
    print("-" * 40)
    
    # Even failed scripts can estimate costs
    test_data = {
        "word_count": 800,
        "model_used": "o3-2025-04-16"
    }
    
    cost = generator.estimate_cost(test_data)
    print(f"Estimated cost for 800-word script: {cost['total_cost_usd']}")
    
    # 7. File Saving with Error Recovery
    print("\n\n7. FILE SAVING ERROR HANDLING")
    print("-" * 40)
    
    # Generate and save a script
    result = generator.generate_script("Matt Damon")
    if result["success"]:
        try:
            filepath = generator.save_script(result)
            print(f"✓ Script saved successfully to: {filepath}")
        except Exception as e:
            print(f"✗ Failed to save script: {e}")


def demonstrate_custom_error_handling():
    """Show how to implement custom error handling."""
    
    print("\n\nCUSTOM ERROR HANDLING PATTERNS")
    print("=" * 60)
    
    generator = ProductionScriptGenerator()
    
    # Pattern 1: Handle specific error types
    def safe_generate_with_custom_handling(actor_name):
        try:
            result = generator.generate_script(actor_name)
            if result["success"]:
                return result
            else:
                # Handle specific error types
                error_type = result.get("error_type", "unknown")
                
                if error_type == "rate_limit":
                    print("⏳ Rate limit hit, waiting 60 seconds...")
                    # In production, wait and retry
                    return None
                    
                elif error_type == "authentication":
                    print("🔑 API key issue, please check credentials")
                    return None
                    
                elif error_type == "validation":
                    print(f"📝 Invalid input: {result['error']}")
                    return None
                    
                else:
                    print(f"❌ Unexpected error: {result['error']}")
                    return None
                    
        except Exception as e:
            print(f"💥 Critical error: {e}")
            # Log to monitoring system
            # Send alert if needed
            return None
    
    # Test the custom handler
    print("\nTesting custom error handler:")
    result = safe_generate_with_custom_handling("Will Smith")
    if result:
        print(f"✓ Generated successfully: {result['word_count']} words")
    
    # Pattern 2: Graceful degradation
    def generate_with_degradation(actor_name):
        """Try o3 first, then o3-mini, then return a template."""
        
        # Try primary model
        try:
            gen = ProductionScriptGenerator(model_name="o3-2025-04-16", use_fallback=False)
            result = gen.generate_script(actor_name)
            if result["success"]:
                print(f"✓ Generated with o3")
                return result
        except:
            pass
        
        # Try fallback model
        try:
            gen = ProductionScriptGenerator(model_name="o3-mini-2025-01-31", use_fallback=False)
            result = gen.generate_script(actor_name)
            if result["success"]:
                print(f"✓ Generated with o3-mini (fallback)")
                return result
        except:
            pass
        
        # Return template as last resort
        print(f"⚠️  Returning template for {actor_name}")
        return {
            "success": True,
            "actor_name": actor_name,
            "full_script": f"[TEMPLATE SCRIPT FOR {actor_name.upper()}]",
            "word_count": 0,
            "template": True
        }
    
    print("\n\nTesting graceful degradation:")
    result = generate_with_degradation("Scarlett Johansson")
    print(f"Result: {'Template' if result.get('template') else 'AI Generated'}")


if __name__ == "__main__":
    demonstrate_error_handling()
    demonstrate_custom_error_handling()