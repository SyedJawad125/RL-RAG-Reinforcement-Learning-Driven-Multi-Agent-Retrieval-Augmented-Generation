"""
Planner Agent - Query Analysis and Task Decomposition
Analyzes queries and creates execution plans
"""
from typing import Dict, Any, List
import json
import logging
from .base_agent import BaseAgent, AgentState, AgentResult

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner Agent analyzes queries and breaks them into sub-tasks.
    
    Responsibilities:
    - Classify query type (question, search, analysis, summarization)
    - Determine required agents and tools
    - Create execution plan
    - Assess query complexity
    """
    
    def __init__(self, llm_service=None):
        super().__init__(
            name="Planner",
            description="Analyzes queries and creates execution plans",
            llm_service=llm_service
        )
    
    async def execute(self, state: AgentState) -> AgentResult:
        """
        Analyze query and create execution plan.
        
        Args:
            state: Current agent state with query
            
        Returns:
            AgentResult with execution plan
        """
        query = state.query
        
        try:
            self.add_thought(state, f"Analyzing query: '{query}'")
            
            # Step 1: Classify query type
            query_classification = await self._classify_query(query, state)
            
            # Step 2: Determine complexity
            complexity = await self._assess_complexity(query, state)
            
            # Step 3: Create execution plan
            execution_plan = await self._create_plan(
                query,
                query_classification,
                complexity,
                state
            )
            
            self.add_observation(
                state,
                f"Created plan with {len(execution_plan['agents'])} agents"
            )
            
            # Prepare result
            result_data = {
                "query_type": query_classification["type"],
                "complexity": complexity,
                "execution_plan": execution_plan,
                "estimated_time": self._estimate_execution_time(execution_plan),
                "requires_internet": execution_plan.get("requires_internet", False)
            }
            
            return self.create_result(
                success=True,
                output=json.dumps(result_data, indent=2),
                state=state,
                confidence=0.9
            )
            
        except Exception as e:
            self.add_error(state, f"Planning failed: {str(e)}")
            return self.create_result(
                success=False,
                output="",
                state=state,
                error=str(e)
            )
    
    async def _classify_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """
        Classify query type.
        
        Returns:
            Dictionary with query classification
        """
        self.add_action(state, "Classifying query type", "llm_classifier")
        
        prompt = f"""Analyze this query and classify it into ONE of these types:

TYPES:
- factual_question: Simple factual questions (What is X? Who is Y?)
- analytical_question: Questions requiring analysis (Why? How? Compare X and Y?)
- search_query: Broad search requiring internet lookup
- document_query: Questions about specific uploaded documents
- summarization: Requests to summarize content
- creative: Creative writing or generation

Query: "{query}"

Return ONLY a JSON object with this structure:
{{
    "type": "query_type_here",
    "confidence": 0.9,
    "reasoning": "brief explanation",
    "keywords": ["key", "words"],
    "intent": "what user wants to achieve"
}}

