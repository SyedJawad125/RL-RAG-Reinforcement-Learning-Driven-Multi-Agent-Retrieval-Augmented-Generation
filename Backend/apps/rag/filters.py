"""
Django Filters for Multi-Agent RAG System
Comprehensive filtering for all models
"""
import django_filters
from django_filters import (
    FilterSet, CharFilter, BooleanFilter, NumberFilter, 
    DateTimeFilter, ChoiceFilter, UUIDFilter, BaseInFilter,
    DateFilter, TimeFilter
)
from .models import (
    Document, DocumentChunk, Session, Query, AgentExecution,
    GraphEntity, GraphRelationship, AgentMemory, ToolExecution
)


class NumberInFilter(BaseInFilter, NumberFilter):
    """Filter for list of numbers (e.g., ?ids=1,2,3)"""
    pass


class UUIDInFilter(BaseInFilter, UUIDFilter):
    """Filter for list of UUIDs (e.g., ?ids=uuid1,uuid2)"""
    pass


class DocumentFilter(FilterSet):
    """Filter for Document model"""
    
    # Basic filters
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    filename = CharFilter(field_name='filename', lookup_expr='icontains')
    content_type = CharFilter(field_name='content_type', lookup_expr='icontains')
    content_types = BaseInFilter(field_name='content_type', lookup_expr='in')
    
    # Status filters
    status = ChoiceFilter(field_name='status', choices=Document.STATUS_CHOICES)
    status_in = BaseInFilter(field_name='status', lookup_expr='in')
    
    # Count filters
    chunks_count_min = NumberFilter(field_name='chunks_count', lookup_expr='gte')
    chunks_count_max = NumberFilter(field_name='chunks_count', lookup_expr='lte')
    entities_count_min = NumberFilter(field_name='entities_count', lookup_expr='gte')
    entities_count_max = NumberFilter(field_name='entities_count', lookup_expr='lte')
    relationships_count_min = NumberFilter(field_name='relationships_count', lookup_expr='gte')
    relationships_count_max = NumberFilter(field_name='relationships_count', lookup_expr='lte')
    
    # Size filters
    size_min = NumberFilter(field_name='size', lookup_expr='gte')
    size_max = NumberFilter(field_name='size', lookup_expr='lte')
    
    # Date filters
    uploaded_at = DateTimeFilter(field_name='uploaded_at')
    uploaded_after = DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_before = DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')
    uploaded_date = DateFilter(field_name='uploaded_at', lookup_expr='date')
    
    processed_at = DateTimeFilter(field_name='processed_at')
    processed_after = DateTimeFilter(field_name='processed_at', lookup_expr='gte')
    processed_before = DateTimeFilter(field_name='processed_at', lookup_expr='lte')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Processing time filters
    processing_time_min = NumberFilter(field_name='processing_time', lookup_expr='gte')
    processing_time_max = NumberFilter(field_name='processing_time', lookup_expr='lte')
    
    # Metadata filters
    has_metadata = BooleanFilter(field_name='metadata', method='filter_has_metadata')
    
    def filter_has_metadata(self, queryset, name, value):
        if value:
            return queryset.exclude(metadata={})
        return queryset.filter(metadata={})
    
    class Meta:
        model = Document
        fields = []


class DocumentChunkFilter(FilterSet):
    """Filter for DocumentChunk model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    document_id = UUIDFilter(field_name='document__id')
    document_ids = UUIDInFilter(field_name='document__id', lookup_expr='in')
    document_filename = CharFilter(field_name='document__filename', lookup_expr='icontains')
    
    content = CharFilter(field_name='content', lookup_expr='icontains')
    chunk_index = NumberFilter(field_name='chunk_index')
    chunk_index_min = NumberFilter(field_name='chunk_index', lookup_expr='gte')
    chunk_index_max = NumberFilter(field_name='chunk_index', lookup_expr='lte')
    
    has_embedding = BooleanFilter(field_name='embedding', method='filter_has_embedding')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    def filter_has_embedding(self, queryset, name, value):
        if value:
            return queryset.exclude(embedding__isnull=True)
        return queryset.filter(embedding__isnull=True)
    
    class Meta:
        model = DocumentChunk
        fields = []


class SessionFilter(FilterSet):
    """Filter for Session model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    user_id = CharFilter(field_name='user_id', lookup_expr='icontains')
    user_ids = BaseInFilter(field_name='user_id', lookup_expr='in')
    
    started_at = DateTimeFilter(field_name='started_at')
    started_after = DateTimeFilter(field_name='started_at', lookup_expr='gte')
    started_before = DateTimeFilter(field_name='started_at', lookup_expr='lte')
    started_date = DateFilter(field_name='started_at', lookup_expr='date')
    
    last_activity = DateTimeFilter(field_name='last_activity')
    last_activity_after = DateTimeFilter(field_name='last_activity', lookup_expr='gte')
    last_activity_before = DateTimeFilter(field_name='last_activity', lookup_expr='lte')
    
    message_count_min = NumberFilter(field_name='message_count', lookup_expr='gte')
    message_count_max = NumberFilter(field_name='message_count', lookup_expr='lte')
    
    is_active = BooleanFilter(field_name='is_active')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = Session
        fields = []


