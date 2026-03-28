# """
# Multi-Agent Coordinator using LangGraph
# Orchestrates Planner, Search, RAG, and Answer agents
# """
# from typing import Dict, Any, Optional, List
# import logging
# from django.conf import settings
# from .base_agent import AgentState, AgentResult
# from .planner_agent import PlannerAgent
# from .search_agent import SearchAgent
# from .rag_agent import RAGAgent
# from .answer_agent import AnswerAgent
# import json

# # LangGraph imports
# try:
#     from langgraph.graph import StateGraph, END
#     from langchain_core.messages import HumanMessage, SystemMessage
#     LANGGRAPH_AVAILABLE = True
# except ImportError:
#     LANGGRAPH_AVAILABLE = False
#     logger.warning("[Coordinator] LangGraph not available, using fallback coordination")

# logger = logging.getLogger(__name__)


# class MultiAgentCoordinator:
#     """
#     Coordinates multiple specialized agents using LangGraph.
    
#     Workflow:
#     1. Planner analyzes query and creates execution plan
#     2. Execute agents based on plan (RAG, Search, or both)
#     3. Answer agent synthesizes final response
#     """
    
#     def __init__(
#         self,
#         llm_service=None,
#         vector_store=None,
#         embedding_service=None,
#         tavily_client=None
#     ):
#         """
#         Initialize coordinator with all required services.
        
#         Args:
#             llm_service: LLM service instance
#             vector_store: Vector store instance
#             embedding_service: Embedding service instance
#             tavily_client: Tavily API client
#         """
#         self.llm_service = llm_service
#         self.vector_store = vector_store
#         self.embedding_service = embedding_service
#         self.tavily_client = tavily_client
        
#         # Initialize agents
#         self.planner = PlannerAgent(llm_service=llm_service)
#         self.search_agent = SearchAgent(
#             llm_service=llm_service,
#             tavily_client=tavily_client
#         )
#         self.rag_agent = RAGAgent(
#             llm_service=llm_service,
#             vector_store=vector_store,
#             embedding_service=embedding_service
#         )
#         self.answer_agent = AnswerAgent(llm_service=llm_service)
        
#         # Build LangGraph workflow
#         if LANGGRAPH_AVAILABLE:
#             self.workflow = self._build_langgraph_workflow()
#         else:
#             self.workflow = None
        
#         logger.info("[Coordinator] Multi-Agent Coordinator initialized")
#         logger.info(f"[Coordinator] Agents: {[self.planner.name, self.search_agent.name, self.rag_agent.name, self.answer_agent.name]}")
    
#     async def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
#         """
#         Execute multi-agent workflow for a query.
        
#         Args:
#             query: User query
#             context: Additional context (document_id, session_id, etc.)
            
#         Returns:
#             Dictionary with answer and execution metadata
#         """
#         context = context or {}
        
#         logger.info(f"\n{'='*80}")
#         logger.info(f"[Coordinator] Starting multi-agent execution")
#         logger.info(f"[Coordinator] Query: {query}")
#         logger.info(f"{'='*80}\n")
        
#         # Initialize state
#         state = AgentState(
#             agent_name="Coordinator",
#             query=query,
#             context=context
#         )
        
#         try:
#             if LANGGRAPH_AVAILABLE and self.workflow:
#                 # Use LangGraph workflow
#                 result = await self._execute_with_langgraph(state)
#             else:
#                 # Fallback to sequential execution
#                 result = await self._execute_sequential(state)
            
#             return result
            
#         except Exception as e:
#             logger.error(f"[Coordinator] Execution failed: {e}", exc_info=True)
#             return {
#                 "answer": "I apologize, but I encountered an error while processing your query.",
#                 "strategy_used": "error",
#                 "retrieved_chunks": [],
#                 "confidence": 0.0,
#                 "source": "error",
#                 "agent_type": "coordinator",
#                 "execution_steps": state.execution_steps,
#                 "error": str(e)
#             }
    
