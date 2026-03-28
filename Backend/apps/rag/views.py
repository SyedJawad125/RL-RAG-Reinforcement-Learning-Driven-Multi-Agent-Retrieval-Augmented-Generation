# """
# Django Views for Multi-Agent RAG System
# Complete REST API implementation
# """
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.utils import timezone
# from django.db.models import Avg, Count
# import logging
# import time
# import uuid
# import asyncio

# from apps.rag.models import Document, Query, Session, AgentExecution
# from apps.rag.serializers import *
# from apps.rag.services.core_services import (
#     get_llm_service,
#     get_embedding_service,
#     get_vector_store
# )
# from apps.rag.services.agents.coordinator import MultiAgentCoordinator
# from apps.rag.services.document_processor import DocumentProcessor

# logger = logging.getLogger(__name__)

# # Initialize coordinator (singleton)
# _coordinator = None

# def get_coordinator():
#     """Get or create coordinator instance"""
#     global _coordinator
#     if _coordinator is None:
#         try:
#             # Initialize Tavily client if API key available
#             from django.conf import settings
#             tavily_client = None
#             if hasattr(settings, 'TAVILY_API_KEY') and settings.TAVILY_API_KEY:
#                 try:
#                     from tavily import TavilyClient
#                     tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
#                 except ImportError:
#                     logger.warning("Tavily package not installed")
            
#             _coordinator = MultiAgentCoordinator(
#                 llm_service=get_llm_service(),
#                 vector_store=get_vector_store(),
#                 embedding_service=get_embedding_service(),
#                 tavily_client=tavily_client
#             )
#         except Exception as e:
#             logger.error(f"Failed to initialize coordinator: {e}")
#             raise
#     return _coordinator


# # ============================================
# # Query API
# # ============================================

# @api_view(['POST'])
# def query_rag(request):
#     """
#     Main RAG query endpoint with multi-agent support.
    
#     POST /api/rag/v1/query/
#     """
#     serializer = QueryRequestSerializer(data=request.data)
    
#     if not serializer.is_valid():
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     data = serializer.validated_data
#     query_text = data['query']
#     strategy = data['strategy']
#     top_k = data['top_k']
#     session_id = data.get('session_id')
#     document_id = data.get('document_id')
    
#     start_time = time.time()
    
#     try:
#         logger.info(f"[Query] Received: {query_text[:50]}... (strategy: {strategy})")
        
#         # Get coordinator
#         coordinator = get_coordinator()
        
#         # Prepare context
#         context = {
#             'top_k': top_k,
#             'session_id': session_id,
#             'document_id': str(document_id) if document_id else None,
#             'strategy': strategy
#         }
        
#         # Execute query (async)
#         result = asyncio.run(coordinator.execute(query_text, context))
        
#         processing_time = time.time() - start_time
        
#         # Save to database
#         query_record = Query.objects.create(
#             id=uuid.uuid4(),
#             query_text=query_text,
#             answer=result['answer'],
#             strategy_used=strategy,
#             processing_time=processing_time,
#             confidence_score=result.get('confidence', 0.7),
#             retrieved_chunks_count=len(result.get('retrieved_chunks', [])),
#             agent_steps_count=len(result.get('execution_steps', [])),
#             session_id=session_id,
#             document_id=document_id,
#             agents_used=result.get('agents_used', []),
#             metadata={
#                 'execution_steps': result.get('execution_steps', []),
#                 'internet_sources': result.get('internet_sources', {}),
#                 'source': result.get('source'),
#                 'agent_type': result.get('agent_type'),
#                 'query_type': result.get('query_type')
#             }
#         )
        
#         # Update session
#         if session_id:
#             try:
#                 session = Session.objects.get(id=session_id)
#                 session.message_count += 1
#                 session.last_activity = timezone.now()
#                 session.save()
#             except Session.DoesNotExist:
#                 pass
        
#         # Prepare response
#         response_data = {
#             'query': query_text,
#             'answer': result['answer'],
#             'strategy_used': strategy,
#             'processing_time': processing_time,
#             'retrieved_chunks': result.get('retrieved_chunks', []),
#             'confidence_score': result.get('confidence', 0.7),
#             'source': result.get('source'),
#             'agent_type': result.get('agent_type'),
#             'execution_steps': result.get('execution_steps', []),
#             'internet_sources': result.get('internet_sources', {}),
#             'query_type': result.get('query_type')
#         }
        
