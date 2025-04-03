"""
Intention Recognition Constants

This module provides standard intention types and constants used in the intention recognition system.
"""

# Main intention categories
class IntentionTypes:
    # General intention types
    QUERY = "query"  # User wants information
    ACTION = "action"  # User wants to perform an action
    FEEDBACK = "feedback"  # User is providing feedback
    CLARIFICATION = "clarification"  # User is asking for clarification
    GREETING = "greeting"  # User is greeting the system
    UNKNOWN = "unknown"  # Intention couldn't be determined

# Sub-intention types
class QueryIntentions:
    INFORMATION = "information"  # General information search
    EXPLANATION = "explanation"  # User wants an explanation
    COMPARISON = "comparison"  # User wants a comparison
    STATUS = "status"  # User wants status information
    
class ActionIntentions:
    CREATE = "create"  # Create something
    UPDATE = "update"  # Update something
    DELETE = "delete"  # Delete something
    EXECUTE = "execute"  # Execute a task or function
    SCHEDULE = "schedule"  # Schedule something

# Confidence thresholds
class ConfidenceThresholds:
    HIGH = 0.8  # High confidence level
    MEDIUM = 0.5  # Medium confidence level
    LOW = 0.3  # Low confidence level 