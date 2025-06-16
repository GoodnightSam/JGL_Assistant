#!/usr/bin/env python3
"""
Google Image search and download for video production.
Downloads images based on storyboard search queries.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ImageSearcher:
    """
    Searches and downloads images using Google Custom Search API.
    """
    
    # Google Custom Search API endpoint
    SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"
    
    # Free tier limit
    DAILY_SEARCH_LIMIT = 100
    
    # Results per search
    RESULTS_PER_SEARCH = 10
    
    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Initialize the image searcher.
        
        Args:
            api_key: Google API key (or from env GOOGLE_API_KEY)
            search_engine_id: Custom Search Engine ID (or from env GOOGLE_SEARCH_ENGINE_ID)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not self.api_key:
            raise ValueError("Google API key not provided. Set GOOGLE_API_KEY in .env file")
        if not self.search_engine_id:
            raise ValueError("Search Engine ID not provided. Set GOOGLE_SEARCH_ENGINE_ID in .env file")
        
        # Track daily usage
        self.usage_file = "output/.google_api_usage.json"
        self._load_usage()
        
        logger.info("Successfully initialized Google Image Searcher")
    
    def _load_usage(self):
        """Load or initialize daily usage tracking."""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            except:
                self.usage_data = {}
        else:
            self.usage_data = {}
        
        # Reset if new day
        today = date.today().isoformat()
        if self.usage_data.get("date") != today:
            self.usage_data = {
                "date": today,
                "searches": 0,
                "actors": {}
            }
            self._save_usage()
    
    def _save_usage(self):
        """Save usage data."""
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def _check_usage_limit(self) -> Tuple[bool, int]:
        """
        Check if we're within daily usage limit.
        
        Returns:
            Tuple of (within_limit, remaining_searches)
        """
        remaining = self.DAILY_SEARCH_LIMIT - self.usage_data.get("searches", 0)
        return remaining > 0, remaining
    
    def search_images(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results to retrieve (max 10)
            
        Returns:
            List of image results with metadata
        """
        within_limit, remaining = self._check_usage_limit()
        if not within_limit:
            raise Exception(f"Daily Google API limit reached ({self.DAILY_SEARCH_LIMIT} searches)")
        
        logger.info(f"Searching images for: {query} (remaining quota: {remaining})")
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "searchType": "image",
            "num": min(num_results, 10),  # Max 10 per request
            "safe": "active"  # Safe search
        }
        
        try:
            response = requests.get(self.SEARCH_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            # Update usage
            self.usage_data["searches"] += 1
            self._save_usage()
            
            data = response.json()
            items = data.get("items", [])
            
            # Extract relevant metadata
            results = []
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "displayLink": item.get("displayLink", ""),
                    "snippet": item.get("snippet", ""),
                    "mime": item.get("mime", ""),
                    "fileFormat": item.get("fileFormat", ""),
                    "image": item.get("image", {}),
                    "contextLink": item.get("image", {}).get("contextLink", ""),
                    "thumbnailLink": item.get("image", {}).get("thumbnailLink", "")
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} images for query: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching images: {e}")
            raise
    
    def download_image(self, url: str, save_path: str, timeout: int = 30) -> bool:
        """
        Download an image from URL.
        
        Args:
            url: Image URL
            save_path: Where to save the image
            timeout: Download timeout in seconds
            
        Returns:
            Success boolean
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def get_file_extension(self, url: str, mime_type: str = None) -> str:
        """
        Determine file extension from URL or MIME type.
        
        Args:
            url: Image URL
            mime_type: Optional MIME type
            
        Returns:
            File extension (e.g., '.jpg')
        """
        # Try from URL first
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in self.SUPPORTED_EXTENSIONS:
            if path.endswith(ext):
                return ext
        
        # Try from MIME type
        if mime_type:
            mime_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp',
                'image/bmp': '.bmp'
            }
            ext = mime_map.get(mime_type.lower())
            if ext:
                return ext
        
        # Default to .jpg
        return '.jpg'
    
    def process_storyboard_images(self, storyboard_path: str, actor_name: str, 
                                  images_dir: str, skip_existing: bool = True) -> Dict[str, Any]:
        """
        Process all image searches from a storyboard.
        
        Args:
            storyboard_path: Path to storyboard JSON
            actor_name: Actor name
            images_dir: Directory to save images
            skip_existing: Skip shots that already have images
            
        Returns:
            Dictionary with results and metadata
        """
        # Load storyboard
        with open(storyboard_path, 'r') as f:
            storyboard_data = json.load(f)
        
        storyboard = storyboard_data.get("storyboard", [])
        total_shots = len(storyboard)
        
        # Check existing images
        existing_shots = set()
        if skip_existing and os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                # Extract shot number from filename like "1B.jpg"
                if filename[:-5].endswith(('.jpg', '.png', '.gif', '.webp', '.bmp')):
                    try:
                        shot_num = int(filename.split('B')[0])
                        existing_shots.add(shot_num)
                    except:
                        pass
        
        # Process results
        results = {
            "actor_name": actor_name,
            "total_shots": total_shots,
            "processed_shots": 0,
            "skipped_shots": len(existing_shots),
            "downloaded_images": 0,
            "failed_downloads": 0,
            "search_errors": 0,
            "timestamp": datetime.now().isoformat(),
            "shot_metadata": {}
        }
        
        # Track actor usage
        if actor_name not in self.usage_data["actors"]:
            self.usage_data["actors"][actor_name] = 0
        
        # Process each shot
        for shot in storyboard:
            shot_num = shot.get("shot")
            if not shot_num:
                continue
            
            # Skip if existing
            if skip_existing and shot_num in existing_shots:
                logger.info(f"Skipping shot {shot_num} - images already exist")
                results["shot_metadata"][str(shot_num)] = {"status": "skipped"}
                continue
            
            # Get search query
            search_query = shot.get("image_search", "")
            if not search_query:
                logger.warning(f"No search query for shot {shot_num}")
                continue
            
            logger.info(f"Processing shot {shot_num}/{total_shots}: {search_query}")
            
            # Search images
            try:
                within_limit, remaining = self._check_usage_limit()
                if not within_limit:
                    logger.warning(f"Daily limit reached. Stopping at shot {shot_num}")
                    results["limit_reached"] = True
                    break
                
                search_results = self.search_images(search_query)
                results["processed_shots"] += 1
                
                # Track metadata for this shot
                shot_metadata = {
                    "search_query": search_query,
                    "search_results": len(search_results),
                    "images": []
                }
                
                # Download images (B, C, D, etc.)
                letter_index = 1  # Start at B (A reserved for AI-generated)
                for i, result in enumerate(search_results[:9]):  # Max 9 images (B-J)
                    letter = chr(65 + letter_index)  # B=66, C=67, etc.
                    
                    url = result.get("link")
                    if not url:
                        continue
                    
                    # Determine extension
                    ext = self.get_file_extension(url, result.get("mime"))
                    filename = f"{shot_num}{letter}{ext}"
                    save_path = os.path.join(images_dir, filename)
                    
                    # Download
                    success = self.download_image(url, save_path)
                    
                    if success:
                        results["downloaded_images"] += 1
                        # Save metadata
                        image_metadata = {
                            "filename": filename,
                            "url": url,
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "source": result.get("displayLink", ""),
                            "context_url": result.get("contextLink", ""),
                            "mime": result.get("mime", ""),
                            "download_success": True
                        }
                    else:
                        results["failed_downloads"] += 1
                        image_metadata = {
                            "filename": filename,
                            "url": url,
                            "download_success": False
                        }
                    
                    shot_metadata["images"].append(image_metadata)
                    letter_index += 1
                
                results["shot_metadata"][str(shot_num)] = shot_metadata
                
                # Update actor usage
                self.usage_data["actors"][actor_name] += 1
                self._save_usage()
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing shot {shot_num}: {e}")
                results["search_errors"] += 1
                results["shot_metadata"][str(shot_num)] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        within_limit, remaining = self._check_usage_limit()
        return {
            "date": self.usage_data.get("date"),
            "searches_today": self.usage_data.get("searches", 0),
            "remaining": remaining,
            "limit": self.DAILY_SEARCH_LIMIT,
            "within_limit": within_limit,
            "actors_processed": list(self.usage_data.get("actors", {}).keys())
        }