#         logger.info(f"[Query] Completed in {processing_time:.2f}s")
        
#         return Response(response_data, status=status.HTTP_200_OK)
        
#     except Exception as e:
#         logger.error(f"[Query] Failed: {e}", exc_info=True)
#         return Response(
#             {'error': f'Query processing failed: {str(e)}'},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# # ============================================
# # Document Management
# # ============================================

# # @api_view(['POST'])
# # def upload_document(request):
# #     """
# #     Upload and process document.
    
# #     POST /api/rag/v1/upload/
# #     """
# #     if 'file' not in request.FILES:
# #         return Response(
# #             {'error': 'No file provided'},
# #             status=status.HTTP_400_BAD_REQUEST
# #         )
    
# #     file = request.FILES['file']
# #     metadata = request.data.get('metadata', {})
    
# #     start_time = time.time()
    
# #     try:
# #         logger.info(f"[Upload] Processing: {file.name}")
        
# #         # Create document record
# #         document = Document.objects.create(
# #             id=uuid.uuid4(),
# #             filename=file.name,
# #             content_type=file.content_type or 'application/octet-stream',
# #             size=file.size,
# #             status='processing',
# #             metadata=metadata if isinstance(metadata, dict) else {}
# #         )
        
# #         # Process document
# #         processor = DocumentProcessor(
# #             vector_store=get_vector_store(),
# #             embedding_service=get_embedding_service()
# #         )
        
# #         result = asyncio.run(processor.process_document(
# #             file=file,
# #             document_id=str(document.id)
# #         ))
        
# #         # Update document
# #         document.status = 'completed'
# #         document.chunks_count = result['chunks_created']
# #         document.processed_at = timezone.now()
# #         document.processing_time = time.time() - start_time
# #         document.save()
        
# #         logger.info(f"[Upload] Completed: {result['chunks_created']} chunks")
        
# #         return Response({
# #             'document_id': str(document.id),
# #             'filename': document.filename,
# #             'status': 'success',
# #             'chunks_created': result['chunks_created'],
# #             'processing_time': f"{document.processing_time:.1f} seconds",
# #             'message': f"Document '{file.name}' processed successfully"
# #         }, status=status.HTTP_201_CREATED)
        
# #     except Exception as e:
# #         logger.error(f"[Upload] Failed: {e}", exc_info=True)
# #         if 'document' in locals():
# #             document.status = 'failed'
# #             document.save()
# #         return Response(
# #             {'error': f'Document upload failed: {str(e)}'},
# #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #         )


# # ============================================================
# # Replace your upload_document view in views.py with this
# # ============================================================

# @api_view(['POST'])
# def upload_document(request):
#     """
#     Upload and process document.
#     POST /api/rag/v1/upload/
#     """
#     if 'file' not in request.FILES:
#         return Response(
#             {'error': 'No file provided'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     file = request.FILES['file']
#     metadata = request.data.get('metadata', {})

#     # ── Validate file extension ──
#     allowed = ['.pdf', '.txt', '.docx', '.csv']
#     filename_lc = file.name.lower()
#     if not any(filename_lc.endswith(ext) for ext in allowed):
#         return Response(
#             {'error': f'Unsupported file type. Allowed: {", ".join(allowed)}'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     start_time = time.time()

#     try:
#         logger.info(f"[Upload] Processing: {file.name} ({file.size} bytes)")

#         # Create document record with 'processing' status
#         document = Document.objects.create(
#             id=uuid.uuid4(),
#             filename=file.name,
#             content_type=file.content_type or 'application/octet-stream',
#             size=file.size,
#             status='processing',
#             metadata=metadata if isinstance(metadata, dict) else {}
#         )

#         # Process document
#         processor = DocumentProcessor(
#             vector_store=get_vector_store(),
#             embedding_service=get_embedding_service()
#         )

#         result = asyncio.run(processor.process_document(
#             file=file,
#             document_id=str(document.id)
#         ))

#         chunks_created = result.get('chunks_created', 0)

#         # ── CRITICAL CHECK: warn if no chunks were created ──
#         if chunks_created == 0:
#             document.status = 'failed'
#             document.chunks_count = 0
#             document.processed_at = timezone.now()
#             document.processing_time = time.time() - start_time
#             document.metadata = {
#                 **document.metadata,
#                 'error': 'No text could be extracted. The PDF may be image/scan-based. Try a text-based PDF or convert to TXT.'
#             }
#             document.save()