class QueryFilter(FilterSet):
    """Filter for Query model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    session_id = UUIDFilter(field_name='session__id')
    session_ids = UUIDInFilter(field_name='session__id', lookup_expr='in')
    session_user_id = CharFilter(field_name='session__user_id', lookup_expr='icontains')
    
    document_id = UUIDFilter(field_name='document__id')
    document_ids = UUIDInFilter(field_name='document__id', lookup_expr='in')
    document_filename = CharFilter(field_name='document__filename', lookup_expr='icontains')
    
    query_text = CharFilter(field_name='query_text', lookup_expr='icontains')
    answer = CharFilter(field_name='answer', lookup_expr='icontains')
    
    strategy_used = ChoiceFilter(field_name='strategy_used', choices=Query.STRATEGY_CHOICES)
    strategies_used = BaseInFilter(field_name='strategy_used', lookup_expr='in')
    
    query_type = ChoiceFilter(field_name='query_type', choices=Query.QUERY_TYPE_CHOICES)
    query_types = BaseInFilter(field_name='query_type', lookup_expr='in')
    
    processing_time_min = NumberFilter(field_name='processing_time', lookup_expr='gte')
    processing_time_max = NumberFilter(field_name='processing_time', lookup_expr='lte')
    
    confidence_score_min = NumberFilter(field_name='confidence_score', lookup_expr='gte')
    confidence_score_max = NumberFilter(field_name='confidence_score', lookup_expr='lte')
    
    retrieved_chunks_count_min = NumberFilter(field_name='retrieved_chunks_count', lookup_expr='gte')
    retrieved_chunks_count_max = NumberFilter(field_name='retrieved_chunks_count', lookup_expr='lte')
    
    agent_steps_count_min = NumberFilter(field_name='agent_steps_count', lookup_expr='gte')
    agent_steps_count_max = NumberFilter(field_name='agent_steps_count', lookup_expr='lte')
    
    agent_used = CharFilter(field_name='agents_used', method='filter_agent_used')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_date = DateFilter(field_name='created_at', lookup_expr='date')
    
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    def filter_agent_used(self, queryset, name, value):
        """Filter by agent name in agents_used JSON array"""
        return queryset.filter(agents_used__contains=[value])
    
    class Meta:
        model = Query
        fields = []


class AgentExecutionFilter(FilterSet):
    """Filter for AgentExecution model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    query_id = UUIDFilter(field_name='query__id')
    query_ids = UUIDInFilter(field_name='query__id', lookup_expr='in')
    query_text = CharFilter(field_name='query__query_text', lookup_expr='icontains')
    
    agent_type = CharFilter(field_name='agent_type', lookup_expr='icontains')
    agent_types = BaseInFilter(field_name='agent_type', lookup_expr='in')
    
    agent_name = CharFilter(field_name='agent_name', lookup_expr='icontains')
    agent_names = BaseInFilter(field_name='agent_name', lookup_expr='in')
    
    status = ChoiceFilter(field_name='status', choices=AgentExecution.STATUS_CHOICES)
    status_in = BaseInFilter(field_name='status', lookup_expr='in')
    
    start_time = DateTimeFilter(field_name='start_time')
    start_after = DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_before = DateTimeFilter(field_name='start_time', lookup_expr='lte')
    start_date = DateFilter(field_name='start_time', lookup_expr='date')
    
    end_time = DateTimeFilter(field_name='end_time')
    end_after = DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_before = DateTimeFilter(field_name='end_time', lookup_expr='lte')
    
    execution_time_min = NumberFilter(field_name='execution_time', lookup_expr='gte')
    execution_time_max = NumberFilter(field_name='execution_time', lookup_expr='lte')
    
    steps_count_min = NumberFilter(field_name='steps_count', lookup_expr='gte')
    steps_count_max = NumberFilter(field_name='steps_count', lookup_expr='lte')
    
    tool_used = CharFilter(field_name='tools_used', method='filter_tool_used')
    
    confidence_min = NumberFilter(field_name='confidence', lookup_expr='gte')
    confidence_max = NumberFilter(field_name='confidence', lookup_expr='lte')
    
    has_errors = BooleanFilter(field_name='errors', method='filter_has_errors')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    def filter_tool_used(self, queryset, name, value):
        """Filter by tool name in tools_used JSON array"""
        return queryset.filter(tools_used__contains=[value])
    
    def filter_has_errors(self, queryset, name, value):
        if value:
            return queryset.exclude(errors=[])
        return queryset.filter(errors=[])
    
    class Meta:
        model = AgentExecution
        fields = []


