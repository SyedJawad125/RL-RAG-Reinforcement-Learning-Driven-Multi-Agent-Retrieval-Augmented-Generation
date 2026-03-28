"""
Django Views for Multi-Agent RAG System
Complete REST API implementation
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Avg, Count, Sum
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
                'rl_metadata':      result.get('rl_metadata', {}),
                'rl_query_id':      result.get('rl_metadata', {}).get('query_id', ''),
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
            'rl_metadata': result.get('rl_metadata', {}),
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
    










"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADD THE FOLLOWING SECTION TO THE BOTTOM OF  apps/rag/views.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Also add these imports near the top of views.py:

    from apps.rag.models import RLExperienceRecord, RLEpisodeSummary
    from apps.rag.serializers import (
        UserFeedbackSerializer,
        RLStatsSerializer,
        RLExperienceRecordSerializer,
        RLEpisodeSummarySerializer,
    )

ALSO — update query_rag() so it stores rl_metadata from the coordinator:
    Inside query_rag(), in the Query.objects.create(...) call,
    add to metadata:
        'rl_metadata': result.get('rl_metadata', {}),
        'rl_query_id': result.get('rl_metadata', {}).get('query_id', ''),

    And after saving the query, call:
        _save_rl_episode(result, query_record)

    The helper _save_rl_episode is defined below.
"""




# ─────────────────────────────────────────────────────────────────────────────
#  HELPER — save episode summary after every query
# ─────────────────────────────────────────────────────────────────────────────

def _save_rl_episode(result: dict, query_record) -> None:
    """
    Called at the end of query_rag() to persist a per-query episode summary.
    Safe to call even if RL metadata is missing (older non-RL responses).
    """
    from apps.rag.models import RLEpisodeSummary

    rl_meta = result.get("rl_metadata", {})
    if not rl_meta:
        return

    try:
        RLEpisodeSummary.objects.update_or_create(
            query_id = rl_meta.get("query_id", str(query_record.id)),
            defaults = {
                "total_steps":      rl_meta.get("steps_taken",    0),
                "total_reward":     rl_meta.get("last_reward",     0.0),
                "final_confidence": result.get("confidence_score", 0.7),
                "epsilon_at_end":   rl_meta.get("epsilon",         None),
                "actions_taken":    [rl_meta.get("last_action", "ANSWER_NOW")],
                "used_internet":    bool(result.get("internet_sources")),
            },
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(f"[Views] _save_rl_episode failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT 1 — User Feedback  (thumbs up / thumbs down)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
def rl_feedback(request):
    """
    Submit user feedback for a completed query.
    This triggers a deferred reward update in the Q-table.

    POST /api/rag/v1/rl/feedback/
    Body: { "query_id": "...", "feedback": "positive" | "negative" }

    Effect:
        • Q(s, a) updated with ± 0.3 for every experience in that episode
        • Q-table persisted to disk immediately
        • RLExperienceRecord rows updated with the feedback label
    """
    serializer = UserFeedbackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query_id = serializer.validated_data["query_id"]
    feedback = serializer.validated_data["feedback"]

    try:
        coordinator = get_coordinator()
        coordinator.rl_agent.apply_user_feedback(query_id, feedback)

        # Update episode summary
        from apps.rag.models import RLEpisodeSummary
        RLEpisodeSummary.objects.filter(query_id=query_id).update(
            user_feedback=feedback
        )

        return Response(
            {
                "status":   "ok",
                "query_id": query_id,
                "feedback": feedback,
                "message":  "Q-table updated with user feedback",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT 2 — Live RL Statistics
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
def rl_stats(request):
    """
    Return live RL training statistics.

    GET /api/rag/v1/rl/stats/

    Response includes:
        • epsilon (exploration rate — should decay over time)
        • total_updates (Q-table updates so far)
        • states_learned (how many unique states the agent has visited)
        • replay_buf_size (experiences stored)
        • db_stats (aggregate rewards, action distribution)
        • recent_episodes (last 10 episode summaries)
    """
    from apps.rag.models import RLExperienceRecord, RLEpisodeSummary

    try:
        coordinator = get_coordinator()
        live_stats  = coordinator.rl_agent.get_rl_stats()

        # DB aggregates
        db_stats = {
            "total_experiences":    RLExperienceRecord.objects.count(),
            "avg_reward":           RLExperienceRecord.objects.aggregate(
                                        avg=Avg("reward"))["avg"] or 0.0,
            "positive_feedback":    RLExperienceRecord.objects.filter(
                                        user_feedback="positive").count(),
            "negative_feedback":    RLExperienceRecord.objects.filter(
                                        user_feedback="negative").count(),
            "action_distribution":  dict(
                RLExperienceRecord.objects
                    .values("action_name")
                    .annotate(count=Count("id"))
                    .values_list("action_name", "count")
            ),
            "terminal_avg_reward":  RLExperienceRecord.objects.filter(
                                        done=True
                                    ).aggregate(avg=Avg("reward"))["avg"] or 0.0,
        }

        # Recent episodes
        recent = RLEpisodeSummary.objects.order_by("-created_at")[:10]
        from apps.rag.serializers import RLEpisodeSummarySerializer
        recent_data = RLEpisodeSummarySerializer(recent, many=True).data

        return Response(
            {
                **live_stats,
                "db_stats":       db_stats,
                "recent_episodes": recent_data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT 3 — Per-Query RL Trace
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
def rl_query_trace(request, query_id):
    """
    Return the full RL decision trace for a specific query.

    GET /api/rag/v1/rl/trace/<query_id>/

    Useful for debugging: see exactly which actions the agent took,
    what rewards it received, and what the Q-values were.
    """
    from apps.rag.models import RLExperienceRecord, RLEpisodeSummary
    from apps.rag.serializers import (
        RLExperienceRecordSerializer,
        RLEpisodeSummarySerializer,
    )

    experiences = RLExperienceRecord.objects.filter(
        query_id=query_id
    ).order_by("created_at")

    if not experiences.exists():
        return Response(
            {"error": "No RL trace found for this query_id"},
            status=status.HTTP_404_NOT_FOUND,
        )

    episode = RLEpisodeSummary.objects.filter(query_id=query_id).first()

    return Response(
        {
            "query_id":    query_id,
            "episode":     RLEpisodeSummarySerializer(episode).data if episode else None,
            "experiences": RLExperienceRecordSerializer(experiences, many=True).data,
        },
        status=status.HTTP_200_OK,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINT 4 — Force Q-Table Replay Training
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
def rl_train(request):
    """
    Manually trigger a replay-training batch.
    Useful for scheduled background jobs or admin panels.

    POST /api/rag/v1/rl/train/
    Body (optional): { "batch_size": 64 }

    Returns updated RL stats after training.
    """
    batch_size = int(request.data.get("batch_size", 32))

    try:
        coordinator = get_coordinator()
        memory      = coordinator.rl_agent.memory

        before_updates = memory.q_table.total_updates
        memory.replay_train(batch_size=batch_size)
        after_updates  = memory.q_table.total_updates

        return Response(
            {
                "status":         "ok",
                "batch_size":     batch_size,
                "updates_before": before_updates,
                "updates_after":  after_updates,
                "new_updates":    after_updates - before_updates,
                "epsilon":        round(memory.q_table.epsilon, 4),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)