#             return Response(
#                 {
#                     'error': (
#                         f"Document '{file.name}' was uploaded but no text could be extracted. "
#                         "Possible reasons:\n"
#                         "1. The PDF is image/scan-based (not text-based)\n"
#                         "2. The file is empty or corrupted\n"
#                         "3. The file format is not readable\n\n"
#                         "Solutions:\n"
#                         "- Copy-paste the CV content into a .txt file and upload that\n"
#                         "- Use an online PDF-to-text converter first\n"
#                         "- Make sure the PDF was created from a Word document (not scanned)"
#                     )
#                 },
#                 status=status.HTTP_422_UNPROCESSABLE_ENTITY
#             )

#         # ── Success ──
#         document.status = 'completed'
#         document.chunks_count = chunks_created
#         document.processed_at = timezone.now()
#         document.processing_time = time.time() - start_time
#         document.save()

#         logger.info(f"[Upload] Done: {chunks_created} chunks from '{file.name}'")

#         return Response({
#             'document_id': str(document.id),
#             'filename': document.filename,
#             'status': 'success',
#             'chunks_created': chunks_created,
#             'processing_time': f"{document.processing_time:.1f} seconds",
#             'message': f"Document '{file.name}' processed successfully with {chunks_created} chunks"
#         }, status=status.HTTP_201_CREATED)

#     except Exception as e:
#         logger.error(f"[Upload] Failed: {e}", exc_info=True)
#         if 'document' in locals():
#             document.status = 'failed'
#             document.metadata = {**document.metadata, 'error': str(e)}
#             document.save()
#         return Response(
#             {'error': f'Document upload failed: {str(e)}'},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# @api_view(['GET'])
# def list_documents(request):
#     """List all documents"""
#     documents = Document.objects.all().order_by('-uploaded_at')
#     serializer = DocumentListSerializer(documents, many=True)
    
#     return Response({
#         'total': documents.count(),
#         'documents': serializer.data
#     })


# @api_view(['GET'])
# def get_document(request, document_id):
#     """Get single document"""
#     try:
#         document = Document.objects.get(id=document_id)
#         serializer = DocumentSerializer(document)
#         return Response(serializer.data)
#     except Document.DoesNotExist:
#         return Response(
#             {'error': 'Document not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )


# @api_view(['DELETE'])
# def delete_document(request, document_id):
#     """Delete document"""
#     try:
#         document = Document.objects.get(id=document_id)
#         filename = document.filename
        
#         # Delete from vector store
#         vector_store = get_vector_store()
#         try:
#             vector_store.delete_by_document_id(str(document_id))
#         except Exception as e:
#             logger.warning(f"Failed to delete from vector store: {e}")
        
#         # Delete from database
#         document.delete()
        
#         return Response({
#             'status': 'success',
#             'message': f"Document '{filename}' deleted successfully"
#         })
#     except Document.DoesNotExist:
#         return Response(
#             {'error': 'Document not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )


# @api_view(['DELETE'])
# def clear_all_documents(request):
#     """Clear all documents (DANGEROUS)"""
#     try:
#         # Clear vector store
#         vector_store = get_vector_store()
#         vector_store.reset_collection()
        
#         # Delete all documents
#         doc_count = Document.objects.count()
#         Query.objects.all().delete()
#         Document.objects.all().delete()
        
#         return Response({
#             'status': 'success',
#             'message': f'Cleared {doc_count} documents'
#         })
#     except Exception as e:
#         return Response(
#             {'error': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# # ============================================
# # Session Management
# # ============================================

# @api_view(['POST'])
# def create_session(request):
#     """Create new session"""
#     user_id = request.data.get('user_id')
    
#     session = Session.objects.create(
#         id=uuid.uuid4(),
#         user_id=user_id
#     )
    
#     response_serializer = SessionSerializer(session)
#     return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# @api_view(['GET'])
# def get_session(request, session_id):
#     """Get session details"""
#     try:
#         session = Session.objects.get(id=session_id)
#         serializer = SessionSerializer(session)
        
#         # Include queries
#         queries = Query.objects.filter(session=session).order_by('created_at')
#         queries_data = QueryHistorySerializer(queries, many=True).data
        
