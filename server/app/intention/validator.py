"""
Intention Validation Module

This module provides functionality to validate and normalize intention objects.
"""

from typing import Dict, Any, List, Optional
from app.intention.constants import IntentionTypes
from app.utils.logger import get_logger

logger = get_logger()

class IntentionValidator:
    """
    Validates and normalizes intention objects.
    """
    
    @staticmethod
    def validate(intention: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize an intention object.
        
        Args:
            intention: The intention object to validate
            
        Returns:
            A validated and normalized intention object
        """
        # Create a copy of the intention to avoid modifying the original
        validated = intention.copy()
        
        # Ensure required fields exist
        if "intent" not in validated or not validated["intent"]:
            validated["intent"] = IntentionTypes.UNKNOWN
        
        if "sub_intent" not in validated:
            validated["sub_intent"] = ""
        
        if "parameters" not in validated or not isinstance(validated["parameters"], dict):
            validated["parameters"] = {}
        
        if "confidence" not in validated or not isinstance(validated["confidence"], (int, float)):
            validated["confidence"] = 0.0
        else:
            # Ensure confidence is between 0 and 1
            validated["confidence"] = max(0.0, min(1.0, float(validated["confidence"])))
        
        return validated
    
    @staticmethod
    def merge_intentions(intentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple intention hypotheses into a single intention.
        
        Args:
            intentions: A list of intention objects to merge
            
        Returns:
            A merged intention object
        """
        if not intentions:
            return {
                "intent": IntentionTypes.UNKNOWN,
                "sub_intent": "",
                "parameters": {},
                "confidence": 0.0
            }
        
        if len(intentions) == 1:
            return IntentionValidator.validate(intentions[0])
        
        # Sort intentions by confidence (descending)
        sorted_intentions = sorted(intentions, key=lambda x: x.get("confidence", 0.0), reverse=True)
        
        # Take the highest confidence intention as the base
        primary = sorted_intentions[0]
        validated = IntentionValidator.validate(primary)
        
        # Merge parameters from other intentions
        for intention in sorted_intentions[1:]:
            if "parameters" in intention and isinstance(intention["parameters"], dict):
                for key, value in intention["parameters"].items():
                    if key not in validated["parameters"]:
                        validated["parameters"][key] = value
        
        return validated 