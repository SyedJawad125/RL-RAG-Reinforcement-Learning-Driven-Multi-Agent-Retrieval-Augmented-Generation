# """
# URL Configuration for RAG API + Document Processor
# """
# from django.urls import path
# from apps.rag import views

# app_name = 'rag'

# urlpatterns = [
#     # Query endpoints
#     path('v1/query/', views.query_rag, name='query'),
    
#     # Document management
#     path('v1/upload/', views.upload_document, name='upload'),
#     path('documents/', views.list_documents, name='documents-list'),
#     path('documents/<uuid:document_id>/', views.get_document, name='document-detail'),
#     path('documents/<uuid:document_id>/delete/', views.delete_document, name='document-delete'),
#     path('documents/clear/', views.clear_all_documents, name='documents-clear'),
    
#     # Session management
#     path('sessions/', views.create_session, name='session-create'),
#     path('sessions/<uuid:session_id>/', views.get_session, name='session-detail'),
    
#     # Query history
#     path('queries/', views.list_queries, name='queries-list'),
#     path('queries/<uuid:query_id>/execution/', views.get_query_execution, name='query-execution'),
    
#     # Health & monitoring
#     path('health/', views.health_check, name='health'),
#     path('stats/', views.get_stats, name='stats'),
#     path('agents/status/', views.agent_status, name='agent-status'),
# ]


"""
URL Configuration for RAG API
Following the pattern from your existing URLs
"""
from django.urls import path
from apps.rag import views

app_name = 'rag'


urlpatterns = [
    # Query endpoints
    path('v1/query/', views.query_rag, name='query'),
    
    # Document management
    path('v1/upload/', views.upload_document, name='upload'),
    path('v1/documents/', views.list_documents, name='documents-list'),
    path('v1/documents/<uuid:document_id>/', views.get_document, name='document-detail'),
    path('v1/documents/<uuid:document_id>/delete/', views.delete_document, name='document-delete'),
    path('v1/documents/clear/', views.clear_all_documents, name='documents-clear'),
    
    # Session management
    path('v1/sessions/', views.create_session, name='session-create'),
    path('v1/sessions/<uuid:session_id>/', views.get_session, name='session-detail'),
    
    # Query history
    path('v1/queries/', views.list_queries, name='queries-list'),
    path('v1/queries/<uuid:query_id>/execution/', views.get_query_execution, name='query-execution'),
    
    # Health & monitoring
    path('v1/health/', views.health_check, name='health'),
    path('v1/stats/', views.get_stats, name='stats'),
    path('v1/agents/status/', views.agent_status, name='agent-status'),
]


# urlpatterns = [
#     # Query endpoints
#     path('v1/query/', views.QueryView.as_view(), name='query'),
#     path('v1/query/<uuid:pk>/', views.QueryDetailView.as_view(), name='query-detail'),
#     path('v1/query/<uuid:query_id>/execution/', views.QueryExecutionView.as_view(), name='query-execution'),
    
#     # Document management
#     path('v1/document/', views.DocumentView.as_view(), name='document-list'),
#     path('v1/document/<uuid:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
#     path('v1/document/<uuid:document_id>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
#     path('v1/document/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
#     path('v1/document/clear/', views.DocumentClearView.as_view(), name='document-clear'),
    
#     # Document chunks
#     path('v1/document-chunk/', views.DocumentChunkView.as_view(), name='chunk-list'),
#     path('v1/document-chunk/<uuid:pk>/', views.DocumentChunkDetailView.as_view(), name='chunk-detail'),
    
#     # Session management
#     path('v1/session/', views.SessionView.as_view(), name='session-list'),
#     path('v1/session/<uuid:pk>/', views.SessionDetailView.as_view(), name='session-detail'),
#     path('v1/session/create/', views.SessionCreateView.as_view(), name='session-create'),
    
#     # Agent executions
#     path('v1/agent-execution/', views.AgentExecutionView.as_view(), name='agent-execution-list'),
#     path('v1/agent-execution/<uuid:pk>/', views.AgentExecutionDetailView.as_view(), name='agent-execution-detail'),
    
#     # Graph entities
#     path('v1/graph-entity/', views.GraphEntityView.as_view(), name='graph-entity-list'),
#     path('v1/graph-entity/<uuid:pk>/', views.GraphEntityDetailView.as_view(), name='graph-entity-detail'),
    
#     # Graph relationships
#     path('v1/graph-relationship/', views.GraphRelationshipView.as_view(), name='graph-relationship-list'),
#     path('v1/graph-relationship/<uuid:pk>/', views.GraphRelationshipDetailView.as_view(), name='graph-relationship-detail'),
    
#     # Agent memories
#     path('v1/agent-memory/', views.AgentMemoryView.as_view(), name='agent-memory-list'),
#     path('v1/agent-memory/<uuid:pk>/', views.AgentMemoryDetailView.as_view(), name='agent-memory-detail'),
    
#     # Tool executions
#     path('v1/tool-execution/', views.ToolExecutionView.as_view(), name='tool-execution-list'),
#     path('v1/tool-execution/<uuid:pk>/', views.ToolExecutionDetailView.as_view(), name='tool-execution-detail'),
    
#     # Health & monitoring
#     path('v1/health/', views.HealthCheckView.as_view(), name='health'),
#     path('v1/stats/', views.StatsView.as_view(), name='stats'),
#     path('v1/agent-status/', views.AgentStatusView.as_view(), name='agent-status'),
# ]
