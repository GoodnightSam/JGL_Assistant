#!/usr/bin/env python3
"""
Recommended improvements for image_searcher.py
These are code snippets showing how to fix the identified issues.
"""

import hashlib
import io
from PIL import Image
import requests

class ImageSearcherV2Improvements:
    """
    Code snippets showing recommended improvements.
    """
    
    def validate_and_download_image(self, url: str, save_path: str, 
                                   min_width: int = 640, min_height: int = 360,
                                   max_size_mb: int = 10) -> dict:
        """
        Download and validate image with quality controls.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; JGLAssistant/1.0; +https://github.com/yourusername/JGL_Assistant)',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://google.com/'
            }
            
            # First, get headers to check size
            head_response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            content_length = head_response.headers.get('content-length')
            
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    return {"success": False, "error": f"Image too large: {size_mb:.1f}MB"}
            
            # Download image
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Load into memory first for validation
            image_data = io.BytesIO()
            downloaded_size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size_mb * 1024 * 1024:
                        return {"success": False, "error": "Download exceeded size limit"}
                    image_data.write(chunk)
            
            image_data.seek(0)
            
            # Validate it's a real image
            try:
                img = Image.open(image_data)
                img.verify()  # Verify it's not corrupted
                
                # Re-open for getting info (verify() closes the file)
                image_data.seek(0)
                img = Image.open(image_data)
                
                # Check dimensions
                width, height = img.size
                if width < min_width or height < min_height:
                    return {
                        "success": False, 
                        "error": f"Image too small: {width}x{height}",
                        "width": width,
                        "height": height
                    }
                
                # Calculate hash for deduplication
                image_data.seek(0)
                image_hash = hashlib.md5(image_data.read()).hexdigest()
                
                # Get aspect ratio
                aspect_ratio = width / height
                
                # Save the validated image
                image_data.seek(0)
                with open(save_path, 'wb') as f:
                    f.write(image_data.read())
                
                return {
                    "success": True,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "format": img.format,
                    "mode": img.mode,
                    "hash": image_hash,
                    "size_bytes": downloaded_size
                }
                
            except Exception as e:
                return {"success": False, "error": f"Invalid image format: {str(e)}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enhance_search_query(self, base_query: str, actor_name: str, shot_info: dict) -> str:
        """
        Enhance search query for better results.
        """
        # Add quality modifiers
        quality_terms = ["high resolution", "HD", "professional"]
        
        # Add actor context if not already present
        if actor_name.lower() not in base_query.lower():
            enhanced = f"{base_query} {actor_name}"
        else:
            enhanced = base_query
        
        # Add era/time period if detected in shot
        script_text = shot_info.get("script", "")
        import re
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', script_text)
        if years:
            enhanced += f" {years[0]}s era"
        
        # Add aspect ratio preference
        enhanced += " 16:9 widescreen"
        
        # Remove problematic terms
        remove_terms = ["portrait", "headshot", "face", "close-up"]
        for term in remove_terms:
            enhanced = enhanced.replace(term, "")
        
        return enhanced.strip()
    
    def deduplicate_images(self, existing_hashes: set, new_images: list) -> list:
        """
        Remove duplicate images based on content hash.
        """
        unique_images = []
        
        for img in new_images:
            if img.get("hash") and img["hash"] not in existing_hashes:
                unique_images.append(img)
                existing_hashes.add(img["hash"])
        
        return unique_images
    
    def parse_image_filename(self, filename: str) -> tuple:
        """
        Robust parsing of image filenames like '12B.jpg'.
        """
        import re
        
        # Match pattern: number + letter + extension
        match = re.match(r'^(\d+)([A-Z])\.(\w+)$', filename, re.IGNORECASE)
        if match:
            shot_num = int(match.group(1))
            letter = match.group(2).upper()
            extension = match.group(3).lower()
            return shot_num, letter, extension
        
        return None, None, None
    
    def generate_thumbnail(self, image_path: str, thumb_path: str, size: tuple = (320, 180)):
        """
        Generate thumbnail for quick preview.
        """
        try:
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
    
    def prioritize_search_results(self, results: list, preferences: dict) -> list:
        """
        Reorder search results based on quality signals.
        """
        scored_results = []
        
        for result in results:
            score = 0
            
            # Prefer certain domains
            good_domains = ['getty', 'shutterstock', 'pexels', 'unsplash', 'wikimedia']
            if any(domain in result.get('displayLink', '').lower() for domain in good_domains):
                score += 10
            
            # Prefer images with good metadata
            if result.get('image', {}).get('height', 0) >= 720:
                score += 5
            if result.get('image', {}).get('width', 0) >= 1280:
                score += 5
            
            # Deprioritize potentially problematic images
            bad_signals = ['thumbnail', 'avatar', 'profile', 'headshot', 'portrait']
            if any(signal in result.get('title', '').lower() for signal in bad_signals):
                score -= 10
            
            scored_results.append((score, result))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for score, result in scored_results]
    
    def batch_process_searches(self, queries: list, max_batch: int = 10) -> dict:
        """
        Process multiple searches more efficiently.
        """
        # Group similar queries that might have overlapping results
        grouped = {}
        for query in queries:
            # Simple grouping by first significant word
            key_word = query.split()[0] if query.split() else "misc"
            if key_word not in grouped:
                grouped[key_word] = []
            grouped[key_word].append(query)
        
        # Process in batches with shared result caching
        results_cache = {}
        
        for group, group_queries in grouped.items():
            # Could potentially do one broader search and filter results
            pass
        
        return results_cache