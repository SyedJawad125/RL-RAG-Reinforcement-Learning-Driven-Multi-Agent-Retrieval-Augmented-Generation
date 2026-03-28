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
# # ✅ NEW IMPORT — QueryEnhancer from document_processor
# from ..document_processor import QueryEnhancer
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

#         # ✅ NEW — Initialize QueryEnhancer
#         self.query_enhancer = QueryEnhancer()
        
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

#         # ✅ NEW — Enhance weak/vague queries before passing to any agent
#         # Fixes: "tell me about this cv" → "tell me about Syed_Shahzad_Ali.pdf"
#         # Fixes: "skills of this document" → "skills of Students_Data.csv"
#         active_file = context.get("document_filter", None)
#         enhanced_query = self.query_enhancer.enhance(query, active_file)
#         if enhanced_query != query:
#             logger.info(f"[Coordinator] Query enhanced: '{query}' → '{enhanced_query}'")
#             query = enhanced_query  # all agents now use the enhanced query
        
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
Multi-Agent Coordinator — RL-Enhanced
--------------------------------------
Orchestrates the full query pipeline:

    User Query
        │
        ▼
    PlannerAgent          ← classifies query, determines complexity
        │
        ▼
    RLDecisionAgent  ◄──── Q-learning policy (core)
        │
        ├── RETRIEVE_MORE     → RAGAgent (extra retrieval)
        ├── RE_RANK           → RLDecisionAgent.re_rank_chunks()
        ├── ASK_CLARIFICATION → falls back to ANSWER_NOW (async-safe)
        └── ANSWER_NOW        → AnswerAgent (final synthesis)
                                    │
                                    ▼
                              record_experience()  ← reward + Q-update

The RL agent runs an inner decision loop (max MAX_STEPS steps).
After the loop, AnswerAgent always synthesises the final response.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from services.agents.base_agent   import AgentState
from services.agents.planner_agent import PlannerAgent
from services.agents.rag_agent    import RAGAgent
from services.agents.answer_agent import AnswerAgent
from services.agents.search_agent import SearchAgent
from services.agents.rl_agent     import RLDecisionAgent

logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """
    Central coordinator for the RL-enhanced multi-agent RAG system.

    Injected services (all singletons created in views.py):
        llm_service       – AsyncGroq wrapper
        vector_store      – ChromaDB wrapper
        embedding_service – SentenceTransformer wrapper
        tavily_client     – optional; enables web search
    """

    MAX_RL_STEPS = 5   # hard ceiling for the RL decision loop

    def __init__(
        self,
        llm_service,
        vector_store,
        embedding_service,
        tavily_client = None,
    ) -> None:
        self.llm_service       = llm_service
        self.vector_store      = vector_store
        self.embedding_service = embedding_service

        # Agents
        self.planner      = PlannerAgent(llm_service=llm_service)
        self.rl_agent     = RLDecisionAgent(llm_service=llm_service)
        self.rag_agent    = RAGAgent(
            llm_service       = llm_service,
            vector_store      = vector_store,
            embedding_service = embedding_service,
        )
        self.search_agent = SearchAgent(
            llm_service   = llm_service,
            tavily_client = tavily_client,
        )
        self.answer_agent = AnswerAgent(llm_service=llm_service)

        logger.info("[Coordinator] RL-Enhanced Multi-Agent Coordinator initialised")

    # ─────────────────────────────────────────────────────────────────────────
    #  PUBLIC ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────

    async def execute(
        self,
        query:    str,
        context:  Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Full pipeline execution.

        Args:
            query:   User's question
            context: Dict from views.py — may contain document_id,
                     document_filter, top_k, session_id, strategy

        Returns:
            Result dict with: answer, strategy_used, retrieved_chunks,
            confidence, execution_steps, internet_sources, rl_metadata
        """
        start        = time.time()
        query_id_str = str(uuid.uuid4())

        # Master agent state (shared across all agents in this request)
        state = AgentState(
            agent_name = "coordinator",
            query      = query,
            context    = context.copy(),
        )
        state.metadata["query_id"] = query_id_str

        try:
            # ── 1. PLANNER ────────────────────────────────────────────────
            plan_result = await self.planner.execute(state)
            self._extract_plan_metadata(plan_result, state)

            # ── 2. INITIAL RAG RETRIEVAL (always run once first) ──────────
            await self._run_rag(state)

            # ── 3. RL DECISION LOOP ───────────────────────────────────────
            for step in range(self.MAX_RL_STEPS):
                rl_result   = await self.rl_agent.execute(state)
                action_name = rl_result.output.strip()

                logger.info(f"[Coordinator] RL step {step + 1}/{self.MAX_RL_STEPS} → {action_name}")

                if action_name == "ANSWER_NOW" or step == self.MAX_RL_STEPS - 1:
                    # Terminal action — compute reward after answer
                    break

                elif action_name == "RETRIEVE_MORE":
                    await self._run_rag(state, extra=True)
                    self._record_non_terminal(state, query_id_str)

                elif action_name == "RE_RANK":
                    await self._do_rerank(query, state)
                    self._record_non_terminal(state, query_id_str)

                elif action_name == "ASK_CLARIFICATION":
                    # Cannot block for user input in async flow — fall through
                    logger.info("[Coordinator] ASK_CLARIFICATION → falling back to ANSWER_NOW")
                    break

            # ── 4. SEARCH (if plan requested it and no internet yet) ──────
            plan_needs_internet = state.metadata.get("requires_internet", False)
            if plan_needs_internet and "search_results" not in state.metadata:
                await self._run_search(state)

            # ── 5. ANSWER GENERATION ──────────────────────────────────────
            answer_result = await self.answer_agent.execute(state)

            # ── 6. TERMINAL REWARD ────────────────────────────────────────
            final_confidence = answer_result.confidence
            has_citations    = "**Sources" in (answer_result.output or "")

            next_state_data = {
                "confidence":      final_confidence,
                "retrieved_count": len(state.metadata.get("retrieved_chunks", [])),
                "complexity":      state.metadata.get("query_complexity", "medium"),
                "has_internet":    "search_results" in state.metadata,
                "has_citations":   has_citations,
            }
            self.rl_agent.record_experience(
                state           = state,
                next_state_data = next_state_data,
                done            = True,
                query_id        = query_id_str,
            )

            # ── 7. BUILD RESPONSE ─────────────────────────────────────────
            return self._build_response(
                query        = query,
                answer       = answer_result.output or "",
                state        = state,
                confidence   = final_confidence,
                start        = start,
                query_id_str = query_id_str,
            )

        except Exception as exc:
            logger.error(f"[Coordinator] execute failed: {exc}", exc_info=True)
            raise

    # ─────────────────────────────────────────────────────────────────────────
    #  AGENT RUNNERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _run_rag(self, state: AgentState, extra: bool = False) -> None:
        """
        Run RAGAgent and merge results into state.

        On extra=True (RETRIEVE_MORE action), bump top_k by 3.
        """
        if extra:
            state.context["top_k"] = state.context.get("top_k", 5) + 3
            logger.info(f"[Coordinator] RETRIEVE_MORE → top_k={state.context['top_k']}")

        result = await self.rag_agent.execute(state)

        if result.success and "retrieved_chunks" in result.metadata:
            existing = state.metadata.get("retrieved_chunks", [])
            new      = result.metadata.get("retrieved_chunks", [])
            # Deduplicate by content
            seen    = {c.get("content", "") for c in existing}
            merged  = existing + [c for c in new if c.get("content", "") not in seen]
            state.metadata["retrieved_chunks"] = merged

        # Carry relevance check forward
        if "relevance_check" in result.metadata:
            state.metadata["relevance_check"] = result.metadata["relevance_check"]

    async def _do_rerank(self, query: str, state: AgentState) -> None:
        """Re-rank existing chunks using the RL agent's LLM scorer."""
        chunks = state.metadata.get("retrieved_chunks", [])
        if not chunks:
            return
        re_ranked = await self.rl_agent.re_rank_chunks(query, chunks, state)
        state.metadata["retrieved_chunks"] = re_ranked

        # Update pseudo-confidence based on top chunk score
        if re_ranked:
            top_score = re_ranked[0].get("rl_rerank_score", 5) / 10.0
            state.metadata.setdefault("relevance_check", {})["score"] = top_score

    async def _run_search(self, state: AgentState) -> None:
        """Run SearchAgent and store results in state."""
        result = await self.search_agent.execute(state)
        if result.success:
            state.metadata.update(result.metadata)

    # ─────────────────────────────────────────────────────────────────────────
    #  REWARD HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _record_non_terminal(
        self,
        state:        AgentState,
        query_id_str: str,
    ) -> None:
        """Record a non-terminal reward after a RETRIEVE_MORE / RE_RANK action."""
        next_data = {
            "confidence":      state.metadata.get("relevance_check", {}).get("score", 0.5),
            "retrieved_count": len(state.metadata.get("retrieved_chunks", [])),
            "complexity":      state.metadata.get("query_complexity", "medium"),
            "has_internet":    "search_results" in state.metadata,
            "has_citations":   False,
        }
        self.rl_agent.record_experience(
            state           = state,
            next_state_data = next_data,
            done            = False,
            query_id        = query_id_str,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  PLAN EXTRACTION
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_plan_metadata(
        self,
        plan_result,
        state: AgentState,
    ) -> None:
        """Pull planner output into state.metadata."""
        import json
        try:
            plan_data = json.loads(plan_result.output or "{}")
            state.metadata["query_complexity"]  = plan_data.get("complexity", "medium")
            state.metadata["query_type"]        = plan_data.get("query_type", "factual_question")
            state.metadata["requires_internet"] = (
                plan_data.get("execution_plan", {}).get("requires_internet", False)
            )
            logger.info(
                f"[Coordinator] Plan: type={state.metadata['query_type']} | "
                f"complexity={state.metadata['query_complexity']} | "
                f"internet={state.metadata['requires_internet']}"
            )
        except Exception:
            state.metadata.setdefault("query_complexity",  "medium")
            state.metadata.setdefault("query_type",        "factual_question")
            state.metadata.setdefault("requires_internet", False)

    # ─────────────────────────────────────────────────────────────────────────
    #  RESPONSE BUILDER
    # ─────────────────────────────────────────────────────────────────────────

    def _build_response(
        self,
        query:        str,
        answer:       str,
        state:        AgentState,
        confidence:   float,
        start:        float,
        query_id_str: str,
    ) -> Dict[str, Any]:
        """Build the final dict that views.py returns to the client."""
        chunks          = state.metadata.get("retrieved_chunks", [])
        internet_data   = state.metadata.get("search_results", {})
        internet_sources = (
            internet_data.get("sources", []) if isinstance(internet_data, dict) else []
        )

        # Collect all execution steps from state
        execution_steps: List[Dict] = [
            {
                "step_number": s.step_number,
                "type":        s.step_type,
                "content":     s.content,
                "timestamp":   s.timestamp,
                "metadata":    s.metadata,
            }
            for s in state.execution_steps
        ]

        # RL metadata (surfaced to the client for transparency)
        rl_metadata = {
            "query_id":         query_id_str,
            "steps_taken":      state.metadata.get("rl_step_count",    0),
            "last_action":      state.metadata.get("rl_action_name",   "ANSWER_NOW"),
            "last_reward":      state.metadata.get("rl_reward",        0.0),
            "epsilon":          round(self.rl_agent.memory.q_table.epsilon, 4),
            "states_learned":   len(self.rl_agent.memory.q_table.table),
        }

        return {
            "answer":           answer,
            "confidence":       confidence,
            "retrieved_chunks": [
                {
                    "content":  c.get("content", ""),
                    "score":    c.get("score", 0.0),
                    "metadata": c.get("metadata", {}),
                }
                for c in chunks
            ],
            "execution_steps":  execution_steps,
            "internet_sources": internet_sources,
            "source":           "rl_multi_agent",
            "agent_type":       "rl_coordinator",
            "agents_used":      ["PlannerAgent", "RLDecisionAgent", "RAGAgent", "AnswerAgent"],
            "query_type":       state.metadata.get("query_type", "factual_question"),
            "rl_metadata":      rl_metadata,
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  AGENT STATUS
    # ─────────────────────────────────────────────────────────────────────────

    def get_agent_status(self) -> Dict[str, Any]:
        """Called by views.agent_status — includes RL stats."""
        agents = [
            self.planner, self.rl_agent,
            self.rag_agent, self.search_agent, self.answer_agent,
        ]
        return {
            "agents":    [a.get_capabilities() for a in agents],
            "rl_stats":  self.rl_agent.get_rl_stats(),
            "rl_enabled": True,
        }