#     def _build_langgraph_workflow(self) -> StateGraph:
#         """
#         Build LangGraph state machine for agent coordination.
        
#         Returns:
#             StateGraph workflow
#         """
#         logger.info("[Coordinator] Building LangGraph workflow...")
        
#         # Define workflow
#         workflow = StateGraph(dict)
        
#         # Add nodes (agents)
#         workflow.add_node("planner", self._planner_node)
#         workflow.add_node("rag", self._rag_node)
#         workflow.add_node("search", self._search_node)
#         workflow.add_node("answer", self._answer_node)
        
#         # Define edges
#         workflow.set_entry_point("planner")
        
#         # Conditional routing from planner
#         workflow.add_conditional_edges(
#             "planner",
#             self._route_from_planner,
#             {
#                 "rag_only": "rag",
#                 "search_only": "search",
#                 "rag_then_search": "rag",
#                 "both_parallel": "rag",  # Start with RAG in parallel mode
#                 "answer_direct": "answer"
#             }
#         )
        
#         # RAG can go to search or answer
#         workflow.add_conditional_edges(
#             "rag",
#             self._route_from_rag,
#             {
#                 "search": "search",
#                 "answer": "answer"
#             }
#         )
        
#         # Search always goes to answer
#         workflow.add_edge("search", "answer")
        
#         # Answer is terminal
#         workflow.add_edge("answer", END)
        
#         # Compile workflow
#         app = workflow.compile()
        
#         logger.info("[Coordinator] LangGraph workflow built successfully")
        
#         return app
    
#     async def _planner_node(self, state: dict) -> dict:
#         """Planner agent node"""
#         logger.info("[Planner Node] Starting...")
        
#         agent_state = AgentState(
#             agent_name="Planner",
#             query=state["query"],
#             context=state.get("context", {})
#         )
        
#         result = await self.planner.execute(agent_state)
        
#         # Parse plan
#         try:
#             plan_data = json.loads(result.output)
#             state["execution_plan"] = plan_data["execution_plan"]
#             state["query_type"] = plan_data["query_type"]
#         except:
#             # Default plan
#             state["execution_plan"] = {
#                 "agents": ["RAGAgent", "AnswerAgent"],
#                 "strategy": "simple"
#             }
        
#         state["planner_steps"] = result.execution_steps
        
#         logger.info(f"[Planner Node] Plan: {state['execution_plan']['strategy']}")
        
#         return state
    
#     async def _rag_node(self, state: dict) -> dict:
#         """RAG agent node"""
#         logger.info("[RAG Node] Starting...")
        
#         agent_state = AgentState(
#             agent_name="RAGAgent",
#             query=state["query"],
#             context=state.get("context", {})
#         )
        
#         result = await self.rag_agent.execute(agent_state)
        
#         state["rag_result"] = result
#         state["rag_success"] = result.success
#         state["rag_steps"] = result.execution_steps
        
#         if result.success:
#             state["rag_context"] = result.output
#             state["retrieved_chunks"] = agent_state.metadata.get("retrieved_chunks", [])
#             state["relevance_check"] = agent_state.metadata.get("relevance_check", {})
        
#         logger.info(f"[RAG Node] Success: {result.success}, Confidence: {result.confidence}")
        
#         return state
    
#     async def _search_node(self, state: dict) -> dict:
#         """Search agent node"""
#         logger.info("[Search Node] Starting...")
        
#         agent_state = AgentState(
#             agent_name="SearchAgent",
#             query=state["query"],
#             context=state.get("context", {})
#         )
        
#         result = await self.search_agent.execute(agent_state)
        
#         state["search_result"] = result
#         state["search_success"] = result.success
#         state["search_steps"] = result.execution_steps
        
#         if result.success:
#             state["search_context"] = result.output
#             state["internet_sources"] = agent_state.metadata.get("search_results", {})
        
#         logger.info(f"[Search Node] Success: {result.success}")
        
#         return state
    
#     async def _answer_node(self, state: dict) -> dict:
#         """Answer agent node"""
#         logger.info("[Answer Node] Starting...")
        
