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

    # POST  { "query_id": "...", "feedback": "positive"|"negative" }
    path("v1/rl/feedback/",             views.rl_feedback,     name="rl_feedback"),
 
    # GET   live Q-table stats + DB aggregates
    path("v1/rl/stats/",                views.rl_stats,        name="rl_stats"),
 
    # GET   per-query decision trace
    path("v1/rl/trace/<str:query_id>/", views.rl_query_trace,  name="rl_query_trace"),
 
    # POST  manual replay-training trigger  { "batch_size": 64 }
    path("v1/rl/train/",                views.rl_train,        name="rl_train"),
]


