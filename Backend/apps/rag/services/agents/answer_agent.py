"""
Answer Agent - Response Synthesis and Generation
Generates final answers from context
"""
from typing import Dict, Any, List, Optional
import logging
from django.conf import settings
from .base_agent import BaseAgent, AgentState, AgentResult

logger = logging.getLogger(__name__)


class AnswerAgent(BaseAgent):
    """
    Answer Agent synthesizes final responses from available context.
    
    Responsibilities:
    - Generate coherent answers from context
    - Cite sources appropriately
    - Handle multiple context sources
    - Ensure answer quality and accuracy
    """
    
    def __init__(self, llm_service=None):
        super().__init__(
            name="AnswerAgent",
            description="Generates final answers from context",
            llm_service=llm_service
        )
    
    async def execute(self, state: AgentState) -> AgentResult:
        """
        Generate answer from available context.
        
        Args:
            state: Current agent state with query and context
            
        Returns:
            AgentResult with synthesized answer
        """
        query = state.query
        context_data = state.context
        
        try:
            self.add_thought(state, "Synthesizing answer from available context")
            
            # Gather all available context
            contexts = await self._gather_contexts(state)
            
            if not contexts:
                self.add_observation(state, "No context available, using general knowledge")
                return await self._general_knowledge_answer(query, state)
            
            # Build the answer
            self.add_action(state, "Generating answer from context", "llm_generation")
            
            answer = await self._generate_answer(query, contexts, state)
            
            # Add citations if sources available
            answer_with_citations = await self._add_citations(answer, contexts, state)
            
            self.add_observation(state, f"Generated answer ({len(answer_with_citations)} characters)")
            
            # Calculate confidence based on context quality
            confidence = self._calculate_confidence(contexts, state)
            
            # Store answer metadata
            state.metadata["final_answer"] = answer_with_citations
            state.metadata["answer_confidence"] = confidence
            state.metadata["sources_used"] = [ctx["source"] for ctx in contexts]
            
            return self.create_result(
                success=True,
                output=answer_with_citations,
                state=state,
                confidence=confidence
            )
            
        except Exception as e:
            self.add_error(state, f"Answer generation failed: {str(e)}")
            logger.error(f"[AnswerAgent] Generation error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output="I apologize, but I encountered an error while generating the answer.",
                state=state,
                error=str(e)
            )
    
    async def _gather_contexts(self, state: AgentState) -> List[Dict[str, Any]]:
        """
        Gather all available context from metadata.
        
        Args:
            state: Agent state
            
        Returns:
            List of context dictionaries
        """
        contexts = []
        
        # Check for RAG context
        if "retrieved_chunks" in state.metadata:
            chunks = state.metadata["retrieved_chunks"]
            for chunk in chunks:
                contexts.append({
                    "source": "document",
                    "type": "rag",
                    "content": chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {})
                })
        
        # Check for search results
        if "search_results" in state.metadata:
            search_data = state.metadata["search_results"]
            
            # Use extracted information if available
            if "extracted_information" in search_data:
                contexts.append({
                    "source": "internet",
                    "type": "search",
                    "content": search_data["extracted_information"],
                    "metadata": {"sources": search_data.get("sources", [])}
                })
            
            # Or individual sources
            elif "sources" in search_data:
                for source in search_data["sources"][:3]:  # Top 3
                    contexts.append({
                        "source": "internet",
                        "type": "search",
                        "content": source.get("content", ""),
                        "metadata": {"url": source.get("url", ""), "title": source.get("title", "")}
                    })
        
        # Check for Tavily answer
        if "tavily_answer" in state.metadata:
            contexts.append({
                "source": "internet",
                "type": "tavily_answer",
                "content": state.metadata["tavily_answer"],
                "metadata": {}
            })
        
        return contexts
    
    async def _generate_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        state: AgentState
    ) -> str:
        """
        Generate answer using LLM.
        
        Args:
            query: User query
            contexts: Available contexts
            state: Agent state
            
        Returns:
            Generated answer
        """
        # Build context string
        context_text = self._build_context_string(contexts)
        
        # Build prompt
        prompt = self._build_answer_prompt(query, context_text, contexts)
        
        # Generate answer
        try:
            answer = await self.call_llm(
                prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            return answer.strip()
            
        except Exception as e:
            logger.error(f"[AnswerAgent] LLM generation failed: {e}")
            raise
    
    def _build_context_string(self, contexts: List[Dict[str, Any]]) -> str:
        """Build formatted context string"""
        if not contexts:
            return "No context available"
        
        formatted = []
        
        for i, ctx in enumerate(contexts, 1):
            source_type = ctx.get("type", "unknown")
            content = ctx.get("content", "")
            
            if source_type == "rag":
                metadata = ctx.get("metadata", {})
                source = metadata.get("source", "Document")
                formatted.append(f"[Source {i}: {source}]\n{content}\n")
            
            elif source_type == "search":
                metadata = ctx.get("metadata", {})
                title = metadata.get("title", "Web")
                formatted.append(f"[Source {i}: {title}]\n{content}\n")
            
            else:
                formatted.append(f"[Source {i}]\n{content}\n")
        
        return "\n".join(formatted)
    
    def _build_answer_prompt(
        self,
        query: str,
        context_text: str,
        contexts: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for answer generation"""
        
        # Determine source types
        has_documents = any(ctx.get("type") == "rag" for ctx in contexts)
        has_internet = any(ctx.get("type") in ["search", "tavily_answer"] for ctx in contexts)
        
        source_instruction = ""
        if has_documents and has_internet:
            source_instruction = "Use information from both the documents and internet sources."
        elif has_documents:
            source_instruction = "Use only the information from the provided documents."
        elif has_internet:
            source_instruction = "Use the information from internet search results."
        
        prompt = f"""You are an intelligent AI assistant. Answer the question using the provided context.

{source_instruction}

RULES:
1. Provide a clear, comprehensive answer
2. Use ONLY information from the context - do not hallucinate
3. If the context doesn't contain the answer, say "I don't have enough information to answer this question."
4. Be concise but thorough
5. Maintain a professional, helpful tone
6. If using multiple sources, synthesize the information coherently

--- CONTEXT ---
{context_text}

--- QUESTION ---
{query}

--- YOUR ANSWER ---
"""
        
        return prompt.strip()
    
    async def _add_citations(
        self,
        answer: str,
        contexts: List[Dict[str, Any]],
        state: AgentState
    ) -> str:
        """
        Add source citations to answer.
        
        Args:
            answer: Generated answer
            contexts: Contexts used
            state: Agent state
            
        Returns:
            Answer with citations
        """
        # Don't add citations if no specific sources
        if not contexts or "I don't have enough information" in answer:
            return answer
        
        # Build citations section
        citations = []
        
        # Document sources
        doc_sources = [ctx for ctx in contexts if ctx.get("type") == "rag"]
        if doc_sources:
            unique_docs = set()
            for ctx in doc_sources:
                metadata = ctx.get("metadata", {})
                source = metadata.get("source", "Unknown")
                unique_docs.add(source)
            
            if unique_docs:
                citations.append("\n\n**Sources (Documents):**")
                for doc in unique_docs:
                    citations.append(f"- {doc}")
        
        # Internet sources
        search_sources = [ctx for ctx in contexts if ctx.get("type") == "search"]
        if search_sources:
            citations.append("\n**Sources (Internet):**")
            seen_urls = set()
            for ctx in search_sources:
                metadata = ctx.get("metadata", {})
                url = metadata.get("url", "")
                title = metadata.get("title", "Web source")
                
                if url and url not in seen_urls:
                    citations.append(f"- {title}: {url}")
                    seen_urls.add(url)
        
        if citations:
            return answer + "\n" + "\n".join(citations)
        
        return answer
    
    async def _general_knowledge_answer(
        self,
        query: str,
        state: AgentState
    ) -> AgentResult:
        """
        Generate answer using general knowledge (no specific context).
        
        Args:
            query: User query
            state: Agent state
            
        Returns:
            AgentResult with general answer
        """
        self.add_action(state, "Generating answer from general knowledge", "llm_generation")
        
        prompt = f"""You are a helpful AI assistant. Answer this question using your general knowledge.

RULES:
1. Be honest if you don't know something
2. Provide factual, accurate information
3. Be concise but helpful
4. If the question requires specific/current data you don't have, acknowledge this

Question: {query}

Answer:"""
        
        try:
            answer = await self.call_llm(prompt, temperature=0.5, max_tokens=500)
            
            # Add disclaimer
            answer_with_note = answer.strip() + "\n\n*Note: This answer is based on general knowledge. For specific information, please provide relevant documents.*"
            
            self.add_observation(state, "Generated answer from general knowledge")
            
            return self.create_result(
                success=True,
                output=answer_with_note,
                state=state,
                confidence=0.6
            )
            
        except Exception as e:
            logger.error(f"[AnswerAgent] General knowledge answer failed: {e}")
            return self.create_result(
                success=False,
                output="I apologize, but I'm unable to generate an answer at this time.",
                state=state,
                error=str(e)
            )
    
    def _calculate_confidence(
        self,
        contexts: List[Dict[str, Any]],
        state: AgentState
    ) -> float:
        """
        Calculate answer confidence based on context quality.
        
        Args:
            contexts: Available contexts
            state: Agent state
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not contexts:
            return 0.5  # Medium confidence for general knowledge
        
        base_confidence = 0.7
        
        # Boost for multiple sources
        if len(contexts) >= 3:
            base_confidence += 0.1
        
        # Boost for document sources
        has_docs = any(ctx.get("type") == "rag" for ctx in contexts)
        if has_docs:
            base_confidence += 0.1
        
        # Check relevance score if available
        if "relevance_check" in state.metadata:
            relevance = state.metadata["relevance_check"]
            relevance_score = relevance.get("score", 0.7)
            base_confidence = (base_confidence + relevance_score) / 2
        
        return min(base_confidence, 0.95)  # Cap at 0.95
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                "Multi-source synthesis",
                "Citation generation",
                "General knowledge fallback",
                "Quality assessment",
                "Coherent answer generation"
            ],
            "output_format": "formatted_answer_with_citations",
            "strengths": [
                "Handles multiple context types",
                "Provides source attribution",
                "Maintains accuracy"
            ]
        }