#         # Prepare context for answer agent
#         agent_state = AgentState(
#             agent_name="AnswerAgent",
#             query=state["query"],
#             context=state.get("context", {})
#         )
        
#         # Add RAG context if available
#         if state.get("rag_success"):
#             agent_state.metadata["retrieved_chunks"] = state.get("retrieved_chunks", [])
#             agent_state.metadata["relevance_check"] = state.get("relevance_check", {})
        
#         # Add search context if available
#         if state.get("search_success"):
#             agent_state.metadata["search_results"] = state.get("internet_sources", {})
#             agent_state.metadata["tavily_answer"] = state.get("search_context", "")
        
#         result = await self.answer_agent.execute(agent_state)
        
#         state["final_answer"] = result.output
#         state["answer_confidence"] = result.confidence
#         state["answer_steps"] = result.execution_steps
        
#         logger.info(f"[Answer Node] Generated answer ({len(result.output)} chars)")
        
#         return state
    
#     def _route_from_planner(self, state: dict) -> str:
#         """Route from planner based on execution plan"""
#         plan = state.get("execution_plan", {})
#         strategy = plan.get("strategy", "simple")
        
#         routing_map = {
#             "simple_rag": "rag_only",
#             "internet_first": "search_only",
#             "internet_search": "search_only",
#             "rag_with_fallback": "rag_then_search",
#             "comprehensive": "both_parallel",
#             "summarization": "rag_only",
#         }
        
#         route = routing_map.get(strategy, "rag_only")
        
#         logger.info(f"[Router] Strategy '{strategy}' -> Route '{route}'")
        
#         return route
    
#     def _route_from_rag(self, state: dict) -> str:
#         """Route from RAG based on success"""
#         if state.get("rag_success"):
#             # Check relevance
#             relevance = state.get("relevance_check", {})
#             if relevance.get("is_relevant", True):
#                 return "answer"
        
#         # RAG failed or not relevant - try search if in plan
#         plan = state.get("execution_plan", {})
#         if "SearchAgent" in plan.get("agents", []):
#             return "search"
        
#         # No search available, go to answer anyway
#         return "answer"
    
#     async def _execute_with_langgraph(self, state: AgentState) -> Dict[str, Any]:
#         """Execute using LangGraph workflow"""
#         logger.info("[Coordinator] Executing with LangGraph...")
        
#         # Prepare initial state
#         graph_state = {
#             "query": state.query,
#             "context": state.context,
#             "execution_steps": [],
#         }
        
#         # Run workflow
#         final_state = await self.workflow.ainvoke(graph_state)
        
#         # Collect all execution steps
#         all_steps = []
#         for key in ["planner_steps", "rag_steps", "search_steps", "answer_steps"]:
#             if key in final_state:
#                 all_steps.extend(final_state[key])
        
#         # Determine source
#         source = "unknown"
#         if final_state.get("rag_success") and final_state.get("search_success"):
#             source = "rag_and_internet"
#         elif final_state.get("rag_success"):
#             source = "documents"
#         elif final_state.get("search_success"):
#             source = "internet"
#         else:
#             source = "general_knowledge"
        
#         return {
#             "answer": final_state.get("final_answer", "No answer generated"),
#             "strategy_used": final_state.get("execution_plan", {}).get("strategy", "auto"),
#             "retrieved_chunks": final_state.get("retrieved_chunks", []),
#             "confidence": final_state.get("answer_confidence", 0.7),
#             "source": source,
#             "agent_type": "multi_agent_langgraph",
#             "execution_steps": all_steps,
#             "internet_sources": final_state.get("internet_sources", {}),
#             "query_type": final_state.get("query_type", "unknown")
#         }
    
#     async def _execute_sequential(self, state: AgentState) -> Dict[str, Any]:
#         """Fallback sequential execution without LangGraph"""
#         logger.info("[Coordinator] Executing sequentially (fallback mode)...")
        
#         all_steps = []
        
