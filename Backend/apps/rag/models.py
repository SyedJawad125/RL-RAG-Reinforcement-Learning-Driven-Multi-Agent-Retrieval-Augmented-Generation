"""
Django Models for Multi-Agent RAG System
8 database models with proper relationships and indexing
"""
from django.db import models
from django.utils import timezone
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Document(TimeStampedModel):
    """Document model for storing uploaded files"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField(help_text="File size in bytes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Counts
    chunks_count = models.IntegerField(default=0)
    entities_count = models.IntegerField(default=0)
    relationships_count = models.IntegerField(default=0)
    
    # Processing metadata
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['-uploaded_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.status})"


class DocumentChunk(TimeStampedModel):
    """Document chunks for vector search"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    
    content = models.TextField()
    chunk_index = models.IntegerField(db_index=True)
    
    # Vector embedding (stored as JSON array)
    embedding = models.JSONField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
        unique_together = [['document', 'chunk_index']]
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.filename}"


class Session(TimeStampedModel):
    """User session for tracking conversations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    message_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Session metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['-last_activity', 'is_active']),
        ]
    
    def __str__(self):
        return f"Session {self.id} ({self.user_id or 'anonymous'})"


class Query(TimeStampedModel):
    """Query execution history with agent traces"""
    
    STRATEGY_CHOICES = [
        ('simple', 'Simple'),
        ('agentic', 'Agentic'),
        ('multi_agent', 'Multi-Agent'),
        ('auto', 'Auto'),
    ]
    
    QUERY_TYPE_CHOICES = [
        ('question', 'Question'),
        ('search', 'Search'),
        ('analysis', 'Analysis'),
        ('summarization', 'Summarization'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='queries')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='queries')
    
    # Query details
    query_text = models.TextField()
    answer = models.TextField(null=True, blank=True)
    
    # Strategy & classification
    strategy_used = models.CharField(max_length=20, choices=STRATEGY_CHOICES, default='auto', db_index=True)
    query_type = models.CharField(max_length=20, choices=QUERY_TYPE_CHOICES, null=True, blank=True)
    
    # Performance metrics
    processing_time = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Agent metrics
    retrieved_chunks_count = models.IntegerField(default=0)
    agent_steps_count = models.IntegerField(default=0)
    agents_used = models.JSONField(default=list, blank=True)  # List of agent names
    
    # Metadata (includes execution trace, sources, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Queries'
        indexes = [
            models.Index(fields=['-created_at', 'strategy_used']),
            models.Index(fields=['session', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.query_text[:50]}... ({self.strategy_used})"


class AgentExecution(TimeStampedModel):
    """Agent execution logs for debugging and monitoring"""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='agent_executions')
    
    # Agent details
    agent_type = models.CharField(max_length=100, db_index=True)
    agent_name = models.CharField(max_length=100)
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running', db_index=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True)
    
    # Execution data
    steps_count = models.IntegerField(default=0)
    tools_used = models.JSONField(default=list, blank=True)
    
    # Results
    output = models.TextField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    
    # Errors
    errors = models.JSONField(default=list, blank=True)
    
    # Metadata (execution trace, tool calls, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['query', '-start_time']),
            models.Index(fields=['agent_type', '-start_time']),
        ]
    
    def __str__(self):
        return f"{self.agent_type} - {self.status}"


class GraphEntity(TimeStampedModel):
    """Knowledge graph entities"""
    
    ENTITY_TYPES = [
        ('PERSON', 'Person'),
        ('ORGANIZATION', 'Organization'),
        ('LOCATION', 'Location'),
        ('CONCEPT', 'Concept'),
        ('TECHNOLOGY', 'Technology'),
        ('EVENT', 'Event'),
        ('PRODUCT', 'Product'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=500, db_index=True)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES, db_index=True)
    description = models.TextField(null=True, blank=True)
    
    # Properties
    properties = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name_plural = 'Graph Entities'
        indexes = [
            models.Index(fields=['name', 'entity_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class GraphRelationship(TimeStampedModel):
    """Knowledge graph relationships"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    source = models.ForeignKey(GraphEntity, on_delete=models.CASCADE, related_name='outgoing_relations')
    target = models.ForeignKey(GraphEntity, on_delete=models.CASCADE, related_name='incoming_relations')
    
    relation_type = models.CharField(max_length=100, db_index=True)
    weight = models.FloatField(default=1.0)
    
    # Properties
    properties = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['source', 'relation_type']),
            models.Index(fields=['target', 'relation_type']),
        ]
    
    def __str__(self):
        return f"{self.source.name} --[{self.relation_type}]--> {self.target.name}"