#         response_data = serializer.data
#         response_data['queries'] = queries_data
        
#         return Response(response_data)
#     except Session.DoesNotExist:
#         return Response(
#             {'error': 'Session not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )


# # ============================================
# # Health & Stats
# # ============================================

# @api_view(['GET'])
# def health_check(request):
#     """Health check endpoint"""
#     components = {
#         'database': 'unknown',
#         'llm_service': 'unknown',
#         'embedding_service': 'unknown',
#         'vector_store': 'unknown',
#         'coordinator': 'unknown'
#     }
    
#     all_healthy = True
    
#     # Check database
#     try:
#         Document.objects.count()
#         components['database'] = 'operational'
#     except:
#         components['database'] = 'error'
#         all_healthy = False
    
#     # Check services
#     try:
#         get_llm_service()
#         components['llm_service'] = 'operational'
#     except:
#         components['llm_service'] = 'error'
#         all_healthy = False
    
#     try:
#         get_embedding_service()
#         components['embedding_service'] = 'operational'
#     except:
#         components['embedding_service'] = 'error'
#         all_healthy = False
    
#     try:
#         vs = get_vector_store()
#         vs.get_count()
#         components['vector_store'] = 'operational'
#     except:
#         components['vector_store'] = 'error'
#         all_healthy = False
    
#     try:
#         get_coordinator()
#         components['coordinator'] = 'operational'
#     except:
#         components['coordinator'] = 'error'
#         all_healthy = False
    
#     return Response({
#         'status': 'healthy' if all_healthy else 'degraded',
#         'timestamp': timezone.now(),
#         'version': '1.0.0',
#         'components': components
#     })


# @api_view(['GET'])
# def get_stats(request):
#     """Get system statistics"""
#     stats = {
#         'total_documents': Document.objects.count(),
#         'total_queries': Query.objects.count(),
#         'total_chunks': get_vector_store().get_count(),
#         'average_processing_time': Query.objects.aggregate(
#             Avg('processing_time')
#         )['processing_time__avg'] or 0.0,
#         'strategy_distribution': dict(
#             Query.objects.values('strategy_used').annotate(
#                 count=Count('id')
#             ).values_list('strategy_used', 'count')
#         )
#     }
    
#     return Response(stats)


# @api_view(['GET'])
# def agent_status(request):
#     """Get agent status"""
#     try:
#         coordinator = get_coordinator()
#         status_data = coordinator.get_agent_status()
#         return Response(status_data)
#     except Exception as e:
#         return Response(
#             {'error': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# # ============================================
# # Query History & Debugging
# # ============================================

# @api_view(['GET'])
# def list_queries(request):
#     """List query history"""
#     limit = int(request.GET.get('limit', 20))
#     queries = Query.objects.all().order_by('-created_at')[:limit]
#     serializer = QueryHistorySerializer(queries, many=True)
    
#     return Response({
#         'total': Query.objects.count(),
#         'showing': len(queries),
#         'queries': serializer.data
#     })


# @api_view(['GET'])
# def get_query_execution(request, query_id):
#     """Get detailed execution trace for query"""
#     try:
#         query = Query.objects.get(id=query_id)
        
#         return Response({
#             'query_id': str(query.id),
#             'query_text': query.query_text,
#             'answer': query.answer,
#             'strategy_used': query.strategy_used,
#             'execution_steps': query.metadata.get('execution_steps', []),
#             'agents_used': query.agents_used,
#             'source': query.metadata.get('source'),
#             'processing_time': query.processing_time,
#             'confidence_score': query.confidence_score
#         })
#     except Query.DoesNotExist:
#         return Response(
#             {'error': 'Query not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )




"""
Django Views for Multi-Agent RAG System
Complete REST API implementation
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Avg, Count
import logging
import time
import uuid
import asyncio

from apps.rag.models import Document, Query, Session, AgentExecution
from apps.rag.serializers import *
from apps.rag.services.core_services import (
    get_llm_service,
    get_embedding_service,
    get_vector_store
)
from apps.rag.services.agents.coordinator import MultiAgentCoordinator
from apps.rag.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  COORDINATOR SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_coordinator = None

def get_coordinator():
    """Get or create coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        try:
            from django.conf import settings
            tavily_client = None
            if hasattr(settings, 'TAVILY_API_KEY') and settings.TAVILY_API_KEY:
                try:
                    from tavily import TavilyClient
                    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
                except ImportError:
                    logger.warning("[Views] Tavily package not installed")

            _coordinator = MultiAgentCoordinator(
                llm_service       = get_llm_service(),
                vector_store      = get_vector_store(),
                embedding_service = get_embedding_service(),
                tavily_client     = tavily_client,
            )
        except Exception as exc:
            logger.error(f"[Views] Failed to init coordinator: {exc}")
            raise
    return _coordinator


