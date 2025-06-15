#!/usr/bin/env python3
"""
Folder management utilities for organizing actor projects.
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List
import re


class ActorFolderManager:
    """
    Manages folder structure for actor projects.
    """
    
    def __init__(self, base_output_dir: str = "output"):
        """
        Initialize the folder manager.
        
        Args:
            base_output_dir: Base directory for all output
        """
        self.base_output_dir = base_output_dir
        self.actors_dir = os.path.join(base_output_dir, "actors")
        self._ensure_base_directories()
    
    def _ensure_base_directories(self):
        """Ensure base directories exist."""
        Path(self.base_output_dir).mkdir(exist_ok=True)
        Path(self.actors_dir).mkdir(exist_ok=True)
    
    def normalize_actor_name(self, actor_name: str) -> str:
        """
        Normalize actor name for folder creation.
        Converts to lowercase and replaces spaces with underscores.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Normalized folder name
        """
        # Remove any special characters except spaces, hyphens, apostrophes
        cleaned = re.sub(r"[^\w\s\-']", "", actor_name)
        # Replace spaces with underscores and convert to lowercase
        normalized = cleaned.lower().replace(" ", "_").replace("'", "")
        return normalized
    
    def find_existing_actor_folder(self, actor_name: str) -> Optional[str]:
        """
        Find existing actor folder (case-insensitive).
        
        Args:
            actor_name: The actor's name to search for
            
        Returns:
            Path to existing folder or None
        """
        normalized_name = self.normalize_actor_name(actor_name)
        
        # Check for exact match first
        exact_path = os.path.join(self.actors_dir, normalized_name)
        if os.path.exists(exact_path):
            return exact_path
        
        # Check for case-insensitive match
        try:
            existing_folders = os.listdir(self.actors_dir)
            for folder in existing_folders:
                if folder.lower() == normalized_name.lower():
                    return os.path.join(self.actors_dir, folder)
        except OSError:
            pass
        
        return None
    
    def get_or_create_actor_folder(self, actor_name: str) -> str:
        """
        Get existing actor folder or create new one.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Path to actor folder
        """
        # Check if folder already exists
        existing_folder = self.find_existing_actor_folder(actor_name)
        if existing_folder:
            return existing_folder
        
        # Create new folder
        normalized_name = self.normalize_actor_name(actor_name)
        actor_folder = os.path.join(self.actors_dir, normalized_name)
        Path(actor_folder).mkdir(exist_ok=True)
        return actor_folder
    
    def find_existing_scripts(self, actor_folder: str) -> List[str]:
        """
        Find existing script files in actor folder.
        
        Args:
            actor_folder: Path to actor folder
            
        Returns:
            List of script file paths
        """
        scripts = []
        if os.path.exists(actor_folder):
            for file in os.listdir(actor_folder):
                if file.endswith("_script.txt") and "PHONETIC" not in file:
                    scripts.append(os.path.join(actor_folder, file))
        
        # Sort by modification time (newest first)
        scripts.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return scripts
    
    def get_latest_script(self, actor_name: str) -> Optional[str]:
        """
        Get the latest script for an actor.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Path to latest script or None
        """
        actor_folder = self.find_existing_actor_folder(actor_name)
        if not actor_folder:
            return None
        
        scripts = self.find_existing_scripts(actor_folder)
        return scripts[0] if scripts else None
    
    def get_script_paths(self, actor_name: str) -> dict:
        """
        Get standardized paths for script files.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Dictionary with paths for different file types
        """
        actor_folder = self.get_or_create_actor_folder(actor_name)
        normalized_name = self.normalize_actor_name(actor_name)
        
        return {
            "folder": actor_folder,
            "script": os.path.join(actor_folder, f"{normalized_name}_script.txt"),
            "phonetic": os.path.join(actor_folder, f"{normalized_name}_PHONETIC_script.txt"),
            "json": os.path.join(actor_folder, f"{normalized_name}_script_data.json"),
            "storyboard": os.path.join(actor_folder, f"{normalized_name}_storyboard.json"),
            "music_plan": os.path.join(actor_folder, f"{normalized_name}_music_plan.json"),
            "cost_tracking": os.path.join(actor_folder, f"{normalized_name}_cost_tracking.json")
        }
    
    def get_latest_storyboard(self, actor_name: str) -> Optional[str]:
        """
        Get the latest storyboard for an actor.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Path to storyboard file or None
        """
        paths = self.get_script_paths(actor_name)
        storyboard_path = paths['storyboard']
        
        if os.path.exists(storyboard_path):
            return storyboard_path
        
        return None
    
    def get_latest_music_plan(self, actor_name: str) -> Optional[str]:
        """
        Get the latest music plan for an actor.
        
        Args:
            actor_name: The actor's name
            
        Returns:
            Path to music plan file or None
        """
        paths = self.get_script_paths(actor_name)
        music_plan_path = paths['music_plan']
        
        if os.path.exists(music_plan_path):
            return music_plan_path
        
        return None