#         # 1. Planner
#         logger.info("[Step 1] Planning...")
#         plan_result = await self.planner.execute(state)
#         all_steps.extend(plan_result.execution_steps)
        
#         try:
#             plan_data = json.loads(plan_result.output)
#             execution_plan = plan_data["execution_plan"]
#         except:
#             execution_plan = {"agents": ["RAGAgent", "AnswerAgent"], "strategy": "simple"}
        
#         # 2. Execute based on plan
#         rag_success = False
#         search_success = False
        
#         if "RAGAgent" in execution_plan.get("agents", []):
#             logger.info("[Step 2] RAG Retrieval...")
#             rag_result = await self.rag_agent.execute(state)
#             all_steps.extend(rag_result.execution_steps)
#             rag_success = rag_result.success
        
#         if "SearchAgent" in execution_plan.get("agents", []):
#             # Only search if RAG failed or strategy requires it
#             if not rag_success or execution_plan.get("requires_internet"):
#                 logger.info("[Step 3] Web Search...")
#                 search_result = await self.search_agent.execute(state)
#                 all_steps.extend(search_result.execution_steps)
#                 search_success = search_result.success
        
#         # 3. Answer generation
#         logger.info("[Step 4] Generating Answer...")
#         answer_result = await self.answer_agent.execute(state)
#         all_steps.extend(answer_result.execution_steps)
        
#         # Determine source
#         source = "unknown"
#         if rag_success and search_success:
#             source = "rag_and_internet"
#         elif rag_success:
#             source = "documents"
#         elif search_success:
#             source = "internet"
#         else:
#             source = "general_knowledge"
        
#         return {
#             "answer": answer_result.output,
#             "strategy_used": execution_plan.get("strategy", "sequential"),
#             "retrieved_chunks": state.metadata.get("retrieved_chunks", []),
#             "confidence": answer_result.confidence,
#             "source": source,
#             "agent_type": "multi_agent_sequential",
#             "execution_steps": all_steps,
#             "internet_sources": state.metadata.get("search_results", {})
#         }
    
#     def get_agent_status(self) -> Dict[str, Any]:
#         """Get status of all agents"""
#         return {
#             "coordinator": "active",
#             "langgraph_enabled": LANGGRAPH_AVAILABLE,
#             "agents": {
#                 "planner": self.planner.get_capabilities(),
#                 "search": self.search_agent.get_capabilities(),
#                 "rag": self.rag_agent.get_capabilities(),
#                 "answer": self.answer_agent.get_capabilities()
#             }
#         }






"""
Multi-Agent Coordinator using LangGraph
Orchestrates Planner, Search, RAG, and Answer agents
"""
from typing import Dict, Any, Optional, List
import logging
from django.conf import settings
from .base_agent import AgentState, AgentResult
from .planner_agent import PlannerAgent
from .search_agent import SearchAgent
from .rag_agent import RAGAgent
from .answer_agent import AnswerAgent
# ✅ NEW IMPORT — QueryEnhancer from document_processor
from ..document_processor import QueryEnhancer
import json

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("[Coordinator] LangGraph not available, using fallback coordination")

logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """
    Coordinates multiple specialized agents using LangGraph.
    
    Workflow:
    1. Planner analyzes query and creates execution plan
    2. Execute agents based on plan (RAG, Search, or both)
    3. Answer agent synthesizes final response
    """
    
    def __init__(
        self,
        llm_service=None,
        vector_store=None,
        embedding_service=None,
        tavily_client=None
    ):
        """
        Initialize coordinator with all required services.
        
        Args:
            llm_service: LLM service instance
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            tavily_client: Tavily API client
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.tavily_client = tavily_client
        
        # Initialize agents
        self.planner = PlannerAgent(llm_service=llm_service)
        self.search_agent = SearchAgent(
            llm_service=llm_service,
            tavily_client=tavily_client
        )
        self.rag_agent = RAGAgent(
            llm_service=llm_service,
            vector_store=vector_store,
            embedding_service=embedding_service
        )
        self.answer_agent = AnswerAgent(llm_service=llm_service)

        # ✅ NEW — Initialize QueryEnhancer
        self.query_enhancer = QueryEnhancer()
        
        # Build LangGraph workflow
        if LANGGRAPH_AVAILABLE:
            self.workflow = self._build_langgraph_workflow()
        else:
            self.workflow = None
        
        logger.info("[Coordinator] Multi-Agent Coordinator initialized")
        logger.info(f"[Coordinator] Agents: {[self.planner.name, self.search_agent.name, self.rag_agent.name, self.answer_agent.name]}")
    
    async def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute multi-agent workflow for a query.
        
        Args:
            query: User query
            context: Additional context (document_id, session_id, etc.)
            
        Returns:
            Dictionary with answer and execution metadata
        """
        context = context or {}

        # ✅ NEW — Enhance weak/vague queries before passing to any agent
        # Fixes: "tell me about this cv" → "tell me about Syed_Shahzad_Ali.pdf"
        # Fixes: "skills of this document" → "skills of Students_Data.csv"
        active_file = context.get("document_filter", None)
        enhanced_query = self.query_enhancer.enhance(query, active_file)
        if enhanced_query != query:
            logger.info(f"[Coordinator] Query enhanced: '{query}' → '{enhanced_query}'")
            query = enhanced_query  # all agents now use the enhanced query
        
        logger.info(f"\n{'='*80}")
        logger.info(f"[Coordinator] Starting multi-agent execution")
        logger.info(f"[Coordinator] Query: {query}")
        logger.info(f"{'='*80}\n")
        
        # Initialize state
        state = AgentState(
            agent_name="Coordinator",
            query=query,
            context=context
        )
        
        try:
            if LANGGRAPH_AVAILABLE and self.workflow:
                # Use LangGraph workflow
                result = await self._execute_with_langgraph(state)
            else:
                # Fallback to sequential execution
                result = await self._execute_sequential(state)
            
            return result
            
        except Exception as e:
            logger.error(f"[Coordinator] Execution failed: {e}", exc_info=True)
            return {
                "answer": "I apologize, but I encountered an error while processing your query.",
                "strategy_used": "error",
                "retrieved_chunks": [],
                "confidence": 0.0,
                "source": "error",
                "agent_type": "coordinator",
                "execution_steps": state.execution_steps,
                "error": str(e)
            }
    
    def _build_langgraph_workflow(self) -> StateGraph:
        """
        Build LangGraph state machine for agent coordination.
        
        Returns:
            StateGraph workflow
        """
        logger.info("[Coordinator] Building LangGraph workflow...")
        
        # Define workflow
        workflow = StateGraph(dict)
        
        # Add nodes (agents)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("rag", self._rag_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("answer", self._answer_node)
        
        # Define edges
        workflow.set_entry_point("planner")
        
        # Conditional routing from planner
        workflow.add_conditional_edges(
            "planner",
            self._route_from_planner,
            {
                "rag_only": "rag",
                "search_only": "search",
                "rag_then_search": "rag",
                "both_parallel": "rag",  # Start with RAG in parallel mode
                "answer_direct": "answer"
            }
        )
        
        # RAG can go to search or answer
        workflow.add_conditional_edges(
            "rag",
            self._route_from_rag,
            {
                "search": "search",
                "answer": "answer"
            }
        )
        
        # Search always goes to answer
        workflow.add_edge("search", "answer")
        
        # Answer is terminal
        workflow.add_edge("answer", END)
        
        # Compile workflow
        app = workflow.compile()
        
        logger.info("[Coordinator] LangGraph workflow built successfully")
        
        return app
    
    async def _planner_node(self, state: dict) -> dict:
        """Planner agent node"""
        logger.info("[Planner Node] Starting...")
        
        agent_state = AgentState(
            agent_name="Planner",
            query=state["query"],
            context=state.get("context", {})
        )
        
        result = await self.planner.execute(agent_state)
        
        # Parse plan
        try:
            plan_data = json.loads(result.output)
            state["execution_plan"] = plan_data["execution_plan"]
            state["query_type"] = plan_data["query_type"]
        except:
            # Default plan
            state["execution_plan"] = {
                "agents": ["RAGAgent", "AnswerAgent"],
                "strategy": "simple"
            }
        
        state["planner_steps"] = result.execution_steps
        
        logger.info(f"[Planner Node] Plan: {state['execution_plan']['strategy']}")
        
        return state
    
    async def _rag_node(self, state: dict) -> dict:
        """RAG agent node"""
        logger.info("[RAG Node] Starting...")
        
        agent_state = AgentState(
            agent_name="RAGAgent",
            query=state["query"],
            context=state.get("context", {})
        )
        
        result = await self.rag_agent.execute(agent_state)
        
        state["rag_result"] = result
        state["rag_success"] = result.success
        state["rag_steps"] = result.execution_steps
        
        if result.success:
            state["rag_context"] = result.output
            state["retrieved_chunks"] = agent_state.metadata.get("retrieved_chunks", [])
            state["relevance_check"] = agent_state.metadata.get("relevance_check", {})
        
        logger.info(f"[RAG Node] Success: {result.success}, Confidence: {result.confidence}")
        
        return state
    
    async def _search_node(self, state: dict) -> dict:
        """Search agent node"""
        logger.info("[Search Node] Starting...")
        
        agent_state = AgentState(
            agent_name="SearchAgent",
            query=state["query"],
            context=state.get("context", {})
        )
        
        result = await self.search_agent.execute(agent_state)
        
        state["search_result"] = result
        state["search_success"] = result.success
        state["search_steps"] = result.execution_steps
        
        if result.success:
            state["search_context"] = result.output
            state["internet_sources"] = agent_state.metadata.get("search_results", {})
        
        logger.info(f"[Search Node] Success: {result.success}")
        
        return state
    
    async def _answer_node(self, state: dict) -> dict:
        """Answer agent node"""
        logger.info("[Answer Node] Starting...")
        
        # Prepare context for answer agent
        agent_state = AgentState(
            agent_name="AnswerAgent",
            query=state["query"],
            context=state.get("context", {})
        )
        
        # Add RAG context if available
        if state.get("rag_success"):
            agent_state.metadata["retrieved_chunks"] = state.get("retrieved_chunks", [])
            agent_state.metadata["relevance_check"] = state.get("relevance_check", {})
        
        # Add search context if available
        if state.get("search_success"):
            agent_state.metadata["search_results"] = state.get("internet_sources", {})
            agent_state.metadata["tavily_answer"] = state.get("search_context", "")
        
        result = await self.answer_agent.execute(agent_state)
        
        state["final_answer"] = result.output
        state["answer_confidence"] = result.confidence
        state["answer_steps"] = result.execution_steps
        
        logger.info(f"[Answer Node] Generated answer ({len(result.output)} chars)")
        
        return state
    
    def _route_from_planner(self, state: dict) -> str:
        """Route from planner based on execution plan"""
        plan = state.get("execution_plan", {})
        strategy = plan.get("strategy", "simple")
        
        routing_map = {
            "simple_rag": "rag_only",
            "internet_first": "search_only",
            "internet_search": "search_only",
            "rag_with_fallback": "rag_then_search",
            "comprehensive": "both_parallel",
            "summarization": "rag_only",
        }
        
        route = routing_map.get(strategy, "rag_only")
        
        logger.info(f"[Router] Strategy '{strategy}' -> Route '{route}'")
        
        return route
    
    def _route_from_rag(self, state: dict) -> str:
        """Route from RAG based on success"""
        if state.get("rag_success"):
            # Check relevance
            relevance = state.get("relevance_check", {})
            if relevance.get("is_relevant", True):
                return "answer"
        
        # RAG failed or not relevant - try search if in plan
        plan = state.get("execution_plan", {})
        if "SearchAgent" in plan.get("agents", []):
            return "search"
        
        # No search available, go to answer anyway
        return "answer"
    
    async def _execute_with_langgraph(self, state: AgentState) -> Dict[str, Any]:
        """Execute using LangGraph workflow"""
        logger.info("[Coordinator] Executing with LangGraph...")
        
        # Prepare initial state
        graph_state = {
            "query": state.query,
            "context": state.context,
            "execution_steps": [],
        }
        
        # Run workflow
        final_state = await self.workflow.ainvoke(graph_state)
        
        # Collect all execution steps
        all_steps = []
        for key in ["planner_steps", "rag_steps", "search_steps", "answer_steps"]:
            if key in final_state:
                all_steps.extend(final_state[key])
        
        # Determine source
        source = "unknown"
        if final_state.get("rag_success") and final_state.get("search_success"):
            source = "rag_and_internet"
        elif final_state.get("rag_success"):
            source = "documents"
        elif final_state.get("search_success"):
            source = "internet"
        else:
            source = "general_knowledge"
        
        return {
            "answer": final_state.get("final_answer", "No answer generated"),
            "strategy_used": final_state.get("execution_plan", {}).get("strategy", "auto"),
            "retrieved_chunks": final_state.get("retrieved_chunks", []),
            "confidence": final_state.get("answer_confidence", 0.7),
            "source": source,
            "agent_type": "multi_agent_langgraph",
            "execution_steps": all_steps,
            "internet_sources": final_state.get("internet_sources", {}),
            "query_type": final_state.get("query_type", "unknown")
        }
    
    async def _execute_sequential(self, state: AgentState) -> Dict[str, Any]:
        """Fallback sequential execution without LangGraph"""
        logger.info("[Coordinator] Executing sequentially (fallback mode)...")
        
        all_steps = []
        
        # 1. Planner
        logger.info("[Step 1] Planning...")
        plan_result = await self.planner.execute(state)
        all_steps.extend(plan_result.execution_steps)
        
        try:
            plan_data = json.loads(plan_result.output)
            execution_plan = plan_data["execution_plan"]
        except:
            execution_plan = {"agents": ["RAGAgent", "AnswerAgent"], "strategy": "simple"}
        
        # 2. Execute based on plan
        rag_success = False
        search_success = False
        
        if "RAGAgent" in execution_plan.get("agents", []):
            logger.info("[Step 2] RAG Retrieval...")
            rag_result = await self.rag_agent.execute(state)
            all_steps.extend(rag_result.execution_steps)
            rag_success = rag_result.success
        
        if "SearchAgent" in execution_plan.get("agents", []):
            # Only search if RAG failed or strategy requires it
            if not rag_success or execution_plan.get("requires_internet"):
                logger.info("[Step 3] Web Search...")
                search_result = await self.search_agent.execute(state)
                all_steps.extend(search_result.execution_steps)
                search_success = search_result.success
        
        # 3. Answer generation
        logger.info("[Step 4] Generating Answer...")
        answer_result = await self.answer_agent.execute(state)
        all_steps.extend(answer_result.execution_steps)
        
        # Determine source
        source = "unknown"
        if rag_success and search_success:
            source = "rag_and_internet"
        elif rag_success:
            source = "documents"
        elif search_success:
            source = "internet"
        else:
            source = "general_knowledge"
        
        return {
            "answer": answer_result.output,
            "strategy_used": execution_plan.get("strategy", "sequential"),
            "retrieved_chunks": state.metadata.get("retrieved_chunks", []),
            "confidence": answer_result.confidence,
            "source": source,
            "agent_type": "multi_agent_sequential",
            "execution_steps": all_steps,
            "internet_sources": state.metadata.get("search_results", {})
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "coordinator": "active",
            "langgraph_enabled": LANGGRAPH_AVAILABLE,
            "agents": {
                "planner": self.planner.get_capabilities(),
                "search": self.search_agent.get_capabilities(),
                "rag": self.rag_agent.get_capabilities(),
                "answer": self.answer_agent.get_capabilities()
            }
        }