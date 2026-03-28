"""
Search Agent - Web Search and Information Retrieval
Performs internet searches using Tavily API
"""
from typing import Dict, Any, List, Optional
import logging
from django.conf import settings
from .base_agent import BaseAgent, AgentState, AgentResult

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """
    Search Agent performs web searches to find current information.
    
    Responsibilities:
    - Perform web searches using Tavily API
    - Extract relevant information from search results
    - Validate and rank search results
    - Handle search failures gracefully
    """
    
    def __init__(self, llm_service=None, tavily_client=None):
        super().__init__(
            name="SearchAgent",
            description="Performs web searches for current information",
            llm_service=llm_service
        )
        self.tavily_client = tavily_client
        self.max_results = 5
    
    async def execute(self, state: AgentState) -> AgentResult:
        """
        Execute web search for the query.
        
        Args:
            state: Current agent state with query
            
        Returns:
            AgentResult with search results
        """
        query = state.query
        
        try:
            self.add_thought(state, f"Need to search the internet for: '{query}'")
            
            # Check if Tavily client is available
            if not self.tavily_client:
                self.add_error(state, "Tavily client not initialized")
                return self.create_result(
                    success=False,
                    output="Web search is not available (Tavily API not configured)",
                    state=state,
                    error="Tavily client not available"
                )
            
            # Optimize search query
            optimized_query = await self._optimize_search_query(query, state)
            
            # Perform search
            self.add_action(state, f"Searching web for: '{optimized_query}'", "tavily_search")
            
            search_results = await self._perform_search(optimized_query, state)
            
            if not search_results:
                self.add_observation(state, "No search results found")
                return self.create_result(
                    success=False,
                    output="No relevant information found on the internet",
                    state=state,
                    confidence=0.3
                )
            
            # Rank and filter results
            ranked_results = await self._rank_results(search_results, query, state)
            
            # Extract key information
            extracted_info = await self._extract_information(ranked_results, query, state)
            
            self.add_observation(
                state,
                f"Found {len(ranked_results)} relevant sources"
            )
            
            # Prepare result
            result_data = {
                "sources": ranked_results,
                "extracted_information": extracted_info,
                "query_used": optimized_query
            }
            
            state.metadata["search_results"] = result_data
            
            return self.create_result(
                success=True,
                output=extracted_info,
                state=state,
                confidence=0.85
            )
            
        except Exception as e:
            self.add_error(state, f"Search failed: {str(e)}")
            logger.error(f"[SearchAgent] Search error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output="",
                state=state,
                error=str(e)
            )
    
    async def _optimize_search_query(self, query: str, state: AgentState) -> str:
        """
        Optimize query for better search results.
        
        Args:
            query: Original query
            state: Agent state
            
        Returns:
            Optimized search query
        """
        self.add_action(state, "Optimizing search query", "query_optimizer")
        
        # For now, use the original query
        # In production, you could use LLM to optimize
        optimized = query.strip()
        
        # Remove question words that don't help search
        remove_words = ["what", "how", "why", "when", "where", "who", "is", "are", "the"]
        words = optimized.lower().split()
        
        # Keep important context words
        if len(words) > 5:
            filtered = [w for w in words if w not in remove_words or words.index(w) > 2]
            if filtered:
                optimized = " ".join(filtered)
        
        self.add_observation(state, f"Optimized query: '{optimized}'")
        
        return optimized
    
    async def _perform_search(self, query: str, state: AgentState) -> List[Dict[str, Any]]:
        """
        Perform actual web search using Tavily.
        
        Args:
            query: Search query
            state: Agent state
            
        Returns:
            List of search results
        """
        try:
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",  # or "basic"
                max_results=self.max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            results = []
            
            # Process Tavily results
            if response and "results" in response:
                for item in response["results"]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0.0),
                        "source": self._extract_domain(item.get("url", ""))
                    })
            
            # Add Tavily's answer if available
            if response.get("answer"):
                state.metadata["tavily_answer"] = response["answer"]
            
            return results
            
        except Exception as e:
            logger.error(f"[SearchAgent] Tavily search failed: {e}")
            return []
    
    async def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        Rank search results by relevance.
        
        Args:
            results: Search results
            query: Original query
            state: Agent state
            
        Returns:
            Ranked results
        """
        self.add_action(state, "Ranking search results", "result_ranker")
        
        # Sort by Tavily's score
        ranked = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)
        
        # Take top results
        top_results = ranked[:self.max_results]
        
        self.add_observation(state, f"Selected top {len(top_results)} results")
        
        return top_results
    
    async def _extract_information(
        self,
        results: List[Dict[str, Any]],
        query: str,
        state: AgentState
    ) -> str:
        """
        Extract and synthesize information from search results.
        
        Args:
            results: Ranked search results
            query: Original query
            state: Agent state
            
        Returns:
            Extracted information as text
        """
        self.add_action(state, "Extracting information from sources", "information_extractor")
        
        if not results:
            return "No information available"
        
        # Combine content from top sources
        combined_content = []
        
        for i, result in enumerate(results[:3], 1):  # Top 3 sources
            content = result.get("content", "").strip()
            source = result.get("source", "Unknown")
            
            if content:
                combined_content.append(
                    f"[Source {i}: {source}]\n{content[:500]}..."  # Limit content length
                )
        
        # Use Tavily's answer if available
        if "tavily_answer" in state.metadata:
            return state.metadata["tavily_answer"]
        
        # Otherwise, combine sources
        return "\n\n".join(combined_content)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return "unknown"
    
    async def search_with_context(
        self,
        query: str,
        context: Optional[str] = None,
        state: Optional[AgentState] = None
    ) -> Dict[str, Any]:
        """
        Search with additional context.
        
        Args:
            query: Search query
            context: Additional context
            state: Optional agent state
            
        Returns:
            Search results dictionary
        """
        if state is None:
            state = AgentState(agent_name=self.name, query=query)
        
        if context:
            # Enhance query with context
            enhanced_query = f"{query} {context}"
            state.query = enhanced_query
        
        result = await self.execute(state)
        
        return {
            "success": result.success,
            "results": state.metadata.get("search_results", {}),
            "execution_steps": result.execution_steps
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                "Web search (Tavily API)",
                "Query optimization",
                "Result ranking",
                "Information extraction",
                "Source validation"
            ],
            "output_format": "search_results_with_sources",
            "limitations": [
                "Requires Tavily API key",
                "Limited to recent/current information",
                "Depends on search engine quality"
            ]
        }