class GraphEntityFilter(FilterSet):
    """Filter for GraphEntity model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    name = CharFilter(field_name='name', lookup_expr='icontains')
    name_exact = CharFilter(field_name='name', lookup_expr='iexact')
    
    entity_type = ChoiceFilter(field_name='entity_type', choices=GraphEntity.ENTITY_TYPES)
    entity_types = BaseInFilter(field_name='entity_type', lookup_expr='in')
    
    description = CharFilter(field_name='description', lookup_expr='icontains')
    
    property_key = CharFilter(field_name='properties', method='filter_property_key')
    property_value = CharFilter(field_name='properties', method='filter_property_value')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    def filter_property_key(self, queryset, name, value):
        """Filter entities that have a specific property key"""
        return queryset.filter(properties__has_key=value)
    
    def filter_property_value(self, queryset, name, value):
        """Filter entities that have a property with specific value (key=value format)"""
        if '=' in value:
            key, val = value.split('=', 1)
            return queryset.filter(properties__contains={key: val})
        return queryset
    
    class Meta:
        model = GraphEntity
        fields = []


class GraphRelationshipFilter(FilterSet):
    """Filter for GraphRelationship model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    source_id = UUIDFilter(field_name='source__id')
    source_ids = UUIDInFilter(field_name='source__id', lookup_expr='in')
    source_name = CharFilter(field_name='source__name', lookup_expr='icontains')
    source_type = ChoiceFilter(field_name='source__entity_type', choices=GraphEntity.ENTITY_TYPES)
    
    target_id = UUIDFilter(field_name='target__id')
    target_ids = UUIDInFilter(field_name='target__id', lookup_expr='in')
    target_name = CharFilter(field_name='target__name', lookup_expr='icontains')
    target_type = ChoiceFilter(field_name='target__entity_type', choices=GraphEntity.ENTITY_TYPES)
    
    relation_type = CharFilter(field_name='relation_type', lookup_expr='icontains')
    relation_types = BaseInFilter(field_name='relation_type', lookup_expr='in')
    
    weight_min = NumberFilter(field_name='weight', lookup_expr='gte')
    weight_max = NumberFilter(field_name='weight', lookup_expr='lte')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = GraphRelationship
        fields = []


class AgentMemoryFilter(FilterSet):
    """Filter for AgentMemory model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    session_id = UUIDFilter(field_name='session__id')
    session_ids = UUIDInFilter(field_name='session__id', lookup_expr='in')
    session_user_id = CharFilter(field_name='session__user_id', lookup_expr='icontains')
    
    memory_type = CharFilter(field_name='memory_type', lookup_expr='icontains')
    memory_types = BaseInFilter(field_name='memory_type', lookup_expr='in')
    
    content = CharFilter(field_name='content', lookup_expr='icontains')
    
    importance_score_min = NumberFilter(field_name='importance_score', lookup_expr='gte')
    importance_score_max = NumberFilter(field_name='importance_score', lookup_expr='lte')
    
    last_accessed = DateTimeFilter(field_name='last_accessed')
    last_accessed_after = DateTimeFilter(field_name='last_accessed', lookup_expr='gte')
    last_accessed_before = DateTimeFilter(field_name='last_accessed', lookup_expr='lte')
    
    access_count_min = NumberFilter(field_name='access_count', lookup_expr='gte')
    access_count_max = NumberFilter(field_name='access_count', lookup_expr='lte')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = AgentMemory
        fields = []


class ToolExecutionFilter(FilterSet):
    """Filter for ToolExecution model"""
    
    id = UUIDFilter(field_name='id')
    ids = UUIDInFilter(field_name='id', lookup_expr='in')
    
    agent_execution_id = UUIDFilter(field_name='agent_execution__id')
    agent_execution_ids = UUIDInFilter(field_name='agent_execution__id', lookup_expr='in')
    agent_type = CharFilter(field_name='agent_execution__agent_type', lookup_expr='icontains')
    
    tool_name = CharFilter(field_name='tool_name', lookup_expr='icontains')
    tool_names = BaseInFilter(field_name='tool_name', lookup_expr='in')
    
    execution_time_min = NumberFilter(field_name='execution_time', lookup_expr='gte')
    execution_time_max = NumberFilter(field_name='execution_time', lookup_expr='lte')
    
    success = BooleanFilter(field_name='success')
    
    has_error = BooleanFilter(field_name='error_message', method='filter_has_error')
    
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_date = DateFilter(field_name='created_at', lookup_expr='date')
    
    def filter_has_error(self, queryset, name, value):
        if value:
            return queryset.exclude(error_message__isnull=True).exclude(error_message='')
        return queryset.filter(error_message__isnull=True)
    
    class Meta:
        model = ToolExecution
        fields = []