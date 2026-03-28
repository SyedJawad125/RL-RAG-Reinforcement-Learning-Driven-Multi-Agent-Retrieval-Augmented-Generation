"""
Django REST Framework Serializers for RAG System
"""
from rest_framework import serializers
from apps.rag.models import (
    Document,
    DocumentChunk,
    Query,
    Session,
    AgentExecution,
    GraphEntity,
    GraphRelationship
)


# ============================================
# Document Serializers
# ============================================

class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    file = serializers.FileField()
    metadata = serializers.JSONField(required=False, default=dict)


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'content_type', 'size', 'status',
            'chunks_count', 'entities_count', 'relationships_count',
            'uploaded_at', 'processed_at', 'processing_time', 'metadata'
        ]
        read_only_fields = ['id', 'uploaded_at', 'processed_at']


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document listing"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'content_type', 'size', 'status',
            'chunks_count', 'uploaded_at'
        ]


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model"""
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'document', 'content', 'chunk_index',
            'metadata', 'created_at'
        ]


# ============================================
# Query Serializers
# ============================================

class QueryRequestSerializer(serializers.Serializer):
    """Serializer for query request"""
    query = serializers.CharField(max_length=2000)
    strategy = serializers.ChoiceField(
        choices=['simple', 'agentic', 'multi_agent', 'auto'],
        default='auto'
    )
    top_k = serializers.IntegerField(min_value=1, max_value=20, default=5)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    document_id = serializers.UUIDField(required=False, allow_null=True)


class RetrievedChunkSerializer(serializers.Serializer):
    """Serializer for retrieved chunks"""
    content = serializers.CharField()
    score = serializers.FloatField()
    metadata = serializers.JSONField()


class InternetSourceSerializer(serializers.Serializer):
    """Serializer for internet search sources"""
    title = serializers.CharField()
    url = serializers.URLField()
    snippet = serializers.CharField()
    source = serializers.CharField()
    score = serializers.FloatField(required=False)


class ExecutionStepSerializer(serializers.Serializer):
    """Serializer for agent execution steps"""
    step_number = serializers.IntegerField()
    type = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.CharField()
    metadata = serializers.JSONField(default=dict)


class QueryResponseSerializer(serializers.Serializer):
    """Serializer for query response"""
    query = serializers.CharField()
    answer = serializers.CharField()
    strategy_used = serializers.CharField()
    processing_time = serializers.FloatField()
    retrieved_chunks = RetrievedChunkSerializer(many=True, required=False)
    confidence_score = serializers.FloatField()
    
    # Multi-agent specific fields
    source = serializers.CharField(required=False)
    agent_type = serializers.CharField(required=False)
    execution_steps = ExecutionStepSerializer(many=True, required=False)
    internet_sources = InternetSourceSerializer(many=True, required=False)
    query_type = serializers.CharField(required=False)


class QueryHistorySerializer(serializers.ModelSerializer):
    """Serializer for query history"""
    
    class Meta:
        model = Query
        fields = [
            'id', 'query_text', 'answer', 'strategy_used',
            'processing_time', 'confidence_score', 'created_at',
            'agent_steps_count', 'agents_used'
        ]


# ============================================
# Session Serializers
# ============================================

class SessionCreateSerializer(serializers.Serializer):
    """Serializer for session creation"""
    user_id = serializers.CharField(max_length=255, required=False, allow_null=True)


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model"""
    queries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'user_id', 'started_at', 'last_activity',
            'message_count', 'is_active', 'queries_count', 'metadata'
        ]
    
    def get_queries_count(self, obj):
        return obj.queries.count()


# ============================================
# Agent Execution Serializers
# ============================================

class AgentExecutionSerializer(serializers.ModelSerializer):
    """Serializer for AgentExecution model"""
    
    class Meta:
        model = AgentExecution
        fields = [
            'id', 'query', 'agent_type', 'agent_name', 'status',
            'start_time', 'end_time', 'execution_time', 'steps_count',
            'tools_used', 'output', 'confidence', 'errors', 'metadata'
        ]


class AgentExecutionSummarySerializer(serializers.Serializer):
    """Serializer for agent execution summary"""
    agent_type = serializers.CharField()
    agent_name = serializers.CharField()
    total_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    average_time = serializers.FloatField()
    tools_used = serializers.ListField(child=serializers.CharField())


# ============================================
# Graph Serializers
# ============================================

class GraphEntitySerializer(serializers.ModelSerializer):
    """Serializer for GraphEntity model"""
    
    class Meta:
        model = GraphEntity
        fields = [
            'id', 'name', 'entity_type', 'description',
            'properties', 'created_at', 'updated_at'
        ]


class GraphRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for GraphRelationship model"""
    source_name = serializers.CharField(source='source.name', read_only=True)
    target_name = serializers.CharField(source='target.name', read_only=True)
    
    class Meta:
        model = GraphRelationship
        fields = [
            'id', 'source', 'target', 'source_name', 'target_name',
            'relation_type', 'weight', 'properties', 'created_at'
        ]


# ============================================
# Health & Stats Serializers
# ============================================

class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response"""
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    components = serializers.DictField()


class SystemStatsSerializer(serializers.Serializer):
    """Serializer for system statistics"""
    total_documents = serializers.IntegerField()
    total_queries = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    strategy_distribution = serializers.DictField()
    source_distribution = serializers.DictField(required=False)
    agent_usage = serializers.DictField(required=False)