JSON:"""
        
        try:
            response = await self.call_llm(prompt, temperature=0.1, max_tokens=300)
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            
            classification = json.loads(response)
            
            self.add_observation(
                state,
                f"Classified as: {classification['type']} (confidence: {classification['confidence']})"
            )
            
            return classification
            
        except Exception as e:
            logger.warning(f"[Planner] Classification failed: {e}, using default")
            return {
                "type": "factual_question",
                "confidence": 0.5,
                "reasoning": "Classification failed, using default",
                "keywords": query.split()[:5],
                "intent": "unknown"
            }
    
    async def _assess_complexity(self, query: str, state: AgentState) -> str:
        """
        Assess query complexity.
        
        Returns:
            Complexity level: 'simple', 'medium', 'complex'
        """
        self.add_action(state, "Assessing query complexity", "complexity_analyzer")
        
        # Simple heuristics for complexity
        word_count = len(query.split())
        has_comparison = any(word in query.lower() for word in ['compare', 'difference', 'versus', 'vs'])
        has_multi_part = any(word in query.lower() for word in ['and', 'also', 'additionally', 'furthermore'])
        has_time_aspect = any(word in query.lower() for word in ['trend', 'history', 'evolution', 'changes'])
        
        complexity_score = 0
        
        if word_count > 20:
            complexity_score += 2
        elif word_count > 10:
            complexity_score += 1
        
        if has_comparison:
            complexity_score += 2
        if has_multi_part:
            complexity_score += 1
        if has_time_aspect:
            complexity_score += 1
        
        if complexity_score >= 4:
            complexity = "complex"
        elif complexity_score >= 2:
            complexity = "medium"
        else:
            complexity = "simple"
        
        self.add_observation(state, f"Complexity assessed as: {complexity}")
        
        return complexity
    
    async def _create_plan(
        self,
        query: str,
        classification: Dict[str, Any],
        complexity: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Create execution plan based on query analysis.
        
        Returns:
            Execution plan with agents and tools
        """
        self.add_action(state, "Creating execution plan", "plan_generator")
        
        query_type = classification["type"]
        
        plan = {
            "agents": [],
            "tools": [],
            "strategy": "simple",
            "requires_internet": False,
            "parallel_execution": False
        }
        
        # Determine which agents are needed
        if query_type == "document_query":
            # Use RAG agent for document queries
            plan["agents"] = ["RAGAgent"]
            plan["tools"] = ["vector_search"]
            plan["strategy"] = "simple_rag"
            
        elif query_type == "factual_question":
            # Check if we need internet search
            if "current" in query.lower() or "latest" in query.lower() or "recent" in query.lower():
                plan["agents"] = ["SearchAgent", "AnswerAgent"]
                plan["tools"] = ["web_search"]
                plan["requires_internet"] = True
                plan["strategy"] = "internet_first"
            else:
                # Try RAG first, then internet
                plan["agents"] = ["RAGAgent", "SearchAgent", "AnswerAgent"]
                plan["tools"] = ["vector_search", "web_search"]
                plan["strategy"] = "rag_with_fallback"
                
        elif query_type == "search_query":
            # Broad search - use internet
            plan["agents"] = ["SearchAgent", "AnswerAgent"]
            plan["tools"] = ["web_search"]
            plan["requires_internet"] = True
            plan["strategy"] = "internet_search"
            
        elif query_type == "analytical_question":
            # Complex analysis - use all agents
            plan["agents"] = ["RAGAgent", "SearchAgent", "AnswerAgent"]
            plan["tools"] = ["vector_search", "web_search", "knowledge_graph"]
            plan["strategy"] = "comprehensive"
            plan["parallel_execution"] = True
            
        elif query_type == "summarization":
            # Summarization
            plan["agents"] = ["RAGAgent", "AnswerAgent"]
            plan["tools"] = ["vector_search"]
            plan["strategy"] = "summarization"
            
        else:
            # Default: RAG + Answer
            plan["agents"] = ["RAGAgent", "AnswerAgent"]
            plan["tools"] = ["vector_search"]
            plan["strategy"] = "simple"
        
        # Adjust based on complexity
        if complexity == "complex" and "AnswerAgent" in plan["agents"]:
            # For complex queries, add research step
            if "SearchAgent" not in plan["agents"]:
                plan["agents"].insert(-1, "SearchAgent")
                plan["tools"].append("web_search")
        
        self.add_observation(
            state,
            f"Plan created: {len(plan['agents'])} agents, strategy: {plan['strategy']}"
        )
        
        return plan
    
    def _estimate_execution_time(self, plan: Dict[str, Any]) -> float:
        """
        Estimate execution time based on plan.
        
        Returns:
            Estimated time in seconds
        """
        base_time = 1.0
        
        # Add time per agent
        agent_times = {
            "RAGAgent": 1.5,
            "SearchAgent": 3.0,
            "AnswerAgent": 2.0,
        }
        
        total_time = base_time
        for agent in plan["agents"]:
            total_time += agent_times.get(agent, 1.0)
        
        # Adjust for parallel execution
        if plan.get("parallel_execution"):
            total_time *= 0.7  # 30% speedup
        
        return round(total_time, 1)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                "Query classification",
                "Complexity assessment",
                "Execution planning",
                "Agent coordination",
                "Time estimation"
            ],
            "output_format": "execution_plan_json"
        }