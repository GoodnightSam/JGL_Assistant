#!/usr/bin/env python3
"""
Step 3: Image Search Integration
Handles Google Image searches based on storyboard queries.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from image_searcher_enhanced_v2 import EnhancedImageSearcher
from folder_manager import ActorFolderManager

logger = logging.getLogger(__name__)


def check_existing_images(folder_manager: ActorFolderManager, actor_name: str, 
                         storyboard_path: str) -> Dict[str, Any]:
    """
    Check existing images and compare with storyboard requirements.
    
    Args:
        folder_manager: ActorFolderManager instance
        actor_name: Actor name
        storyboard_path: Path to storyboard JSON
        
    Returns:
        Dictionary with image status
    """
    # Get existing images info
    existing = folder_manager.check_existing_images(actor_name)
    
    # Load storyboard to get total shots
    with open(storyboard_path, 'r') as f:
        storyboard_data = json.load(f)
    
    total_shots = len(storyboard_data.get("storyboard", []))
    shots_with_images = len(existing["shots_with_images"])
    shots_missing = total_shots - shots_with_images
    
    return {
        "has_images": existing["has_images"],
        "total_images": existing["total_images"],
        "total_shots": total_shots,
        "shots_with_images": shots_with_images,
        "shots_missing": shots_missing,
        "complete": shots_missing == 0,
        "existing_shots": existing["shots_with_images"]
    }


def display_image_status(status: Dict[str, Any]) -> None:
    """Display current image status to user."""
    print(f"\n📸 Image Status:")
    print(f"   Total shots: {status['total_shots']}")
    print(f"   Shots with images: {status['shots_with_images']}")
    print(f"   Missing images: {status['shots_missing']}")
    print(f"   Total image files: {status['total_images']}")
    
    if status['complete']:
        print("   ✓ All shots have images")
    else:
        print(f"   ⚠️  {status['shots_missing']} shots need images")


def prompt_image_action(status: Dict[str, Any]) -> str:
    """
    Prompt user for action based on existing images.
    
    Returns:
        Action: 'use_existing', 'download_missing', 'download_all', 'skip'
    """
    if not status['has_images']:
        # No existing images
        print("\nNo existing images found.")
        print("Options:")
        print("1. Download all images")
        print("2. Skip image download")
        
        while True:
            choice = input("\nSelect option (1-2): ").strip()
            if choice == '1':
                return 'download_all'
            elif choice == '2':
                return 'skip'
            else:
                print("Invalid option. Please enter 1 or 2.")
    
    elif status['complete']:
        # All images exist
        print("\nAll shots already have images.")
        print("Options:")
        print("1. Use existing images")
        print("2. Re-download all images (will overwrite)")
        print("3. Skip to next step")
        
        while True:
            choice = input("\nSelect option (1-3): ").strip()
            if choice == '1':
                return 'use_existing'
            elif choice == '2':
                confirm = input("⚠️  This will overwrite existing images. Continue? (y/n): ").strip().lower()
                if confirm == 'y':
                    return 'download_all'
                else:
                    continue
            elif choice == '3':
                return 'skip'
            else:
                print("Invalid option. Please enter 1, 2, or 3.")
    
    else:
        # Partial images exist
        print(f"\nSome images exist ({status['shots_with_images']}/{status['total_shots']} shots).")
        print("Options:")
        print("1. Download missing images only")
        print("2. Re-download all images (will overwrite)")
        print("3. Use existing images as-is")
        print("4. Skip to next step")
        
        while True:
            choice = input("\nSelect option (1-4): ").strip()
            if choice == '1':
                return 'download_missing'
            elif choice == '2':
                confirm = input("⚠️  This will overwrite existing images. Continue? (y/n): ").strip().lower()
                if confirm == 'y':
                    return 'download_all'
                else:
                    continue
            elif choice == '3':
                return 'use_existing'
            elif choice == '4':
                return 'skip'
            else:
                print("Invalid option. Please enter 1, 2, 3, or 4.")


def proceed_to_step3(folder_manager: ActorFolderManager, actor_name: str, 
                    storyboard_path: str, cost_tracker=None) -> bool:
    """
    Execute Step 3: Download images based on storyboard searches.
    
    Args:
        folder_manager: ActorFolderManager instance
        actor_name: Actor name
        storyboard_path: Path to storyboard JSON
        cost_tracker: Optional cost tracker
        
    Returns:
        Success boolean
    """
    print(f"\n🖼️  Step 3: Image Search and Download for {actor_name}")
    print("Using Google Custom Search API")
    
    try:
        # Check for API credentials
        if not os.getenv("GOOGLE_API_KEY"):
            print("\n❌ Error: GOOGLE_API_KEY not found in .env file")
            print("\nTo get your Google API credentials:")
            print("1. Go to: https://console.cloud.google.com/")
            print("2. Create/select a project")
            print("3. Enable 'Custom Search API'")
            print("4. Create credentials (API Key)")
            print("5. Add to .env: GOOGLE_API_KEY=your_key_here")
            print("\nAlso needed: GOOGLE_SEARCH_ENGINE_ID")
            print("1. Go to: https://programmablesearchengine.google.com/")
            print("2. Create a search engine")
            print("3. Enable 'Image search' and 'Search the entire web'")
            print("4. Copy the Search Engine ID")
            print("5. Add to .env: GOOGLE_SEARCH_ENGINE_ID=your_id_here")
            return False
        
        # Initialize enhanced image searcher
        try:
            searcher = EnhancedImageSearcher()
        except ValueError as e:
            print(f"\n❌ Configuration error: {e}")
            return False
        
        # Show current usage
        usage = searcher.get_usage_summary()
        print(f"\n📊 API Usage Today: {usage['searches_today']}/{usage['limit']} searches")
        print(f"   Remaining: {usage['remaining']} searches")
        
        # Check existing images
        paths = folder_manager.get_script_paths(actor_name)
        images_dir = paths['images_dir']
        image_metadata_path = paths['image_metadata']
        
        status = check_existing_images(folder_manager, actor_name, storyboard_path)
        display_image_status(status)
        
        # Get user action
        action = prompt_image_action(status)
        
        if action == 'skip' or action == 'use_existing':
            print(f"\n{'✓ Using existing images' if action == 'use_existing' else '⏭️  Skipping image download'}")
            return True
        
        # Determine skip_existing based on action
        skip_existing = (action == 'download_missing')
        
        print(f"\n🔍 Starting image download...")
        print(f"   Mode: {action}")
        print("   This may take several minutes...\n")
        
        # Process images
        results = searcher.process_storyboard_images(
            storyboard_path=storyboard_path,
            actor_name=actor_name,
            images_dir=images_dir,
            skip_existing=skip_existing
        )
        
        # Save metadata
        with open(image_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Display results
        print(f"\n✓ Image download complete!")
        print(f"   Processed shots: {results['processed_shots']}")
        print(f"   Skipped shots: {results.get('skipped_shots', 0)}")
        print(f"   Total download attempts: {results.get('total_downloads', 0)}")
        print(f"   Successful downloads: {results.get('successful_downloads', 0)}")
        print(f"   Failed downloads: {results.get('failed_downloads', 0)}")
        print(f"   Search errors: {results.get('search_errors', 0)}")
        
        # Show domain statistics if there were failures
        failed_domains = results.get('domain_statistics', {}).get('failed_domains', {})
        if failed_domains:
            print("\n📈 Domain failure statistics:")
            for domain, count in sorted(failed_domains.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {domain}: {count} failures")
        
        if results.get('limit_reached'):
            print("\n⚠️  Daily API limit reached. Some shots may be incomplete.")
        
        print(f"\n📁 Images saved to: {images_dir}")
        print(f"📋 Metadata saved to: {image_metadata_path}")
        
        # Show final usage
        final_usage = searcher.get_usage_summary()
        print(f"\n📊 Updated API Usage: {final_usage['searches_today']}/{final_usage['limit']} searches")
        
        # Note: Google API is free for first 100 searches/day, so no cost tracking needed
        # But we could track usage statistics if desired
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in Step 3: {e}")
        logger.error(f"Step 3 error: {e}", exc_info=True)
        return False