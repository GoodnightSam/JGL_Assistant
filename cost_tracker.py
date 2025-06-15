#!/usr/bin/env python3
"""
Cost tracking utilities for JGL Assistant.
Tracks API costs across all operations for each actor project.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks and persists API costs for actor projects.
    """
    
    def __init__(self, cost_file_path: str):
        """
        Initialize the cost tracker.
        
        Args:
            cost_file_path: Path to the cost tracking JSON file
        """
        self.cost_file_path = cost_file_path
        self.cost_data = self._load_existing_data()
    
    def _load_existing_data(self) -> Dict[str, Any]:
        """Load existing cost data if file exists."""
        if os.path.exists(self.cost_file_path):
            try:
                with open(self.cost_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing cost data: {e}")
        
        # Initialize with empty structure
        return {
            "actor_name": "",
            "total_cost": 0.0,
            "entries": []
        }
    
    def add_entry(self, 
                  step: str, 
                  model: str, 
                  cost: float,
                  usage_data: Optional[Dict[str, Any]] = None,
                  additional_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new cost entry.
        
        Args:
            step: The step/operation performed (e.g., "script_generation", "phonetic_conversion")
            model: The model used (e.g., "o3-2025-04-16", "o4-mini")
            cost: The cost in USD
            usage_data: Optional token usage data
            additional_info: Any additional information to track
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "model": model,
            "cost": cost,
            "usage": usage_data or {},
            "additional_info": additional_info or {}
        }
        
        self.cost_data["entries"].append(entry)
        self.cost_data["total_cost"] += cost
        
        # Save immediately
        self._save_data()
        
        logger.info(f"Tracked cost: {step} - ${cost:.4f} ({model})")
    
    def set_actor_name(self, actor_name: str) -> None:
        """Set the actor name for this tracking file."""
        self.cost_data["actor_name"] = actor_name
        self._save_data()
    
    def _save_data(self) -> None:
        """Save cost data to file."""
        try:
            with open(self.cost_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cost_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost tracking data: {e}")
    
    def get_step_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of costs by step.
        
        Returns:
            Dictionary with step names as keys and summary data as values
        """
        summary = {}
        
        for entry in self.cost_data["entries"]:
            step = entry["step"]
            if step not in summary:
                summary[step] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "models_used": set()
                }
            
            summary[step]["count"] += 1
            summary[step]["total_cost"] += entry["cost"]
            summary[step]["models_used"].add(entry["model"])
        
        # Convert sets to lists for JSON serialization
        for step_data in summary.values():
            step_data["models_used"] = list(step_data["models_used"])
        
        return summary
    
    def get_total_cost(self) -> float:
        """Get total cost for this actor."""
        return self.cost_data["total_cost"]
    
    def get_latest_entries(self, n: int = 5) -> list:
        """Get the n most recent cost entries."""
        return self.cost_data["entries"][-n:] if self.cost_data["entries"] else []


def format_cost_summary(cost_tracker: CostTracker) -> str:
    """
    Format a human-readable cost summary.
    
    Args:
        cost_tracker: The CostTracker instance
        
    Returns:
        Formatted string summary
    """
    total = cost_tracker.get_total_cost()
    summary = cost_tracker.get_step_summary()
    
    lines = [
        f"Total Cost: ${total:.4f}",
        f"Operations: {len(cost_tracker.cost_data['entries'])}",
        ""
    ]
    
    if summary:
        lines.append("Cost by Step:")
        for step, data in summary.items():
            lines.append(f"  - {step}: ${data['total_cost']:.4f} ({data['count']} times)")
    
    return "\n".join(lines)