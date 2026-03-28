"""
Base Agent Class for Multi-Agent System
Provides common functionality for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message passed between agents"""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    

@dataclass
class AgentStep:
    """Single execution step in agent reasoning"""
    step_number: int
    step_type: str  # 'THOUGHT', 'ACTION', 'OBSERVATION', 'ERROR'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Agent state for tracking execution"""
    agent_name: str
    query: str
    context: Dict[str, Any] = field(default_factory=dict)
    messages: List[AgentMessage] = field(default_factory=list)
    execution_steps: List[AgentStep] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    output: str
    confidence: float = 0.7
    agent_name: str = ""
    execution_steps: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    Each agent must implement:
    - execute(): Main execution logic
    - get_capabilities(): Description of what the agent can do
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_service=None,
        max_iterations: int = 5
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description and capabilities
            llm_service: LLM service instance
            max_iterations: Maximum iterations for reasoning loops
        """
        self.name = name
        self.description = description
        self.llm_service = llm_service
        self.max_iterations = max_iterations
        
        self.execution_id = None
        self.state = None
        
        logger.info(f"[{self.name}] Agent initialized")
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Args:
            state: Current agent state
            
        Returns:
            AgentResult with output and metadata
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return agent capabilities and metadata.
        
        Returns:
            Dictionary describing agent capabilities
        """
        pass
    
    def add_thought(self, state: AgentState, thought: str) -> None:
        """Add a thought step to execution trace"""
        step = AgentStep(
            step_number=len(state.execution_steps) + 1,
            step_type="THOUGHT",
            content=thought
        )
        state.execution_steps.append(step)
        logger.debug(f"[{self.name}] THOUGHT: {thought}")
    
    def add_action(self, state: AgentState, action: str, tool_name: str = None) -> None:
        """Add an action step to execution trace"""
        step = AgentStep(
            step_number=len(state.execution_steps) + 1,
            step_type="ACTION",
            content=action,
            metadata={"tool": tool_name} if tool_name else {}
        )
        state.execution_steps.append(step)
        if tool_name:
            state.tools_used.append(tool_name)
        logger.debug(f"[{self.name}] ACTION: {action}")
    
    def add_observation(self, state: AgentState, observation: str) -> None:
        """Add an observation step to execution trace"""
        step = AgentStep(
            step_number=len(state.execution_steps) + 1,
            step_type="OBSERVATION",
            content=observation
        )
        state.execution_steps.append(step)
        logger.debug(f"[{self.name}] OBSERVATION: {observation}")
    
    def add_error(self, state: AgentState, error: str) -> None:
        """Add an error step to execution trace"""
        step = AgentStep(
            step_number=len(state.execution_steps) + 1,
            step_type="ERROR",
            content=error
        )
        state.execution_steps.append(step)
        logger.error(f"[{self.name}] ERROR: {error}")
    
    async def call_llm(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Call LLM service with prompt.
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response text
        """
        if not self.llm_service:
            raise ValueError(f"[{self.name}] LLM service not initialized")
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"[{self.name}] LLM call failed: {str(e)}")
            raise
    
    def create_result(
        self,
        success: bool,
        output: str,
        state: AgentState,
        confidence: float = 0.7,
        error: Optional[str] = None
    ) -> AgentResult:
        """
        Create standardized agent result.
        
        Args:
            success: Whether execution was successful
            output: Agent output
            state: Current agent state
            confidence: Confidence score
            error: Optional error message
            
        Returns:
            AgentResult object
        """
        return AgentResult(
            success=success,
            output=output,
            confidence=confidence,
            agent_name=self.name,
            execution_steps=[
                {
                    "step_number": step.step_number,
                    "type": step.step_type,
                    "content": step.content,
                    "timestamp": step.timestamp,
                    "metadata": step.metadata
                }
                for step in state.execution_steps
            ],
            tools_used=list(set(state.tools_used)),  # Deduplicate
            metadata={
                **state.metadata,
                "agent_name": self.name,
                "total_steps": len(state.execution_steps)
            },
            error=error
        )
    
    def log_execution(self, state: AgentState, message: str, level: str = "info") -> None:
        """
        Log execution message.
        
        Args:
            state: Current agent state
            message: Message to log
            level: Log level (debug, info, warning, error)
        """
        log_msg = f"[{self.name}] {message}"
        
        if level == "debug":
            logger.debug(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        elif level == "error":
            logger.error(log_msg)
        else:
            logger.info(log_msg)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class ToolResult:
    """Result from tool execution"""
    
    def __init__(
        self,
        success: bool,
        output: Any,
        tool_name: str,
        execution_time: float = 0.0,
        error: Optional[str] = None
    ):
        self.success = success
        self.output = output
        self.tool_name = tool_name
        self.execution_time = execution_time
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "tool_name": self.tool_name,
            "execution_time": self.execution_time,
            "error": self.error
        }