# ─────────────────────────────────────────────────────────────────────────────
#  QUERY
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def query_rag(request):
    """
    Main RAG query endpoint.

    POST /api/rag/v1/query/

    Body:
        query       (str)  — user question
        strategy    (str)  — simple | agentic | multi_agent | auto
        top_k       (int)  — number of chunks to retrieve
        session_id  (uuid) — optional session
        document_id (uuid) — optional document UUID filter

    THE KEY FIX:
        When document_id is provided we look up the Document record in the DB
        to get the actual filename, then pass BOTH:

            context['document_id']     = UUID string   → fallback filter
            context['document_filter'] = "Students_Data.csv"  → primary filter

        RAGAgent._build_filter() uses 'document_filter' (filename) to build:
            {"source": {"$eq": "Students_Data.csv"}}

        This matches what DocumentProcessor stores in ChromaDB:
            metadata["source"] = file.name   ← original filename
    """
    serializer = QueryRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data        = serializer.validated_data
    query_text  = data['query']
    strategy    = data['strategy']
    top_k       = data['top_k']
    session_id  = data.get('session_id')
    document_id = data.get('document_id')

    start_time = time.time()

    try:
        logger.info(f"[Query] '{query_text[:60]}' | strategy={strategy} | doc={document_id}")

        coordinator = get_coordinator()

        # ── Build context ────────────────────────────────────────────────
        context = {
            'top_k':      top_k,
            'session_id': session_id,
            'strategy':   strategy,
        }

        if document_id:
            context['document_id'] = str(document_id)

            # ── CRITICAL FIX: also look up the filename ──────────────────
            # The frontend sends document UUID (d.id).
            # ChromaDB stores metadata["source"] = filename.
            # We need to pass the filename as "document_filter" so RAGAgent
            # can build the correct where-clause: {"source": {"$eq": filename}}
            try:
                doc_obj = Document.objects.get(id=document_id)
                context['document_filter'] = doc_obj.filename
                logger.info(
                    f"[Query] Document filter resolved: "
                    f"UUID={document_id} → filename='{doc_obj.filename}'"
                )
            except Document.DoesNotExist:
                logger.warning(
                    f"[Query] Document {document_id} not found in DB — "
                    "falling back to UUID filter only"
                )

        # ── Execute ──────────────────────────────────────────────────────
        result = asyncio.run(coordinator.execute(query_text, context))

        processing_time = time.time() - start_time

        # ── Save to DB ───────────────────────────────────────────────────
        query_record = Query.objects.create(
            id                    = uuid.uuid4(),
            query_text            = query_text,
            answer                = result['answer'],
            strategy_used         = strategy,
            processing_time       = processing_time,
            confidence_score      = result.get('confidence', 0.7),
            retrieved_chunks_count= len(result.get('retrieved_chunks', [])),
            agent_steps_count     = len(result.get('execution_steps', [])),
            session_id            = session_id,
            document_id           = document_id,
            agents_used           = result.get('agents_used', []),
            metadata              = {
                'execution_steps':  result.get('execution_steps', []),
                'internet_sources': result.get('internet_sources', {}),
                'source':           result.get('source'),
                'agent_type':       result.get('agent_type'),
                'query_type':       result.get('query_type'),
                'document_filter':  context.get('document_filter'),
            }
        )

        # ── Update session ───────────────────────────────────────────────
        if session_id:
            try:
                session = Session.objects.get(id=session_id)
                session.message_count += 1
                session.last_activity  = timezone.now()
                session.save()
            except Session.DoesNotExist:
                pass

        logger.info(
            f"[Query] Done in {processing_time:.2f}s | "
            f"chunks={len(result.get('retrieved_chunks', []))} | "
            f"source={result.get('source')}"
        )

        return Response({
            'query':            query_text,
            'answer':           result['answer'],
            'strategy_used':    strategy,
            'processing_time':  processing_time,
            'retrieved_chunks': result.get('retrieved_chunks', []),
            'confidence_score': result.get('confidence', 0.7),
            'source':           result.get('source'),
            'agent_type':       result.get('agent_type'),
            'execution_steps':  result.get('execution_steps', []),
            'internet_sources': result.get('internet_sources', {}),
            'query_type':       result.get('query_type'),
        }, status=status.HTTP_200_OK)

    except Exception as exc:
        logger.error(f"[Query] Failed: {exc}", exc_info=True)
        return Response(
            {'error': f'Query processing failed: {str(exc)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def upload_document(request):
    """
    Upload and process document.
    POST /api/rag/v1/upload/

    Tabular files (CSV, TSV, tabular TXT) are indexed row-by-row.
    Other files use sliding-window chunking.
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file     = request.FILES['file']
    metadata = request.data.get('metadata', {})

    # Validate extension
    allowed     = ['.pdf', '.txt', '.docx', '.csv', '.tsv']
    filename_lc = file.name.lower()
    if not any(filename_lc.endswith(ext) for ext in allowed):
        return Response(
            {'error': f'Unsupported file type. Allowed: {", ".join(allowed)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    start_time = time.time()

    try:
        logger.info(f"[Upload] '{file.name}' ({file.size:,} bytes)")

        document = Document.objects.create(
            id           = uuid.uuid4(),
            filename     = file.name,
            content_type = file.content_type or 'application/octet-stream',
            size         = file.size,
            status       = 'processing',
            metadata     = metadata if isinstance(metadata, dict) else {},
        )

        processor = DocumentProcessor(
            vector_store      = get_vector_store(),
            embedding_service = get_embedding_service(),
        )

        result = asyncio.run(processor.process_document(
            file        = file,
            document_id = str(document.id),
        ))

        chunks_created = result.get('chunks_created', 0)

        if chunks_created == 0:
            document.status          = 'failed'
            document.chunks_count    = 0
            document.processed_at    = timezone.now()
            document.processing_time = time.time() - start_time
            document.metadata        = {
                **document.metadata,
                'error': 'No text could be extracted from this file.',
            }
            document.save()

            return Response(
                {
                    'error': (
                        f"'{file.name}' was uploaded but no text could be extracted.\n\n"
                        "Possible reasons:\n"
                        "1. PDF is image/scan-based (not text-based)\n"
                        "2. File is empty or corrupted\n\n"
                        "Solutions:\n"
                        "- Copy content into a .txt file and upload that\n"
                        "- Use an online PDF-to-text converter first"
                    )
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        document.status          = 'completed'
        document.chunks_count    = chunks_created
        document.processed_at    = timezone.now()
        document.processing_time = time.time() - start_time
        document.metadata        = {
            **document.metadata,
            'indexing_mode': result.get('indexing_mode', 'unknown'),
        }
        document.save()

        logger.info(
            f"[Upload] '{file.name}' done | "
            f"{chunks_created} chunks | "
            f"mode={result.get('indexing_mode')} | "
            f"time={document.processing_time:.1f}s"
        )

        return Response({
            'document_id':      str(document.id),
            'filename':         document.filename,
            'status':           'success',
            'chunks_created':   chunks_created,
            'indexing_mode':    result.get('indexing_mode', 'unknown'),
            'processing_time':  f"{document.processing_time:.1f}s",
            'message': (
                f"'{file.name}' processed successfully "
                f"({chunks_created} chunks, mode: {result.get('indexing_mode', 'unknown')})"
            ),
        }, status=status.HTTP_201_CREATED)

    except Exception as exc:
        logger.error(f"[Upload] Failed: {exc}", exc_info=True)
        if 'document' in locals():
            document.status   = 'failed'
            document.metadata = {**document.metadata, 'error': str(exc)}
            document.save()
        return Response(
            {'error': f'Upload failed: {str(exc)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  DOCUMENT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def list_documents(request):
    """List all documents."""
    documents  = Document.objects.all().order_by('-uploaded_at')
    serializer = DocumentListSerializer(documents, many=True)
    return Response({'total': documents.count(), 'documents': serializer.data})


@api_view(['GET'])
def get_document(request, document_id):
    """Get single document."""
    try:
        document   = Document.objects.get(id=document_id)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_document(request, document_id):
    """Delete document from DB and vector store."""
    try:
        document = Document.objects.get(id=document_id)
        filename = document.filename

        # Delete chunks from ChromaDB
        vector_store = get_vector_store()
        try:
            vector_store.delete_by_document_id(str(document_id))
            logger.info(f"[Delete] Removed chunks for '{filename}' from ChromaDB")
        except Exception as exc:
            logger.warning(f"[Delete] ChromaDB delete failed: {exc}")

        document.delete()
        logger.info(f"[Delete] Document '{filename}' deleted")

        return Response({'status': 'success', 'message': f"'{filename}' deleted"})

    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def clear_all_documents(request):
    """Clear all documents and reset vector store."""
    try:
        vector_store = get_vector_store()
        vector_store.reset_collection()

        doc_count = Document.objects.count()
        Query.objects.all().delete()
        Document.objects.all().delete()

        logger.info(f"[Clear] Deleted {doc_count} documents and reset ChromaDB")

        return Response({'status': 'success', 'message': f'Cleared {doc_count} documents'})

    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
#  SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def create_session(request):
    """Create new session."""
    user_id = request.data.get('user_id')
    session = Session.objects.create(id=uuid.uuid4(), user_id=user_id)
    return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_session(request, session_id):
    """Get session with its queries."""
    try:
        session       = Session.objects.get(id=session_id)
        queries       = Query.objects.filter(session=session).order_by('created_at')
        response_data = SessionSerializer(session).data
        response_data['queries'] = QueryHistorySerializer(queries, many=True).data
        return Response(response_data)
    except Session.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
#  HEALTH & STATS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    components = {
        'database':          'unknown',
        'llm_service':       'unknown',
        'embedding_service': 'unknown',
        'vector_store':      'unknown',
        'coordinator':       'unknown',
    }
    all_healthy = True

    try:    Document.objects.count(); components['database'] = 'operational'
    except: components['database'] = 'error'; all_healthy = False

    try:    get_llm_service();       components['llm_service'] = 'operational'
    except: components['llm_service'] = 'error'; all_healthy = False

    try:    get_embedding_service(); components['embedding_service'] = 'operational'
    except: components['embedding_service'] = 'error'; all_healthy = False

    try:    vs = get_vector_store(); vs.get_count(); components['vector_store'] = 'operational'
    except: components['vector_store'] = 'error'; all_healthy = False

    try:    get_coordinator();       components['coordinator'] = 'operational'
    except: components['coordinator'] = 'error'; all_healthy = False

    return Response({
        'status':     'healthy' if all_healthy else 'degraded',
        'timestamp':  timezone.now(),
        'version':    '1.0.0',
        'components': components,
    })


@api_view(['GET'])
def get_stats(request):
    """System statistics."""
    return Response({
        'total_documents':         Document.objects.count(),
        'total_queries':           Query.objects.count(),
        'total_chunks':            get_vector_store().get_count(),
        'average_processing_time': Query.objects.aggregate(
            Avg('processing_time')
        )['processing_time__avg'] or 0.0,
        'strategy_distribution':   dict(
            Query.objects.values('strategy_used')
            .annotate(count=Count('id'))
            .values_list('strategy_used', 'count')
        ),
    })


@api_view(['GET'])
def agent_status(request):
    """Get agent status."""
    try:
        coordinator = get_coordinator()
        return Response(coordinator.get_agent_status())
    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
#  QUERY HISTORY & DEBUGGING
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def list_queries(request):
    """List query history."""
    limit    = int(request.GET.get('limit', 20))
    queries  = Query.objects.all().order_by('-created_at')[:limit]
    return Response({
        'total':   Query.objects.count(),
        'showing': len(queries),
        'queries': QueryHistorySerializer(queries, many=True).data,
    })


@api_view(['GET'])
def get_query_execution(request, query_id):
    """Detailed execution trace for a query."""
    try:
        query = Query.objects.get(id=query_id)
        return Response({
            'query_id':        str(query.id),
            'query_text':      query.query_text,
            'answer':          query.answer,
            'strategy_used':   query.strategy_used,
            'execution_steps': query.metadata.get('execution_steps', []),
            'agents_used':     query.agents_used,
            'source':          query.metadata.get('source'),
            'processing_time': query.processing_time,
            'confidence_score':query.confidence_score,
            'document_filter': query.metadata.get('document_filter'),
        })
    except Query.DoesNotExist:
        return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)