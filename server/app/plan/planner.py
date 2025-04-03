from typing import List, Dict, Any
from app.llm.base_llm import BaseLLM
from app.utils.logger import get_logger
import json
import re
from pydantic import BaseModel

logger = get_logger()

class Action(BaseModel):
    """Action model for agent execution"""
    agent_name: str
    action_type: str
    parameters: Dict[str, Any]
    explanation: str = ""

    class Config:
        arbitrary_types_allowed = True

class Planner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def _get_planning_prompt(self, intention: Dict[str, Any], agents: List[Dict[str, Any]], message: str) -> str:
        """Generate the planning prompt for the LLM"""
        agents_description = "\n".join([
            f"Agent {agent['name']}: {agent['description']}\n"
            f"Available tools: {', '.join(tool['name'] for tool in agent['tools'])}"
            for agent in agents
        ])

        return f"""As an advanced planning system, analyze the user's message to determine the appropriate response strategy.
Given the following:

User Message: {message}

Recognized Intention:
{intention}

Available Agents and their Tools:
{agents_description}

First, determine if this is a simple daily life question that can be answered directly by the Copilot agent, or if it requires a more complex action plan.

For simple daily life questions (e.g., greetings, weather, basic facts, simple preferences):
- Use only the Copilot agent with its response tool
- Keep the action plan minimal with just one action

For complex tasks that require decision making or deeper analysis (e.g., strategy decisions, technical choices, business analysis, research questions, comparisons), you MUST break down the task into specific actions considering:
1. What information needs to be gathered from different sources
2. What analysis needs to be performed on the gathered information
3. What comparisons or evaluations need to be made
4. What recommendations need to be synthesized
5. How to present the final comprehensive response

Examples of complex tasks that require detailed breakdown:
- Business or technical strategy decisions
- Technology selection or comparison
- Market analysis or competitive research
- Architecture or design choices
- Cost-benefit analysis
- Risk assessment
- Performance optimization recommendations

Return the plan as a JSON array of actions. Each action should have:
- agent_name: The name of the agent to perform the action
- action_type: The type of action to perform, ATTENTION: please make sure action_type must be one of the agent's tools
- parameters: Any parameters needed for the action
- explanation: A brief explanation about why you choose this action

Example for a simple daily life question:
[{{"agent_name": "Copilot", "action_type": "respond", "parameters": {{"query": "What's the weather like today?"}}, "explanation": "This is a simple daily life question that can be answered directly."}}]

Example for a complex decision-making task:
[
    {{"agent_name": "Researcher", "action_type": "search", "parameters": {{"query": "current market analysis of technology X"}}, "explanation": "Gather market data and current trends"}},
    {{"agent_name": "Analyst", "action_type": "analyze", "parameters": {{"data": "market research results"}}, "explanation": "Analyze market positioning and competitive advantages"}},
    {{"agent_name": "Researcher", "action_type": "search", "parameters": {{"query": "implementation challenges and success cases"}}, "explanation": "Gather practical implementation insights"}},
    {{"agent_name": "Analyst", "action_type": "analyze", "parameters": {{"data": "implementation insights"}}, "explanation": "Analyze feasibility and potential risks"}},
    {{"agent_name": "Copilot", "action_type": "Answer", "parameters": {{"query": "comprehensive analysis"}}, "explanation": "Provide final recommendation based on all gathered and analyzed information"}}
]

Example is only for data structure demonstration, you should follow it's structure, but don't follow the example content, you MUST USE actual agents and tools data showing in the Available Agents and their Tools section.

Do not return any other text than the JSON array of actions.

Remember: 
1. Only use Copilot alone for simple daily life questions
2. For ANY questions involving decision-making, strategy, or complex analysis, create a detailed multi-agent plan
3. When in doubt about complexity, prefer breaking down into multiple steps rather than a single response."""

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON array from text that might contain markdown code blocks or other decorators"""
        # Remove markdown code blocks if present
        text = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
        
        # Find the first '[' and last ']' to extract the JSON array
        start = text.find('[')
        end = text.rfind(']')
        
        if start != -1 and end != -1:
            return text[start:end + 1]
        return text

    async def create_plan(self, intention: Dict[str, Any], agents: List[Dict[str, Any]], message: str) -> List[Action]:
        """Create an action plan based on the intention and available agents"""
        # Generate the planning prompt
        prompt = self._get_planning_prompt(intention, agents, message)
        
        # Get plan from LLM
        response = await self.llm.aChat([
            {"role": "system", "content": prompt}
        ])

        try:
            # Get content and clean it up
            content = response.get("content", "")
            json_str = self._extract_json_from_text(content)
            
            # Parse the JSON string
            try:
                plan_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {str(e)}\nContent: {json_str}")
                return []
            
            # Create actions from the plan data
            actions = []
            for action_data in plan_data:
                try:
                    action = Action(
                        agent_name=action_data["agent_name"],
                        action_type=action_data["action_type"],
                        parameters=action_data.get("parameters", {}),
                        explanation=action_data.get("explanation", "")
                    )
                    actions.append(action)
                except Exception as e:
                    logger.error(f"Error creating action from data {action_data}: {str(e)}")
                    continue
            
            return actions
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return [] 