class AgentMemory(TimeStampedModel):
    """Long-term memory for agents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='memories')
    
    memory_type = models.CharField(max_length=50, db_index=True)  # 'fact', 'preference', 'context'
    content = models.TextField()
    
    # Relevance and importance
    importance_score = models.FloatField(default=0.5)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name_plural = 'Agent Memories'
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['session', '-last_accessed']),
            models.Index(fields=['memory_type', '-last_accessed']),
        ]
    
    def __str__(self):
        return f"{self.memory_type}: {self.content[:50]}..."


class ToolExecution(TimeStampedModel):
    """Tool execution logs for agent tools"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_execution = models.ForeignKey(AgentExecution, on_delete=models.CASCADE, related_name='tool_executions')
    
    tool_name = models.CharField(max_length=100, db_index=True)
    tool_input = models.JSONField(default=dict)
    tool_output = models.JSONField(null=True, blank=True)
    
    execution_time = models.FloatField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['agent_execution', 'created_at']),
            models.Index(fields=['tool_name', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.tool_name} - {'✓' if self.success else '✗'}"


# RL Models

class RLExperienceRecord(models.Model):
    """
    Stores every (state, action, reward, next_state, done) tuple
    produced during a query.

    Enables:
        • Offline replay training
        • Deferred user-feedback reward updates
        • Analytics / performance monitoring
    """

    ACTION_CHOICES = [
        ("RETRIEVE_MORE",      "Retrieve More"),
        ("RE_RANK",            "Re-Rank"),
        ("ANSWER_NOW",         "Answer Now"),
        ("ASK_CLARIFICATION",  "Ask Clarification"),
    ]

    FEEDBACK_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("none",     "None"),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link back to the Query that generated this experience
    query_id      = models.CharField(max_length=100, db_index=True)

    # RL tuple
    rl_state      = models.JSONField(help_text="[conf_bucket, retr_bucket, comp_bucket, has_internet]")
    action_idx    = models.IntegerField()
    action_name   = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    reward        = models.FloatField()
    next_rl_state = models.JSONField()
    done          = models.BooleanField(default=False, db_index=True)

    # Deferred feedback
    user_feedback = models.CharField(
        max_length=10, choices=FEEDBACK_CHOICES, default="none", db_index=True
    )

    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["query_id", "created_at"]),
            models.Index(fields=["action_name", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action_name} | reward={self.reward:+.3f} | done={self.done}"


class RLEpisodeSummary(models.Model):
    """
    Aggregated per-query RL statistics.
    One row per query — written by the coordinator after the full pipeline.

    Useful for:
        • Monitoring convergence (is ε decreasing? are rewards improving?)
        • Identifying queries that required many steps
        • A/B comparison before/after RL deployment
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_id        = models.CharField(max_length=100, unique=True, db_index=True)

    total_steps     = models.IntegerField(default=0)
    total_reward    = models.FloatField(default=0.0)
    final_confidence = models.FloatField(null=True, blank=True)
    epsilon_at_end  = models.FloatField(null=True, blank=True)

    # Which actions were taken (list of action names)
    actions_taken   = models.JSONField(default=list)

    # Was this query resolved from RAG only, or needed internet?
    used_internet   = models.BooleanField(default=False)

    # Did the user provide feedback?
    user_feedback   = models.CharField(max_length=10, default="none")

    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return (
            f"Episode {self.query_id[:8]}… | "
            f"steps={self.total_steps} | reward={self.total_reward:+.3f}"
        )