#!/usr/bin/env python3
"""
Enhanced Google Image search and download for video production.
Implements validation, retries, deduplication, and threading.
"""

import os
import json
import time
import logging
import requests
import hashlib
import io
import concurrent.futures
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple, Set
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from PIL import Image
import threading

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EnhancedImageSearcher:
    """
    Enhanced image searcher with validation, retries, and deduplication.
    """
    
    # Google Custom Search API endpoint
    SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"
    
    # Free tier limit
    DAILY_SEARCH_LIMIT = 100
    
    # Target images per shot
    IMAGES_PER_SHOT = 10
    
    # Max results to fetch per search (to ensure we get enough valid ones)
    MAX_SEARCH_RESULTS = 25
    
    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Domains known for watermarks
    WATERMARKED_DOMAINS = {
        'gettyimages.com', 'shutterstock.com', 'alamy.com', 'istockphoto.com',
        'dreamstime.com', '123rf.com', 'fotolia.com', 'depositphotos.com'
    }
    
    # Trusted domains (less likely to have issues)
    TRUSTED_DOMAINS = {
        'wikimedia.org', 'wikipedia.org', 'pexels.com', 'unsplash.com',
        'pixabay.com', 'flickr.com', 'archive.org'
    }
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """Initialize the enhanced image searcher."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not self.api_key:
            raise ValueError("Google API key not provided. Set GOOGLE_API_KEY in .env file")
        if not self.search_engine_id:
            raise ValueError("Search Engine ID not provided. Set GOOGLE_SEARCH_ENGINE_ID in .env file")
        
        # Initialize locks and tracking structures first
        self.failed_domains = {}
        self.failed_domains_lock = threading.Lock()
        self.image_hashes = set()
        self.hashes_lock = threading.Lock()
        
        # Track daily usage (must be after locks are initialized)
        self.usage_file = "output/.google_api_usage.json"
        self._load_usage()
        
        logger.info("Successfully initialized Enhanced Google Image Searcher")
    
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
                "actors": {},
                "failed_domains": {}
            }
            self._save_usage()
    
    def _save_usage(self):
        """Save usage data."""
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
        
        # Update failed domains in usage data
        with self.failed_domains_lock:
            self.usage_data["failed_domains"] = dict(self.failed_domains)
        
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current API usage summary."""
        self._load_usage()  # Refresh data
        return {
            "searches_today": self.usage_data.get("searches", 0),
            "limit": self.DAILY_SEARCH_LIMIT,
            "remaining": self.DAILY_SEARCH_LIMIT - self.usage_data.get("searches", 0),
            "date": self.usage_data.get("date", date.today().isoformat()),
            "actors_searched": list(self.usage_data.get("actors", {}).keys())
        }
    
    def _track_failed_domain(self, domain: str):
        """Track domains that fail frequently."""
        with self.failed_domains_lock:
            if domain not in self.failed_domains:
                self.failed_domains[domain] = 0
            self.failed_domains[domain] += 1
    
    def _get_domain_score(self, url: str) -> int:
        """Score a domain based on reliability and watermark likelihood."""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check if it's a known watermarked domain
            if any(wd in domain for wd in self.WATERMARKED_DOMAINS):
                return -10
            
            # Check if it's a trusted domain
            if any(td in domain for td in self.TRUSTED_DOMAINS):
                return 10
            
            # Check failure history
            failures = self.failed_domains.get(domain, 0)
            if failures > 5:
                return -5
            elif failures > 2:
                return -2
            
            return 0
        except:
            return 0
    
    def search_images_extended(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for more images using pagination to get up to MAX_SEARCH_RESULTS.
        
        Args:
            query: Search query
            
        Returns:
            List of image results with metadata
        """
        all_results = []
        start_index = 1
        
        # Google Custom Search returns max 10 results per request
        while len(all_results) < self.MAX_SEARCH_RESULTS:
            remaining = self.MAX_SEARCH_RESULTS - len(all_results)
            num_to_fetch = min(10, remaining)
            
            results = self.search_images(query, num_results=num_to_fetch, start_index=start_index)
            if not results:
                break
            
            all_results.extend(results)
            start_index += len(results)
            
            # Small delay between requests
            time.sleep(0.5)
        
        return all_results
    
    def search_images(self, query: str, num_results: int = 10, start_index: int = 1) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results to retrieve (max 10)
            start_index: Starting index for results
            
        Returns:
            List of image results with metadata
        """
        within_limit, remaining = self._check_usage_limit()
        if not within_limit:
            raise Exception(f"Daily Google API limit reached ({self.DAILY_SEARCH_LIMIT} searches)")
        
        logger.info(f"Searching images for: {query} (start: {start_index}, remaining quota: {remaining})")
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "searchType": "image",
            "num": min(num_results, 10),
            "start": start_index,
            "safe": "active"
        }
        
        try:
            response = requests.get(self.SEARCH_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            # Update usage
            self.usage_data["searches"] += 1
            self._save_usage()
            
            data = response.json()
            items = data.get("items", [])
            
            # Extract relevant metadata and score results
            results = []
            for item in items:
                url = item.get("link", "")
                domain_score = self._get_domain_score(url)
                
                result = {
                    "title": item.get("title", ""),
                    "link": url,
                    "displayLink": item.get("displayLink", ""),
                    "snippet": item.get("snippet", ""),
                    "mime": item.get("mime", ""),
                    "fileFormat": item.get("fileFormat", ""),
                    "image": item.get("image", {}),
                    "contextLink": item.get("image", {}).get("contextLink", ""),
                    "thumbnailLink": item.get("image", {}).get("thumbnailLink", ""),
                    "domain_score": domain_score
                }
                results.append(result)
            
            # Sort by domain score (higher is better)
            results.sort(key=lambda x: x['domain_score'], reverse=True)
            
            logger.info(f"Found {len(results)} images for query: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching images: {e}")
            raise
    
    def _check_usage_limit(self) -> Tuple[bool, int]:
        """Check if we're within daily usage limit."""
        remaining = self.DAILY_SEARCH_LIMIT - self.usage_data.get("searches", 0)
        return remaining > 0, remaining
    
    def validate_and_download_image(self, url: str, save_path: str, max_size_mb: int = 20) -> Dict[str, Any]:
        """
        Download and validate image with quality controls.
        
        Args:
            url: Image URL
            save_path: Where to save the image
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dictionary with download result and metadata
        """
        try:
            domain = urlparse(url).netloc
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://google.com/'
            }
            
            # First, try HEAD request to check size
            try:
                head_response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
                content_length = head_response.headers.get('content-length')
                
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        self._track_failed_domain(domain)
                        return {"success": False, "error": f"Image too large: {size_mb:.1f}MB"}
            except:
                # If HEAD fails, continue with GET
                pass
            
            # Download image with shorter timeout and retries
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=15, stream=True)
                    response.raise_for_status()
                    break
                except requests.Timeout:
                    if attempt == max_retries - 1:
                        self._track_failed_domain(domain)
                        return {"success": False, "error": "Download timeout"}
                    continue
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self._track_failed_domain(domain)
                return {"success": False, "error": f"Not an image: {content_type}"}
            
            # Load into memory for validation
            image_data = io.BytesIO()
            downloaded_size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size_mb * 1024 * 1024:
                        self._track_failed_domain(domain)
                        return {"success": False, "error": "Download exceeded size limit"}
                    image_data.write(chunk)
            
            image_data.seek(0)
            
            # Validate it's a real image
            try:
                img = Image.open(image_data)
                img.verify()  # Verify it's not corrupted
                
                # Re-open for getting info
                image_data.seek(0)
                img = Image.open(image_data)
                
                # Get image properties
                width, height = img.size
                aspect_ratio = width / height
                
                # Calculate hash for deduplication
                image_data.seek(0)
                image_hash = hashlib.md5(image_data.read()).hexdigest()
                
                # Check if duplicate
                with self.hashes_lock:
                    if image_hash in self.image_hashes:
                        return {"success": False, "error": "Duplicate image", "hash": image_hash}
                    self.image_hashes.add(image_hash)
                
                # Save the validated image
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                image_data.seek(0)
                with open(save_path, 'wb') as f:
                    f.write(image_data.read())
                
                # Generate thumbnail
                thumb_dir = os.path.join(os.path.dirname(save_path), "thumbnails")
                thumb_path = os.path.join(thumb_dir, os.path.basename(save_path))
                self.generate_thumbnail(save_path, thumb_path)
                
                return {
                    "success": True,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "format": img.format,
                    "mode": img.mode,
                    "hash": image_hash,
                    "size_bytes": downloaded_size,
                    "size_mb": downloaded_size / (1024 * 1024),
                    "domain": domain
                }
                
            except Exception as e:
                self._track_failed_domain(domain)
                return {"success": False, "error": f"Invalid image: {str(e)}"}
                
        except Exception as e:
            if 'domain' in locals():
                self._track_failed_domain(domain)
            return {"success": False, "error": str(e)}
    
    def generate_thumbnail(self, image_path: str, thumb_path: str, size: tuple = (320, 180)):
        """Generate thumbnail for quick preview."""
        try:
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA' or img.mode == 'LA':
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)
                
                return True
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return False
    
    def download_images_for_shot(self, shot_num: int, search_results: List[Dict], 
                                images_dir: str) -> Dict[str, Any]:
        """
        Download images for a single shot using threading.
        
        Args:
            shot_num: Shot number
            search_results: List of search results
            images_dir: Directory to save images
            
        Returns:
            Dictionary with download results
        """
        shot_result = {
            "shot_num": shot_num,
            "total_results": len(search_results),
            "download_attempts": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "images": []
        }
        
        # Use ThreadPoolExecutor for parallel downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            letter_index = 1  # Start at B (A reserved for AI)
            
            for result in search_results:
                if shot_result["successful_downloads"] >= self.IMAGES_PER_SHOT:
                    break
                
                url = result.get("link")
                if not url:
                    continue
                
                # Determine filename
                ext = self.get_file_extension(url, result.get("mime"))
                letter = chr(65 + letter_index)
                filename = f"{shot_num}{letter}{ext}"
                save_path = os.path.join(images_dir, filename)
                
                # Submit download task
                future = executor.submit(
                    self.validate_and_download_image,
                    url, save_path
                )
                futures.append((future, result, filename, letter_index))
                letter_index += 1
                shot_result["download_attempts"] += 1
            
            # Process results as they complete
            for future, result, filename, idx in futures:
                try:
                    download_result = future.result(timeout=60)
                    
                    if download_result["success"]:
                        shot_result["successful_downloads"] += 1
                        image_metadata = {
                            "filename": filename,
                            "url": result.get("link"),
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "source": result.get("displayLink", ""),
                            "context_url": result.get("contextLink", ""),
                            "width": download_result.get("width"),
                            "height": download_result.get("height"),
                            "aspect_ratio": download_result.get("aspect_ratio"),
                            "size_mb": download_result.get("size_mb"),
                            "format": download_result.get("format"),
                            "hash": download_result.get("hash"),
                            "domain_score": result.get("domain_score", 0)
                        }
                        shot_result["images"].append(image_metadata)
                    else:
                        shot_result["failed_downloads"] += 1
                        logger.debug(f"Failed to download {filename}: {download_result.get('error')}")
                        
                except concurrent.futures.TimeoutError:
                    shot_result["failed_downloads"] += 1
                    logger.error(f"Download timeout (60s) for {filename} from {result.get('link', 'unknown URL')}")
                except Exception as e:
                    shot_result["failed_downloads"] += 1
                    error_msg = str(e) if str(e) else repr(e)
                    logger.error(f"Download error for {filename}: {type(e).__name__}: {error_msg}")
        
        return shot_result
    
    def get_file_extension(self, url: str, mime_type: str = None) -> str:
        """Determine file extension from URL or MIME type."""
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
        Process all image searches from a storyboard with enhanced features.
        """
        # Load existing hashes for deduplication
        metadata_path = os.path.join(os.path.dirname(images_dir), 
                                   f"{actor_name}_image_metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    existing_data = json.load(f)
                    # Load existing hashes
                    for shot_data in existing_data.get("shot_metadata", {}).values():
                        for img in shot_data.get("images", []):
                            if img.get("hash"):
                                self.image_hashes.add(img["hash"])
            except:
                pass
        
        # Load storyboard
        with open(storyboard_path, 'r') as f:
            storyboard_data = json.load(f)
        
        storyboard = storyboard_data.get("storyboard", [])
        total_shots = len(storyboard)
        
        # Process results
        results = {
            "actor_name": actor_name,
            "total_shots": total_shots,
            "processed_shots": 0,
            "skipped_shots": 0,
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "search_errors": 0,
            "timestamp": datetime.now().isoformat(),
            "shot_metadata": {},
            "domain_statistics": {}
        }
        
        # Process each shot
        for shot in storyboard:
            shot_num = shot.get("shot")
            if not shot_num:
                continue
            
            # Check if we already have enough images for this shot
            if skip_existing:
                existing_count = 0
                shot_pattern = f"{shot_num}[B-Z]"
                if os.path.exists(images_dir):
                    import glob
                    existing_files = glob.glob(os.path.join(images_dir, f"{shot_num}[B-Z].*"))
                    existing_count = len(existing_files)
                
                if existing_count >= self.IMAGES_PER_SHOT:
                    logger.info(f"Skipping shot {shot_num} - already has {existing_count} images")
                    results["skipped_shots"] += 1
                    results["shot_metadata"][str(shot_num)] = {"status": "skipped", "existing_count": existing_count}
                    continue
            
            # Get search query
            search_query = shot.get("image_search", "")
            if not search_query:
                logger.warning(f"No search query for shot {shot_num}")
                continue
            
            logger.info(f"Processing shot {shot_num}/{total_shots}: {search_query}")
            
            try:
                # Check API limit
                within_limit, remaining = self._check_usage_limit()
                if not within_limit:
                    logger.warning(f"Daily limit reached. Stopping at shot {shot_num}")
                    results["limit_reached"] = True
                    break
                
                # Search for extended results
                search_results = self.search_images_extended(search_query)
                results["processed_shots"] += 1
                
                # Download images for this shot
                shot_result = self.download_images_for_shot(shot_num, search_results, images_dir)
                
                # Update totals
                results["total_downloads"] += shot_result["download_attempts"]
                results["successful_downloads"] += shot_result["successful_downloads"]
                results["failed_downloads"] += shot_result["failed_downloads"]
                
                # Store shot metadata
                results["shot_metadata"][str(shot_num)] = {
                    "search_query": search_query,
                    "search_results_count": len(search_results),
                    "download_attempts": shot_result["download_attempts"],
                    "successful_downloads": shot_result["successful_downloads"],
                    "images": shot_result["images"]
                }
                
                # Small delay between shots
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing shot {shot_num}: {e}")
                results["search_errors"] += 1
                results["shot_metadata"][str(shot_num)] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Calculate domain statistics
        with self.failed_domains_lock:
            results["domain_statistics"]["failed_domains"] = dict(self.failed_domains)
        
        # Save updated usage
        self._save_usage()
        
        return results