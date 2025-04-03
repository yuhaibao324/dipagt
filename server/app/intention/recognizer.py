"""
Intention Recognition Module

This module provides functionality to identify user intentions based on 
their input, historical interactions, and personal profile data.
"""

from typing import Dict, Any, List, Optional
import json
from app.llm.base_llm import BaseLLM
from app.utils.logger import get_logger
from app.intention.constants import IntentionTypes, QueryIntentions, ActionIntentions

logger = get_logger()

class IntentionRecognizer:
    """
    Recognizes user intentions based on input text, conversation history and personal data.
    
    This class uses an LLM to identify the user's intention from their input.
    """
    
    def __init__(self, llm: BaseLLM, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the intention recognizer with the given LLM and configuration.
        
        Args:
            llm: The LLM instance to use for intention recognition
            config: Optional configuration for the intention recognizer
        """
        self.llm = llm
        self.config = config or {}
        
        # Extract configuration
        self.intention_schema = self.config.get("intention_schema", {
            "intent": "string",  # The primary intent
            "sub_intent": "string",  # Optional sub-intention
            "parameters": "object",  # Parameters extracted from the user query
            "confidence": "number"  # Confidence score (0-1)
        })
        
        self.system_prompt = self.config.get("system_prompt", self._get_default_system_prompt())
        logger.info("IntentionRecognizer initialized")
    
    def _get_default_system_prompt(self) -> str:
        """
        Get the default system prompt for intention recognition.
        
        Returns:
            The default system prompt as a string
        """
        return f"""
        You are an advanced intention recognition system. Your task is to analyze user input and determine their intention.
        
        Given:
        1. User's current input
        2. Conversation history (if available)
        3. User's personal data (if available)
        
        Analyze the information and extract the primary intention, any sub-intentions, and relevant parameters.
        
        Primary intentions must be one of the following:
        - {IntentionTypes.QUERY}: User wants information
        - {IntentionTypes.ACTION}: User wants to perform an action
        - {IntentionTypes.FEEDBACK}: User is providing feedback
        - {IntentionTypes.CLARIFICATION}: User is asking for clarification
        - {IntentionTypes.GREETING}: User is greeting the system
        - {IntentionTypes.UNKNOWN}: Intention couldn't be determined
        
        For query intentions, sub-intentions can be:
        - {QueryIntentions.INFORMATION}: General information search
        - {QueryIntentions.EXPLANATION}: User wants an explanation
        - {QueryIntentions.COMPARISON}: User wants a comparison
        - {QueryIntentions.STATUS}: User wants status information
        
        For action intentions, sub-intentions can be:
        - {ActionIntentions.CREATE}: Create something
        - {ActionIntentions.UPDATE}: Update something
        - {ActionIntentions.DELETE}: Delete something
        - {ActionIntentions.EXECUTE}: Execute a task or function
        - {ActionIntentions.SCHEDULE}: Schedule something
        
        Return your analysis in a JSON format with the following structure:
        {{
            "intent": "string",  # Must be one of the primary intentions listed above
            "sub_intent": "string",  # Must be one of the sub-intentions listed above, or empty string
            "parameters": {{}},  # Extracted parameters relevant to the intention
            "confidence": 0.0  # Confidence score between 0 and 1
        }}
        
        Be precise and accurate in your identification. If the intention is unclear, use {IntentionTypes.UNKNOWN} with an appropriate confidence score.
        """
    
    async def recognize(self, 
                         user_input: str, 
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recognize the user's intention from their input, conversation history and personal data.
        
        Args:
            user_input: The user's current input text
            conversation_history: Optional list of previous messages in the conversation
            user_data: Optional dictionary of user profile and preference data
            
        Returns:
            A dictionary containing the recognized intention
        """
        # Build the context for intention recognition
        messages = self._build_messages(user_input, conversation_history, user_data)
        
        # Send request to the LLM
        try:
            response = await self.llm.aChat(messages)
            
            # Parse and validate the response
            intention = self._parse_intention(response.get("content", ""))
            logger.info(f"Recognized intention: {intention.get('intent')} with confidence: {intention.get('confidence')}")
            
            return intention
        except Exception as e:
            logger.error(f"Error recognizing intention: {str(e)}")
            return {
                "intent": "error",
                "sub_intent": "processing_error",
                "parameters": {"error_message": str(e)},
                "confidence": 0.0
            }
    
    def _build_messages(self, 
                        user_input: str, 
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        user_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """
        Build the messages to send to the LLM for intention recognition.
        
        Args:
            user_input: The user's current input text
            conversation_history: Optional list of previous messages in the conversation
            user_data: Optional dictionary of user profile and preference data
            
        Returns:
            A list of message dictionaries to send to the LLM
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history if available
        if conversation_history:
            # Only include the most recent N messages to avoid exceeding context limits
            max_history = self.config.get("max_history", 5)
            recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history
            
            messages.extend(recent_history)
        
        # Add user data if available
        if user_data:
            user_data_str = f"User profile information:\n{json.dumps(user_data, ensure_ascii=False, indent=2)}"
            messages.append({"role": "system", "content": user_data_str})
        
        # Add the current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _parse_intention(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the intention from the LLM response text.
        
        Args:
            response_text: The text response from the LLM
            
        Returns:
            A dictionary containing the parsed intention
        """
        # Default intention structure in case of parsing errors
        default_intention = {
            "intent": IntentionTypes.UNKNOWN,
            "sub_intent": "",
            "parameters": {},
            "confidence": 0.0
        }
        
        try:
            # Try to extract JSON from the response
            # First, try to parse the entire response as JSON
            try:
                intention = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON using string manipulation
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    intention = json.loads(json_str)
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Validate and normalize the intention
            if "intent" not in intention or intention["intent"] not in vars(IntentionTypes).values():
                intention["intent"] = IntentionTypes.UNKNOWN
            
            if "confidence" not in intention:
                intention["confidence"] = 0.5
            else:
                # Ensure confidence is between 0 and 1
                intention["confidence"] = max(0.0, min(1.0, float(intention["confidence"])))
            
            if "sub_intent" not in intention:
                intention["sub_intent"] = ""
            else:
                # Validate sub-intent based on main intent
                valid_sub_intents = []
                if intention["intent"] == IntentionTypes.QUERY:
                    valid_sub_intents = vars(QueryIntentions).values()
                elif intention["intent"] == IntentionTypes.ACTION:
                    valid_sub_intents = vars(ActionIntentions).values()
                
                if intention["sub_intent"] not in valid_sub_intents:
                    intention["sub_intent"] = ""
                
            if "parameters" not in intention or not isinstance(intention["parameters"], dict):
                intention["parameters"] = {}
                
            return intention
            
        except Exception as e:
            logger.error(f"Error parsing intention from response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            return default_intention 