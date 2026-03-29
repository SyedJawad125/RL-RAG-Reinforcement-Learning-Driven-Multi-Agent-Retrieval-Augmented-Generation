// 'use client';
// import React, { useState, useEffect, useRef, useCallback } from 'react';
// import AxiosInstance from "@/components/AxiosInstance";

// /* ─── Only keyframes & Google Font here — everything visual is Tailwind ─── */
// const GLOBAL_CSS = `
//   @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@600;700;800&display=swap');
//   .font-mono-custom { font-family: 'JetBrains Mono', monospace; }
//   .font-display      { font-family: 'Syne', sans-serif; }
//   @keyframes fadeUp   { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
//   @keyframes blink    { 0%,49%{opacity:1} 50%,100%{opacity:0} }
//   @keyframes spin     { to { transform: rotate(360deg); } }
//   @keyframes shimmer  { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
//   .animate-fade-up    { animation: fadeUp .3s ease forwards; }
//   .animate-blink      { animation: blink 1s step-end infinite; }
//   .animate-spin-slow  { animation: spin .7s linear infinite; }
//   .scanline-bg {
//     background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.04) 2px, rgba(0,0,0,.04) 4px);
//     pointer-events: none; position: fixed; inset: 0; z-index: 50;
//   }
//   .progress-shimmer {
//     background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 50%, #f59e0b 100%);
//     background-size: 200% 100%;
//     animation: shimmer 1.5s infinite;
//   }
//   .react-border-left { border-left-width: 2px; border-left-style: solid; padding-left: 1rem; }
// `;

// /* ─────────────── Toast System ─────────────── */
// let _setToasts = null;
// const toast = {
//   _push(type, msg) {
//     const id = Date.now();
//     _setToasts?.(p => [...p, { id, type, msg }]);
//     setTimeout(() => _setToasts?.(p => p.filter(t => t.id !== id)), 3800);
//   },
//   success: m => toast._push('success', m),
//   error:   m => toast._push('error',   m),
//   warn:    m => toast._push('warn',    m),
//   info:    m => toast._push('info',    m),
// };

// const TOAST_STYLES = {
//   success: 'bg-green-950 border border-green-600 text-green-400',
//   error:   'bg-red-950   border border-red-600   text-red-400',
//   warn:    'bg-amber-950 border border-amber-600 text-amber-400',
//   info:    'bg-sky-950   border border-sky-600   text-sky-400',
// };
// const TOAST_ICONS = { success: '✓', error: '✗', warn: '!', info: 'i' };

// function Toasts() {
//   const [toasts, setToasts] = useState([]);
//   useEffect(() => { _setToasts = setToasts; }, []);
//   return (
//     <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none">
//       {toasts.map(t => (
//         <div key={t.id} className={`animate-fade-up font-mono-custom text-xs px-4 py-2.5 flex items-center gap-2 min-w-[220px] max-w-xs pointer-events-auto ${TOAST_STYLES[t.type]}`}>
//           <span className="font-bold">[{TOAST_ICONS[t.type]}]</span>
//           {t.msg}
//         </div>
//       ))}
//     </div>
//   );
// }

// /* ─────────────── Helpers ─────────────── */
// const fmt = {
//   bytes: b => { if(!b) return '0 B'; const k=1024,s=['B','KB','MB','GB'],i=Math.floor(Math.log(b)/Math.log(k)); return (b/k**i).toFixed(1)+' '+s[i]; },
//   secs:  v => v ? v.toFixed(2)+'s' : '—',
//   pct:   v => v ? (v*100).toFixed(0)+'%' : '—',
//   date:  d => d ? new Date(d).toLocaleString() : '—',
//   cut:   (s,n=80) => s && s.length>n ? s.slice(0,n)+'…' : (s||''),
// };

// const SOURCE_MAP = {
//   chromadb:          { label:'ChromaDB',   classes:'bg-sky-900/40 border-sky-700 text-sky-400'           },
//   internet:          { label:'Web Search', classes:'bg-green-900/40 border-green-700 text-green-400'     },
//   general_knowledge: { label:'AI Memory',  classes:'bg-violet-900/40 border-violet-700 text-violet-400' },
//   coordinator_agent: { label:'Agent',      classes:'bg-amber-900/40 border-amber-700 text-amber-400'     },
//   error:             { label:'Error',      classes:'bg-red-900/40 border-red-700 text-red-400'           },
// };
// const srcInfo = s => SOURCE_MAP[s] || SOURCE_MAP.coordinator_agent;

// const STEP_MAP = {
//   THOUGHT:     { label:'THINK', border:'#a855f7', text:'text-violet-400', bg:'bg-violet-900/20' },
//   ACTION:      { label:'ACT',   border:'#f59e0b', text:'text-amber-400',  bg:'bg-amber-900/20'  },
//   OBSERVATION: { label:'OBS',   border:'#10b981', text:'text-emerald-400',bg:'bg-emerald-900/20'},
//   ERROR:       { label:'ERR',   border:'#ef4444', text:'text-red-400',    bg:'bg-red-900/20'    },
// };

// /* ─────────────── Reusable UI Pieces ─────────────── */
// function Badge({ children, classes }) {
//   return (
//     <span className={`font-mono-custom text-[10px] tracking-widest uppercase px-2 py-0.5 border ${classes}`}>
//       {children}
//     </span>
//   );
// }

// function SectionLabel({ children }) {
//   return (
//     <div className="font-mono-custom text-[10px] tracking-[.18em] uppercase text-gray-500 mb-3 flex items-center gap-2">
//       {children}
//       <span className="flex-1 h-px bg-gray-800" />
//     </div>
//   );
// }

// function InputField({ label, ...props }) {
//   return (
//     <div>
//       {label && <label className="block font-mono-custom text-[10px] tracking-widest uppercase text-gray-500 mb-1.5">{label}</label>}
//       <input
//         className="w-full bg-gray-900 border border-gray-700 text-gray-200 font-mono-custom text-sm px-3 py-2 outline-none focus:border-amber-500 transition-colors placeholder-gray-600"
//         {...props}
//       />
//     </div>
//   );
// }

// function SelectField({ label, children, ...props }) {
//   return (
//     <div>
//       {label && <label className="block font-mono-custom text-[10px] tracking-widest uppercase text-gray-500 mb-1.5">{label}</label>}
//       <select
//         className="w-full bg-gray-900 border border-gray-700 text-gray-200 font-mono-custom text-sm px-3 py-2 outline-none focus:border-amber-500 transition-colors cursor-pointer"
//         {...props}
//       >
//         {children}
//       </select>
//     </div>
//   );
// }

// function TextareaField({ label, ...props }) {
//   return (
//     <div>
//       {label && <label className="block font-mono-custom text-[10px] tracking-widest uppercase text-gray-500 mb-1.5">{label}</label>}
//       <textarea
//         className="w-full bg-gray-900 border border-gray-700 text-gray-200 font-mono-custom text-sm px-3 py-2 outline-none focus:border-amber-500 transition-colors placeholder-gray-600 resize-y"
//         {...props}
//       />
//     </div>
//   );
// }

// function PrimaryBtn({ children, loading, loadingText = 'Processing…', className = '', ...props }) {
//   return (
//     <button
//       className={`bg-amber-500 hover:bg-amber-400 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-gray-950 font-mono-custom font-bold text-xs tracking-widest uppercase px-4 py-3 transition-colors flex items-center justify-center gap-2 w-full ${className}`}
//       {...props}
//     >
//       {loading ? (
//         <>
//           <span className="animate-spin-slow w-3.5 h-3.5 border-2 border-gray-950/30 border-t-gray-950 rounded-full inline-block" />
//           {loadingText}
//         </>
//       ) : children}
//     </button>
//   );
// }

// function GhostBtn({ children, className = '', ...props }) {
//   return (
//     <button
//       className={`font-mono-custom text-[10px] tracking-widest uppercase px-3 py-1.5 border border-gray-700 text-gray-500 hover:border-amber-500 hover:text-amber-400 transition-colors ${className}`}
//       {...props}
//     >
//       {children}
//     </button>
//   );
// }

// function DangerBtn({ children, ...props }) {
//   return (
//     <button
//       className="font-mono-custom text-[10px] tracking-widest uppercase px-3 py-1.5 border border-red-900 text-red-500 hover:bg-red-900/30 transition-colors"
//       {...props}
//     >
//       {children}
//     </button>
//   );
// }

// function Card({ children, className = '' }) {
//   return (
//     <div className={`bg-gray-900 border border-gray-800 p-5 animate-fade-up ${className}`}>
//       {children}
//     </div>
//   );
// }

// function HealthDot({ status }) {
//   const cls = status === 'operational'
//     ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]'
//     : status === 'error' ? 'bg-red-400 shadow-[0_0_6px_#ef4444]'
//     : 'bg-gray-600';
//   return <span className={`inline-block w-2 h-2 rounded-full ${cls}`} />;
// }

// /* ─────────────────────────── MAIN COMPONENT ─────────────────────────── */
// export default function RAGSystem() {
//   const [tab, setTab] = useState('query');
//   const [loading, setLoading] = useState(false);

//   // Query state
//   const [queryText,   setQueryText]   = useState('');
//   const [strategy,    setStrategy]    = useState('agentic');
//   const [topK,        setTopK]        = useState(15);
//   const [selectedDoc, setSelectedDoc] = useState('');
//   const [queryResult, setQueryResult] = useState(null);
//   const [agentTrace,  setAgentTrace]  = useState(null);

//   // Upload state
//   const [file,      setFile]      = useState(null);
//   const [uploadPct, setUploadPct] = useState(0);
//   const [dragging,  setDragging]  = useState(false);
//   const fileRef = useRef();

//   // Data state
//   const [documents,    setDocuments]    = useState([]);
//   const [queryHistory, setQueryHistory] = useState([]);
//   const [stats,        setStats]        = useState({ total_documents:0, total_queries:0, total_chunks:0, average_processing_time:0, strategy_distribution:{} });
//   const [health,       setHealth]       = useState(null);
//   const [agentStatus,  setAgentStatus]  = useState(null);

//   /* ─ Init ─ */
//   useEffect(() => {
//     fetchDocuments(); fetchStats(); fetchHealth();
//     try { const s = localStorage.getItem('rag_qh'); if(s) setQueryHistory(JSON.parse(s)); } catch(_){}
//   }, []);

//   // Ctrl+Enter shortcut
//   useEffect(() => {
//     const h = e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') submitQuery(); };
//     window.addEventListener('keydown', h);
//     return () => window.removeEventListener('keydown', h);
//   }, [queryText, strategy, topK, selectedDoc]);

//   /* ─ API helpers ─ */
//   const fetchDocuments  = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/documents/'); setDocuments(r.data.documents || []); } catch(_){} };
//   const fetchStats      = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/stats/'); setStats(r.data); } catch(_){} };
//   const fetchHealth     = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/health/'); setHealth(r.data); } catch(_){ setHealth({ status:'error', components:{} }); } };
//   const fetchAgentStatus= async () => { try { const r = await AxiosInstance.get('/api/rag/v1/agents/status/'); setAgentStatus(r.data); } catch(_){} };

//   /* ─ Submit Query ─ */
//   const submitQuery = async () => {
//     if (!queryText.trim()) { toast.warn('Enter a query first'); return; }
//     setLoading(true); setQueryResult(null); setAgentTrace(null);
//     try {
//       const r = await AxiosInstance.post('/api/rag/v1/query/', {
//         query: queryText, strategy, top_k: topK, document_id: selectedDoc || null,
//       });
//       const d = r.data;
//       setQueryResult(d);
//       if (d.execution_steps?.length) {
//         setAgentTrace({
//           steps: d.execution_steps, agent_type: d.agent_type || 'react_coordinator',
//           source: d.source || 'unknown', internet_sources: d.internet_sources || [],
//           fallback_used: d.fallback_used || false,
//         });
//       }
//       const entry = {
//         id: Date.now().toString(), query: d.query, answer: d.answer,
//         strategy: d.strategy_used, processing_time: d.processing_time,
//         confidence_score: d.confidence_score, agent_type: d.agent_type,
//         source: d.source, steps: d.execution_steps?.length || 0,
//         timestamp: new Date().toISOString(),
//       };
//       setQueryHistory(prev => {
//         const next = [entry, ...prev.slice(0,49)];
//         localStorage.setItem('rag_qh', JSON.stringify(next));
//         return next;
//       });
//       fetchStats();
//       toast.success('Query completed');
//     } catch(e) { toast.error(e.response?.data?.error || 'Query failed'); }
//     finally { setLoading(false); }
//   };

//   /* ─ Upload ─ */
//   const submitUpload = async () => {
//     if (!file) { toast.warn('Select a file first'); return; }
//     const fd = new FormData(); fd.append('file', file);
//     setLoading(true); setUploadPct(0);
//     try {
//       const r = await AxiosInstance.post('/api/rag/v1/upload/', fd, {
//         headers: { 'Content-Type': 'multipart/form-data' },
//         onUploadProgress: e => setUploadPct(e.total ? Math.round(e.loaded*100/e.total) : 50),
//       });
//       toast.success(`Ingested ${r.data.chunks_created} chunks`);
//       setFile(null); setUploadPct(0); fetchDocuments(); fetchStats();
//     } catch(e) { toast.error(e.response?.data?.error || 'Upload failed'); }
//     finally { setLoading(false); }
//   };

//   /* ─ Delete / Clear ─ */
//   const deleteDoc = async (id, name) => {
//     if (!confirm(`Delete "${name}"?`)) return;
//     try { await AxiosInstance.delete(`/api/rag/v1/documents/${id}/delete/`); toast.success('Removed'); fetchDocuments(); fetchStats(); }
//     catch(_) { toast.error('Delete failed'); }
//   };
//   const clearAll = async () => {
//     if (!confirm('⚠ Delete ALL documents and vectors?')) return;
//     setLoading(true);
//     try { await AxiosInstance.delete('/api/rag/v1/documents/clear/'); toast.success('All cleared'); fetchDocuments(); fetchStats(); }
//     catch(_) { toast.error('Clear failed'); }
//     finally { setLoading(false); }
//   };

//   /* ─ Drag-drop ─ */
//   const onDrop = useCallback(e => {
//     e.preventDefault(); setDragging(false);
//     const f = e.dataTransfer.files[0]; if(f) setFile(f);
//   }, []);

//   /* ────────────────────────────────── RENDER ────────────────────────────────── */
//   return (
//     <>
//       <style>{GLOBAL_CSS}</style>
//       <div className="scanline-bg" />
//       <Toasts />

//       <div className="font-mono-custom bg-gray-950 min-h-screen text-gray-300">

//         {/* ═══ HEADER ═══ */}
//         <header className="sticky top-0 z-40 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800 px-6 py-3 flex items-center justify-between">
//           <div className="flex items-center gap-4">
//             <span className="font-display text-lg font-extrabold text-amber-400 tracking-tight">
//               RAGENT<span className="text-gray-700">/</span>OS
//             </span>
//             <span className="hidden sm:block w-px h-5 bg-gray-800" />
//             <span className="hidden sm:block text-[10px] tracking-[.18em] uppercase text-gray-600">
//               Multi-Agent RAG System
//             </span>
//           </div>
//           <div className="flex items-center gap-4">
//             {health && (
//               <span className="flex items-center gap-1.5 text-[10px] tracking-widest uppercase text-gray-600">
//                 <HealthDot status={health.status === 'healthy' ? 'operational' : 'error'} />
//                 {health.status}
//               </span>
//             )}
//             <span className="text-[10px] text-gray-700 hidden sm:block">
//               {new Date().toLocaleTimeString()}
//             </span>
//           </div>
//         </header>

//         {/* ═══ STATS STRIP ═══ */}
//         <div className="border-b border-gray-800 bg-gray-950 px-6 py-3 flex gap-3 overflow-x-auto">
//           {[
//             { label:'Documents', val: stats.total_documents,                   color:'text-amber-400',  bar:'bg-amber-400'  },
//             { label:'Chunks',    val: stats.total_chunks,                      color:'text-sky-400',    bar:'bg-sky-400'    },
//             { label:'Queries',   val: stats.total_queries,                     color:'text-emerald-400',bar:'bg-emerald-400'},
//             { label:'Avg Time',  val: fmt.secs(stats.average_processing_time), color:'text-violet-400', bar:'bg-violet-400' },
//           ].map(s => (
//             <div key={s.label} className="relative flex flex-col items-center justify-center bg-gray-900 border border-gray-800 px-5 py-2 min-w-[90px] shrink-0 overflow-hidden">
//               <span className={`font-display text-2xl font-bold leading-none ${s.color}`}>{s.val}</span>
//               <span className="text-[9px] tracking-[.15em] uppercase text-gray-600 mt-1">{s.label}</span>
//               <span className={`absolute bottom-0 left-0 right-0 h-0.5 ${s.bar}`} />
//             </div>
//           ))}
//           {Object.entries(stats.strategy_distribution || {}).map(([k, v]) => (
//             <div key={k} className="flex flex-col items-center justify-center bg-gray-900 border border-gray-800 px-4 py-2 shrink-0">
//               <span className="font-display text-xl font-bold text-gray-300 leading-none">{v}</span>
//               <span className="text-[9px] tracking-[.15em] uppercase text-gray-600 mt-1">{k}</span>
//             </div>
//           ))}
//         </div>

//         {/* ═══ NAV TABS ═══ */}
//         <div className="flex border-b border-gray-800 bg-gray-950 overflow-x-auto">
//           {[
//             { id:'query',   label:'Query'       },
//             { id:'upload',  label:'Ingest'      },
//             { id:'docs',    label:'Documents'   },
//             { id:'history', label:'History'     },
//             { id:'trace',   label:'Agent Trace' },
//             { id:'health',  label:'Health'      },
//           ].map(n => (
//             <button
//               key={n.id}
//               onClick={() => { setTab(n.id); if(n.id==='health'){fetchHealth();fetchAgentStatus();} }}
//               className={`shrink-0 px-5 py-3 text-[10px] tracking-[.18em] uppercase transition-colors border-b-2
//                 ${tab === n.id
//                   ? 'text-amber-400 border-amber-500'
//                   : 'text-gray-600 border-transparent hover:text-gray-300'}`}
//             >
//               {n.label}
//             </button>
//           ))}
//         </div>

//         {/* ═══ CONTENT ═══ */}
//         <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">

//           {/* ── QUERY TAB ── */}
//           {tab === 'query' && (
//             <div className="grid lg:grid-cols-2 gap-5 items-start">

//               {/* Left: inputs */}
//               <div className="flex flex-col gap-4">
//                 <Card>
//                   <SectionLabel>Query Input</SectionLabel>
//                   <TextareaField
//                     label="Your Question"
//                     rows={5}
//                     value={queryText}
//                     onChange={e => setQueryText(e.target.value)}
//                     placeholder="e.g. What are the main findings in the uploaded report?"
//                   />
//                   <div className="grid grid-cols-2 gap-3 mt-4">
//                     <SelectField label="Strategy" value={strategy} onChange={e => setStrategy(e.target.value)}>
//                       <option value="simple">Simple</option>
//                       <option value="agentic">Agentic (ReAct)</option>
//                       <option value="multi_agent">Multi-Agent</option>
//                       <option value="auto">Auto</option>
//                     </SelectField>
//                     <InputField label="Top-K Chunks" type="number" min={1} max={50} value={topK} onChange={e => setTopK(+e.target.value)} />
//                   </div>
//                   <div className="mt-3">
//                     <SelectField label="Document Filter (optional)" value={selectedDoc} onChange={e => setSelectedDoc(e.target.value)}>
//                       <option value="">All documents</option>
//                       {documents.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
//                     </SelectField>
//                   </div>
//                   <div className="mt-5 flex items-center gap-3">
//                     <PrimaryBtn loading={loading} loadingText="Processing…" onClick={submitQuery} disabled={loading}>
//                       ▶ Execute Query
//                     </PrimaryBtn>
//                     <span className="text-[9px] text-gray-600 whitespace-nowrap tracking-widest">Ctrl+↵</span>
//                   </div>
//                 </Card>

//                 {/* Strategy guide */}
//                 <Card>
//                   <SectionLabel>Strategy Guide</SectionLabel>
//                   <div className="flex flex-col gap-2.5 text-xs text-gray-500 leading-relaxed">
//                     {[
//                       { s:'simple',      c:'text-sky-400',     d:'Direct vector search in ChromaDB. Fastest, no reasoning.' },
//                       { s:'agentic',     c:'text-amber-400',   d:'ReAct loop: Thought → Action → Observation cycles.'       },
//                       { s:'multi_agent', c:'text-violet-400',  d:'Parallel sub-agents synthesised by coordinator.'           },
//                       { s:'auto',        c:'text-emerald-400', d:'Auto-selects strategy based on query complexity.'          },
//                     ].map(r => (
//                       <div key={r.s} className={`flex gap-2.5 transition-opacity duration-200 ${strategy===r.s ? 'opacity-100' : 'opacity-35'}`}>
//                         <span className={`${r.c} font-bold w-20 shrink-0`}>{r.s}</span>
//                         <span>{r.d}</span>
//                       </div>
//                     ))}
//                   </div>
//                 </Card>
//               </div>

//               {/* Right: results */}
//               <div className="flex flex-col gap-4">
//                 {queryResult ? (
//                   <>
//                     <Card>
//                       <div className="flex items-start justify-between mb-4 gap-3 flex-wrap">
//                         <SectionLabel>Answer</SectionLabel>
//                         <div className="flex flex-wrap gap-1.5">
//                           {queryResult.source && <Badge classes={srcInfo(queryResult.source).classes}>{srcInfo(queryResult.source).label}</Badge>}
//                           <Badge classes="bg-amber-900/40 border-amber-700 text-amber-400">{fmt.secs(queryResult.processing_time)}</Badge>
//                           {queryResult.confidence_score && <Badge classes="bg-emerald-900/40 border-emerald-700 text-emerald-400">{fmt.pct(queryResult.confidence_score)}</Badge>}
//                         </div>
//                       </div>

//                       {/* Answer text */}
//                       <div className="bg-gray-950 border border-gray-800 border-l-2 border-l-amber-500 px-4 py-3 text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
//                         {queryResult.answer}
//                       </div>

//                       {/* Meta row */}
//                       <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
//                         <span>Strategy: <strong className="text-gray-300">{queryResult.strategy_used}</strong></span>
//                         <span>Chunks: <strong className="text-gray-300">{queryResult.retrieved_chunks?.length || 0}</strong></span>
//                         {queryResult.agent_type && <span>Agent: <strong className="text-gray-300">{queryResult.agent_type}</strong></span>}
//                         {agentTrace && <span>Steps: <strong className="text-amber-400">{agentTrace.steps.length}</strong></span>}
//                       </div>

//                       {agentTrace && (
//                         <GhostBtn className="mt-3" onClick={() => setTab('trace')}>
//                           View Agent Trace →
//                         </GhostBtn>
//                       )}
//                     </Card>

//                     {/* Chunks preview */}
//                     {queryResult.retrieved_chunks?.length > 0 && (
//                       <Card>
//                         <SectionLabel>Retrieved Chunks ({queryResult.retrieved_chunks.length})</SectionLabel>
//                         <div className="flex flex-col gap-2 max-h-52 overflow-y-auto">
//                           {queryResult.retrieved_chunks.slice(0,5).map((c, i) => (
//                             <div key={i} className="bg-gray-950 border-l-2 border-gray-700 pl-3 py-1.5 text-xs text-gray-500 leading-relaxed">
//                               <span className="text-amber-500 mr-2 font-bold">#{i+1}</span>
//                               {fmt.cut(typeof c === 'string' ? c : (c.content || JSON.stringify(c)), 130)}
//                             </div>
//                           ))}
//                           {queryResult.retrieved_chunks.length > 5 && (
//                             <p className="text-[10px] text-gray-600 text-center py-1">
//                               +{queryResult.retrieved_chunks.length - 5} more chunks
//                             </p>
//                           )}
//                         </div>
//                       </Card>
//                     )}
//                   </>
//                 ) : (
//                   <Card className="flex flex-col items-center justify-center min-h-[280px] gap-3">
//                     <div className="text-6xl text-gray-800 select-none font-display">◈</div>
//                     <p className="text-[10px] text-gray-600 tracking-widest uppercase">Awaiting query execution</p>
//                   </Card>
//                 )}
//               </div>
//             </div>
//           )}

//           {/* ── INGEST TAB ── */}
//           {tab === 'upload' && (
//             <div className="max-w-xl mx-auto flex flex-col gap-4">
//               <Card>
//                 <SectionLabel>Document Ingestion</SectionLabel>

//                 {/* Drop zone */}
//                 <div
//                   onClick={() => fileRef.current?.click()}
//                   onDragOver={e => { e.preventDefault(); setDragging(true); }}
//                   onDragLeave={() => setDragging(false)}
//                   onDrop={onDrop}
//                   className={`border-2 border-dashed p-10 text-center cursor-pointer transition-colors
//                     ${dragging ? 'border-amber-500 bg-amber-900/10' : 'border-gray-700 hover:border-gray-500'}`}
//                 >
//                   <input ref={fileRef} type="file" accept=".pdf,.txt,.docx" className="hidden"
//                     onChange={e => setFile(e.target.files?.[0] || null)} />
//                   <div className="text-4xl text-gray-600 mb-3">⬆</div>
//                   <p className="text-sm text-gray-300 mb-1">{file ? file.name : 'Drop file or click to browse'}</p>
//                   <p className="text-[10px] tracking-widest uppercase text-gray-600">PDF · TXT · DOCX · max 50 MB</p>
//                 </div>

//                 {/* Selected file */}
//                 {file && (
//                   <div className="mt-3 bg-gray-950 border border-gray-800 px-4 py-3 flex items-center justify-between gap-4">
//                     <div>
//                       <p className="text-sm text-gray-200">{file.name}</p>
//                       <p className="text-[10px] text-gray-500 mt-0.5">{fmt.bytes(file.size)}</p>
//                     </div>
//                     <button onClick={() => setFile(null)} className="text-gray-600 hover:text-red-400 transition-colors">✕</button>
//                   </div>
//                 )}

//                 {/* Progress */}
//                 {uploadPct > 0 && (
//                   <div className="mt-3">
//                     <div className="flex justify-between text-[10px] text-gray-500 mb-1.5">
//                       <span>Uploading…</span><span>{uploadPct}%</span>
//                     </div>
//                     <div className="h-0.5 bg-gray-800 overflow-hidden">
//                       <div className="progress-shimmer h-full transition-all" style={{ width:`${uploadPct}%` }} />
//                     </div>
//                   </div>
//                 )}

//                 <div className="mt-5">
//                   <PrimaryBtn loading={loading} loadingText="Ingesting…" onClick={submitUpload} disabled={!file || loading}>
//                     ▶ Ingest Document
//                   </PrimaryBtn>
//                 </div>
//               </Card>

//               {/* Pipeline */}
//               <Card>
//                 <SectionLabel>Processing Pipeline</SectionLabel>
//                 <div className="flex flex-col">
//                   {[
//                     'Validate & parse uploaded file',
//                     'Extract raw text content',
//                     'Split into semantic chunks',
//                     'Generate vector embeddings',
//                     'Store vectors in ChromaDB',
//                     'Index metadata in PostgreSQL',
//                   ].map((step, i) => (
//                     <div key={i} className="flex items-center gap-3 text-xs text-gray-500 py-2 border-b border-gray-800 last:border-0">
//                       <span className="text-amber-500 font-bold w-4 shrink-0 text-center">{i+1}</span>
//                       {step}
//                     </div>
//                   ))}
//                 </div>
//               </Card>
//             </div>
//           )}

//           {/* ── DOCUMENTS TAB ── */}
//           {tab === 'docs' && (
//             <div>
//               <div className="flex items-center justify-between mb-5">
//                 <h2 className="font-display text-base font-bold text-gray-100">
//                   Documents{' '}
//                   <span className="text-gray-600 font-normal text-sm">({documents.length})</span>
//                 </h2>
//                 <div className="flex gap-2">
//                   <GhostBtn onClick={fetchDocuments}>↻ Refresh</GhostBtn>
//                   {documents.length > 0 && <DangerBtn onClick={clearAll}>Clear All</DangerBtn>}
//                 </div>
//               </div>

//               {documents.length > 0 ? (
//                 <Card className="p-0 overflow-hidden">
//                   {/* Table header */}
//                   <div className="hidden sm:grid grid-cols-[1fr_80px_72px_90px_100px_32px] gap-3 px-4 py-2.5 border-b border-gray-800 text-[9px] tracking-[.18em] uppercase text-gray-600">
//                     <span>Filename</span>
//                     <span>Size</span>
//                     <span>Chunks</span>
//                     <span>Status</span>
//                     <span>Uploaded</span>
//                     <span />
//                   </div>
//                   {documents.map(d => (
//                     <div key={d.id} className="flex sm:grid sm:grid-cols-[1fr_80px_72px_90px_100px_32px] flex-col gap-1 sm:gap-3 items-start sm:items-center px-4 py-3 border-b border-gray-800 last:border-0 hover:bg-gray-800/40 transition-colors">
//                       <span className="text-sm text-gray-200 truncate w-full">{d.filename}</span>
//                       <span className="text-xs text-gray-500">{fmt.bytes(d.size)}</span>
//                       <span className="text-xs text-sky-400 font-bold">{d.chunks_count}</span>
//                       <span>
//                         <Badge classes={
//                           d.status==='completed' ? 'bg-emerald-900/30 border-emerald-700 text-emerald-400'
//                           : d.status==='failed'  ? 'bg-red-900/30 border-red-700 text-red-400'
//                           : 'bg-amber-900/30 border-amber-700 text-amber-400'
//                         }>{d.status}</Badge>
//                       </span>
//                       <span className="text-[10px] text-gray-600">{new Date(d.uploaded_at).toLocaleDateString()}</span>
//                       <button onClick={() => deleteDoc(d.id, d.filename)} className="text-gray-700 hover:text-red-400 transition-colors text-xs self-end sm:self-auto">✕</button>
//                     </div>
//                   ))}
//                 </Card>
//               ) : (
//                 <Card className="flex flex-col items-center justify-center py-16 gap-4">
//                   <span className="text-5xl text-gray-800">◫</span>
//                   <p className="text-sm text-gray-600">No documents ingested yet</p>
//                   <PrimaryBtn onClick={() => setTab('upload')} className="max-w-[220px]">Ingest First Document</PrimaryBtn>
//                 </Card>
//               )}
//             </div>
//           )}

//           {/* ── HISTORY TAB ── */}
//           {tab === 'history' && (
//             <div>
//               <div className="flex items-center justify-between mb-5">
//                 <h2 className="font-display text-base font-bold text-gray-100">
//                   Query History{' '}
//                   <span className="text-gray-600 font-normal text-sm">({queryHistory.length})</span>
//                 </h2>
//                 {queryHistory.length > 0 && (
//                   <DangerBtn onClick={() => { setQueryHistory([]); localStorage.removeItem('rag_qh'); toast.info('History cleared'); }}>
//                     Clear History
//                   </DangerBtn>
//                 )}
//               </div>

//               {queryHistory.length > 0 ? (
//                 <div className="flex flex-col gap-3">
//                   {queryHistory.map(h => (
//                     <div key={h.id} className="animate-fade-up bg-gray-900 border border-gray-800 border-l-2 border-l-gray-700 hover:border-l-amber-500 px-4 py-3.5 transition-colors cursor-default">
//                       <div className="flex items-start justify-between gap-3 mb-3 flex-wrap">
//                         <div className="flex flex-wrap gap-1.5">
//                           {h.source   && <Badge classes={srcInfo(h.source).classes}>{srcInfo(h.source).label}</Badge>}
//                           <Badge classes="bg-amber-900/40 border-amber-700 text-amber-400">{h.strategy}</Badge>
//                           <Badge classes="bg-sky-900/40 border-sky-700 text-sky-400">{fmt.secs(h.processing_time)}</Badge>
//                           {h.confidence_score && <Badge classes="bg-emerald-900/40 border-emerald-700 text-emerald-400">{fmt.pct(h.confidence_score)}</Badge>}
//                           {h.steps > 0 && <Badge classes="bg-violet-900/40 border-violet-700 text-violet-400">{h.steps} steps</Badge>}
//                         </div>
//                         <span className="text-[10px] text-gray-600 shrink-0">{fmt.date(h.timestamp)}</span>
//                       </div>
//                       <p className="text-sm text-amber-400 mb-1.5 leading-snug">Q: {fmt.cut(h.query, 100)}</p>
//                       <p className="text-xs text-gray-500 leading-relaxed">A: {fmt.cut(h.answer, 180)}</p>
//                     </div>
//                   ))}
//                 </div>
//               ) : (
//                 <Card className="flex flex-col items-center justify-center py-16 gap-3">
//                   <span className="text-5xl text-gray-800">◌</span>
//                   <p className="text-sm text-gray-600">No queries yet</p>
//                 </Card>
//               )}
//             </div>
//           )}

//           {/* ── AGENT TRACE TAB ── */}
//           {tab === 'trace' && (
//             <div>
//               {agentTrace ? (
//                 <div className="flex flex-col gap-5">

//                   {/* Overview */}
//                   <Card>
//                     <SectionLabel>Execution Overview</SectionLabel>
//                     <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
//                       {[
//                         { label:'Agent Type',  val: agentTrace.agent_type,                    cls:'text-amber-400'  },
//                         { label:'Source',      val: srcInfo(agentTrace.source).label,         cls:'text-sky-400'    },
//                         { label:'Total Steps', val: agentTrace.steps.length,                  cls:'text-emerald-400'},
//                         { label:'Fallback',    val: agentTrace.fallback_used ? 'Yes' : 'No',  cls: agentTrace.fallback_used ? 'text-red-400' : 'text-gray-500' },
//                       ].map(r => (
//                         <div key={r.label} className="bg-gray-950 border border-gray-800 p-3">
//                           <p className="text-[9px] tracking-widest uppercase text-gray-600 mb-1">{r.label}</p>
//                           <p className={`text-sm font-bold ${r.cls}`}>{r.val}</p>
//                         </div>
//                       ))}
//                     </div>
//                     {/* Step-type counts */}
//                     <div className="flex flex-wrap gap-2">
//                       {Object.entries(STEP_MAP).map(([type, m]) => {
//                         const count = agentTrace.steps.filter(s => s.type === type).length;
//                         return count > 0 ? (
//                           <span key={type} className={`text-[10px] px-3 py-1 ${m.text}`}
//                             style={{ border:`1px solid ${m.border}40`, background:`${m.border}12` }}>
//                             {type}: {count}
//                           </span>
//                         ) : null;
//                       })}
//                     </div>
//                   </Card>

//                   {/* Tavily sources */}
//                   {agentTrace.internet_sources?.length > 0 && (
//                     <Card>
//                       <SectionLabel>Web Sources — Tavily ({agentTrace.internet_sources.length})</SectionLabel>
//                       <div className="flex flex-col gap-3">
//                         {agentTrace.internet_sources.map((src, i) => (
//                           <div key={i} className="bg-gray-950 border border-gray-800 border-l-2 border-l-emerald-600 pl-4 pr-3 py-3">
//                             <p className="text-sm text-gray-200 font-semibold mb-1">{src.title || 'Untitled'}</p>
//                             {src.snippet && <p className="text-xs text-gray-500 leading-relaxed mb-2">{fmt.cut(src.snippet, 160)}</p>}
//                             <div className="flex items-center justify-between gap-3">
//                               {src.url && <a href={src.url} target="_blank" rel="noreferrer" className="text-[10px] text-sky-500 hover:text-sky-400 transition-colors truncate">{fmt.cut(src.url, 60)}</a>}
//                               {src.score && <span className="text-[10px] text-emerald-400 shrink-0">{fmt.pct(src.score)}</span>}
//                             </div>
//                           </div>
//                         ))}
//                       </div>
//                     </Card>
//                   )}

//                   {/* ReAct steps */}
//                   <Card>
//                     <SectionLabel>ReAct Execution Trace</SectionLabel>
//                     <div className="flex flex-col gap-4">
//                       {agentTrace.steps.map((step, i) => {
//                         const m = STEP_MAP[step.type] || STEP_MAP.OBSERVATION;
//                         return (
//                           <div key={i} className={`react-border-left animate-fade-up ${m.bg}`} style={{ borderColor: m.border }}>
//                             <div className="flex items-center gap-2 mb-2">
//                               <span className={`text-[10px] tracking-[.18em] font-bold ${m.text}`}>
//                                 [{String(i+1).padStart(2,'0')}] {m.label}
//                               </span>
//                               {step.timestamp && (
//                                 <span className="text-[9px] text-gray-600">
//                                   {new Date(step.timestamp).toLocaleTimeString()}
//                                 </span>
//                               )}
//                             </div>
//                             <div className="bg-gray-950 border border-gray-800 px-4 py-3 text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
//                               {step.content}
//                             </div>
//                           </div>
//                         );
//                       })}
//                     </div>
//                   </Card>
//                 </div>
//               ) : (
//                 <Card className="flex flex-col items-center justify-center py-16 gap-4">
//                   <span className="text-5xl text-gray-800">⊙</span>
//                   <div className="text-center">
//                     <p className="text-sm text-gray-500 mb-1">No agent trace available</p>
//                     <p className="text-xs text-gray-600 mb-5">Run a query with Agentic strategy to capture the ReAct execution trace</p>
//                   </div>
//                   <PrimaryBtn onClick={() => { setStrategy('agentic'); setTab('query'); }} className="max-w-xs">
//                     Switch to Agentic Mode
//                   </PrimaryBtn>
//                 </Card>
//               )}
//             </div>
//           )}

//           {/* ── HEALTH TAB ── */}
//           {tab === 'health' && (
//             <div className="flex flex-col gap-5">

//               {/* Health */}
//               <Card>
//                 <div className="flex items-center justify-between mb-4">
//                   <SectionLabel>System Health</SectionLabel>
//                   <GhostBtn onClick={() => { fetchHealth(); fetchAgentStatus(); }}>↻ Refresh</GhostBtn>
//                 </div>
//                 {health ? (
//                   <>
//                     <div className="mb-4">
//                       <Badge classes={
//                         health.status === 'healthy'
//                           ? 'bg-emerald-900/30 border-emerald-700 text-emerald-400'
//                           : 'bg-red-900/30 border-red-700 text-red-400'
//                       }>
//                         {health.status?.toUpperCase()}
//                       </Badge>
//                     </div>
//                     <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
//                       {Object.entries(health.components || {}).map(([k, v]) => (
//                         <div key={k} className="bg-gray-950 border border-gray-800 px-3 py-2.5 flex items-center gap-3">
//                           <HealthDot status={v} />
//                           <div>
//                             <p className="text-xs text-gray-300 capitalize">{k.replace(/_/g,' ')}</p>
//                             <p className={`text-[10px] ${v==='operational' ? 'text-emerald-400' : 'text-red-400'}`}>{v}</p>
//                           </div>
//                         </div>
//                       ))}
//                     </div>
//                     <p className="mt-3 text-[10px] text-gray-600">
//                       Checked: {fmt.date(health.timestamp)} · Version {health.version || '—'}
//                     </p>
//                   </>
//                 ) : (
//                   <p className="text-xs text-gray-600">Click Refresh to load health status.</p>
//                 )}
//               </Card>

//               {/* Agent status */}
//               <Card>
//                 <SectionLabel>Agent Status</SectionLabel>
//                 {agentStatus ? (
//                   <pre className="text-xs text-gray-500 leading-relaxed overflow-auto max-h-64 bg-gray-950 p-4 border border-gray-800">
//                     {JSON.stringify(agentStatus, null, 2)}
//                   </pre>
//                 ) : (
//                   <p className="text-xs text-gray-600">Click Refresh above to load agent status.</p>
//                 )}
//               </Card>

//               {/* API reference */}
//               <Card>
//                 <SectionLabel>API Endpoints</SectionLabel>
//                 <div className="flex flex-col gap-1.5">
//                   {[
//                     { m:'POST',   c:'text-emerald-400', ep:'/api/rag/v1/query/',                  desc:'Execute RAG query'    },
//                     { m:'POST',   c:'text-emerald-400', ep:'/api/rag/v1/upload/',                 desc:'Ingest document'      },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/documents/',              desc:'List documents'       },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/documents/<id>/',         desc:'Single document'      },
//                     { m:'DELETE', c:'text-red-400',     ep:'/api/rag/v1/documents/<id>/delete/',  desc:'Delete document'      },
//                     { m:'DELETE', c:'text-red-400',     ep:'/api/rag/v1/documents/clear/',        desc:'Clear all'            },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/queries/',                desc:'Query history'        },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/queries/<id>/execution/', desc:'Execution trace'      },
//                     { m:'POST',   c:'text-emerald-400', ep:'/api/rag/v1/sessions/',               desc:'Create session'       },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/stats/',                  desc:'System stats'         },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/health/',                 desc:'Health check'         },
//                     { m:'GET',    c:'text-sky-400',     ep:'/api/rag/v1/agents/status/',          desc:'Agent status'         },
//                   ].map(r => (
//                     <div key={r.ep} className="flex items-center gap-3 bg-gray-950 border border-gray-800 px-3 py-2 text-xs">
//                       <span className={`${r.c} font-bold w-12 shrink-0`}>{r.m}</span>
//                       <span className="text-gray-300 flex-1 font-mono-custom text-[11px]">{r.ep}</span>
//                       <span className="text-gray-600 text-[10px] hidden sm:block">{r.desc}</span>
//                     </div>
//                   ))}
//                 </div>
//               </Card>
//             </div>
//           )}

//         </main>

//         {/* ═══ FOOTER ═══ */}
//         <footer className="border-t border-gray-800 px-6 py-3 mt-8 flex items-center justify-between">
//           <span className="text-[9px] tracking-[.18em] uppercase text-gray-700">
//             RAGENT/OS · Multi-Agent RAG · v1.0
//           </span>
//           <span className="text-gray-800 text-sm">◈ ◇ ◈</span>
//         </footer>

//       </div>
//     </>
//   );
// }




'use client';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import AxiosInstance from "@/components/AxiosInstance";

/* ─── Global styles ─── */
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; }

  :root {
    --gold:      #c9a84c;
    --gold-lt:   #e8c96e;
    --gold-dk:   #8a6a1f;
    --onyx:      #0a0a0b;
    --charcoal:  #111114;
    --surface:   #16161a;
    --surface2:  #1e1e24;
    --border:    #2a2a32;
    --border-lt: #3a3a46;
    --text:      #e8e6e0;
    --text-muted:#888890;
    --text-dim:  #444450;
    --emerald:   #2dd4a0;
    --sapphire:  #5b9cf6;
    --ruby:      #f06080;
    --amber:     #f0a030;
  }

  body { background: var(--onyx); }

  .font-serif    { font-family: 'Instrument Serif', Georgia, serif; }
  .font-sans     { font-family: 'Space Grotesk', sans-serif; }
  .font-mono     { font-family: 'JetBrains Mono', monospace; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: var(--surface); }
  ::-webkit-scrollbar-thumb { background: var(--gold-dk); border-radius: 2px; }

  /* Animations */
  @keyframes fadeUp   { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  @keyframes fadeIn   { from { opacity:0; } to { opacity:1; } }
  @keyframes spinCW   { to { transform: rotate(360deg); } }
  @keyframes pulse    { 0%,100%{ opacity:1; } 50%{ opacity:.4; } }
  @keyframes shimmer  { 0%{background-position:-400% 0} 100%{background-position:400% 0} }
  @keyframes goldGlow { 0%,100%{ box-shadow:0 0 8px #c9a84c30; } 50%{ box-shadow:0 0 20px #c9a84c60; } }
  @keyframes scanline {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
  }

  .anim-fade-up  { animation: fadeUp .35s cubic-bezier(.2,.8,.4,1) forwards; }
  .anim-fade-in  { animation: fadeIn .25s ease forwards; }
  .anim-spin     { animation: spinCW .7s linear infinite; }
  .anim-pulse    { animation: pulse 2s ease infinite; }
  .anim-shimmer  {
    background: linear-gradient(90deg, var(--gold-dk) 0%, var(--gold-lt) 40%, var(--gold) 50%, var(--gold-lt) 60%, var(--gold-dk) 100%);
    background-size: 400% 100%;
    animation: shimmer 2.5s linear infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .anim-glow     { animation: goldGlow 3s ease infinite; }

  /* Gold gradient text */
  .gold-text {
    background: linear-gradient(135deg, var(--gold-lt) 0%, var(--gold) 50%, var(--gold-dk) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Noise texture overlay */
  .noise-overlay {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    opacity: .025;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
    background-size: 180px;
  }

  /* Gold border card */
  .card-gold {
    background: linear-gradient(135deg, var(--surface) 0%, #1a1a1f 100%);
    border: 1px solid var(--border);
    position: relative;
  }
  .card-gold::before {
    content: '';
    position: absolute; inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(135deg, var(--gold-dk), transparent 50%, var(--gold-dk));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }

  /* Button styles */
  .btn-gold {
    background: linear-gradient(135deg, var(--gold-dk) 0%, var(--gold) 50%, var(--gold-lt) 100%);
    color: var(--onyx);
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    font-size: .7rem;
    border: none;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all .2s;
  }
  .btn-gold::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,.15) 50%, transparent 100%);
    transform: translateX(-100%);
    transition: transform .3s;
  }
  .btn-gold:hover::after { transform: translateX(100%); }
  .btn-gold:hover { box-shadow: 0 0 24px #c9a84c50, 0 4px 16px #00000080; transform: translateY(-1px); }
  .btn-gold:active { transform: translateY(0); }
  .btn-gold:disabled { background: var(--surface2); color: var(--text-dim); cursor: not-allowed; box-shadow: none; transform: none; }

  .btn-ghost {
    background: transparent;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    font-size: .65rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    border: 1px solid var(--border);
    cursor: pointer;
    transition: all .2s;
  }
  .btn-ghost:hover { border-color: var(--gold); color: var(--gold); background: #c9a84c08; }

  .btn-danger {
    background: transparent;
    color: var(--ruby);
    font-family: 'JetBrains Mono', monospace;
    font-size: .65rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    border: 1px solid #f0608030;
    cursor: pointer;
    transition: all .2s;
  }
  .btn-danger:hover { border-color: var(--ruby); background: #f0608012; }

  .btn-emerald {
    background: linear-gradient(135deg, #1a5c45 0%, #2dd4a0 100%);
    color: var(--onyx);
    font-weight: 700;
    font-size: .65rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    border: none;
    cursor: pointer;
    transition: all .2s;
  }
  .btn-emerald:hover { box-shadow: 0 0 20px #2dd4a040; transform: translateY(-1px); }

  .btn-ruby {
    background: linear-gradient(135deg, #5c1a2a 0%, #f06080 100%);
    color: #fff;
    font-weight: 700;
    font-size: .65rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    border: none;
    cursor: pointer;
    transition: all .2s;
  }
  .btn-ruby:hover { box-shadow: 0 0 20px #f0608040; transform: translateY(-1px); }

  /* Input */
  .inp {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: .8rem;
    outline: none;
    transition: border-color .2s, box-shadow .2s;
    width: 100%;
  }
  .inp:focus {
    border-color: var(--gold);
    box-shadow: 0 0 0 3px #c9a84c15;
  }
  .inp::placeholder { color: var(--text-dim); }

  /* Section divider label */
  .sect-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: .6rem;
    letter-spacing: .22em;
    text-transform: uppercase;
    color: var(--text-dim);
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 14px;
  }
  .sect-label::after {
    content: '';
    flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border) 0%, transparent 100%);
  }

  /* Badge */
  .badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: .6rem;
    letter-spacing: .14em;
    text-transform: uppercase;
    padding: 3px 8px;
    border: 1px solid;
    display: inline-flex; align-items: center;
  }

  /* Step trace */
  .trace-step {
    border-left: 2px solid;
    padding-left: 14px;
    transition: opacity .2s;
  }

  /* Tab */
  .tab-btn {
    font-family: 'Space Grotesk', sans-serif;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: 14px 20px;
    background: transparent;
    border: none; border-bottom: 2px solid transparent;
    color: var(--text-dim);
    cursor: pointer;
    transition: all .2s;
    white-space: nowrap;
  }
  .tab-btn:hover { color: var(--text-muted); }
  .tab-btn.active { color: var(--gold); border-bottom-color: var(--gold); }

  /* Stat card */
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 16px 20px;
    display: flex; flex-direction: column;
    gap: 4px;
    position: relative; overflow: hidden;
    transition: border-color .2s;
  }
  .stat-card:hover { border-color: var(--border-lt); }
  .stat-card::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  }

  /* Progress bar */
  .prog-bar {
    height: 3px; background: var(--surface2); overflow: hidden; border-radius: 2px;
  }
  .prog-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold-dk), var(--gold-lt));
    animation: shimmer 2s linear infinite;
    background-size: 200% 100%;
    transition: width .3s;
  }

  /* Health dot */
  .h-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  }
  .h-dot.ok  { background: var(--emerald); box-shadow: 0 0 8px var(--emerald); }
  .h-dot.err { background: var(--ruby);    box-shadow: 0 0 8px var(--ruby); }
  .h-dot.unk { background: var(--text-dim); }

  /* Toast */
  .toast {
    font-family: 'JetBrains Mono', monospace;
    font-size: .7rem;
    padding: 10px 16px;
    display: flex; align-items: center; gap: 10px;
    border-left: 3px solid;
    animation: fadeUp .25s ease;
    min-width: 220px; max-width: 340px;
  }

  /* RL Gauge */
  .rl-gauge {
    width: 100%; height: 6px;
    background: var(--surface2);
    border-radius: 3px; overflow: hidden;
  }
  .rl-gauge-fill {
    height: 100%; border-radius: 3px;
    background: linear-gradient(90deg, var(--gold-dk), var(--gold-lt));
    transition: width .6s cubic-bezier(.4,0,.2,1);
  }

  /* Feedback row */
  .fb-btn {
    padding: 6px 14px;
    border-radius: 2px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600; font-size: .7rem;
    letter-spacing: .06em;
    cursor: pointer; border: 1px solid;
    transition: all .2s;
  }
  .fb-btn.pos { border-color: #2dd4a040; color: var(--emerald); background: #2dd4a008; }
  .fb-btn.pos:hover { background: #2dd4a020; border-color: var(--emerald); box-shadow: 0 0 12px #2dd4a030; }
  .fb-btn.neg { border-color: #f0608040; color: var(--ruby); background: #f0608008; }
  .fb-btn.neg:hover { background: #f0608020; border-color: var(--ruby); box-shadow: 0 0 12px #f0608030; }
  .fb-btn.active-pos { background: #2dd4a025; border-color: var(--emerald); }
  .fb-btn.active-neg { background: #f0608025; border-color: var(--ruby); }

  /* Luxury divider */
  .lux-divider {
    border: none; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-dk), transparent);
    margin: 24px 0;
  }

  /* Q-value bar */
  .qval-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .qval-label { font-family: 'JetBrains Mono', monospace; font-size: .6rem; color: var(--text-muted); width: 130px; flex-shrink: 0; }
  .qval-bar-wrap { flex: 1; height: 4px; background: var(--surface2); border-radius: 2px; overflow: hidden; }
  .qval-bar-fill { height: 100%; border-radius: 2px; background: var(--gold); transition: width .5s; }
  .qval-num { font-family: 'JetBrains Mono', monospace; font-size: .6rem; color: var(--gold); width: 40px; text-align: right; }
`;

/* ─── Toast ─── */
let _setToasts = null;
const toast = {
  _push(type, msg) {
    const id = Date.now();
    _setToasts?.(p => [...p, { id, type, msg }]);
    setTimeout(() => _setToasts?.(p => p.filter(t => t.id !== id)), 4000);
  },
  success: m => toast._push('success', m),
  error:   m => toast._push('error', m),
  warn:    m => toast._push('warn', m),
  info:    m => toast._push('info', m),
};
const TOAST_CFG = {
  success: { bg: '#0d1f17', border: '#2dd4a0', color: '#2dd4a0', icon: '✓' },
  error:   { bg: '#1f0d12', border: '#f06080', color: '#f06080', icon: '✕' },
  warn:    { bg: '#1f180d', border: '#f0a030', color: '#f0a030', icon: '!' },
  info:    { bg: '#0d141f', border: '#5b9cf6', color: '#5b9cf6', icon: 'i' },
};
function Toasts() {
  const [toasts, setToasts] = useState([]);
  useEffect(() => { _setToasts = setToasts; }, []);
  return (
    <div style={{ position:'fixed', bottom:20, right:20, zIndex:9999, display:'flex', flexDirection:'column', gap:8, pointerEvents:'none' }}>
      {toasts.map(t => {
        const c = TOAST_CFG[t.type];
        return (
          <div key={t.id} className="toast" style={{ background: c.bg, borderLeftColor: c.border, color: c.color }}>
            <span style={{ fontWeight: 700 }}>[{c.icon}]</span> {t.msg}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Helpers ─── */
const fmt = {
  bytes: b => { if (!b) return '0 B'; const k=1024,s=['B','KB','MB','GB'],i=Math.floor(Math.log(b)/Math.log(k)); return (b/k**i).toFixed(1)+' '+s[i]; },
  secs:  v => v ? v.toFixed(2)+'s' : '—',
  pct:   v => v != null ? (v*100).toFixed(0)+'%' : '—',
  date:  d => d ? new Date(d).toLocaleString() : '—',
  cut:   (s,n=80) => s && s.length>n ? s.slice(0,n)+'…' : (s||''),
  num:   v => v != null ? (typeof v==='number' ? v.toFixed(4) : v) : '—',
};

const SRC_MAP = {
  rl_multi_agent:    { label:'RL Agent',   gold:true },
  chromadb:          { label:'ChromaDB',   color:'var(--sapphire)' },
  internet:          { label:'Web',        color:'var(--emerald)'  },
  general_knowledge: { label:'AI Memory',  color:'#a855f7'         },
  coordinator_agent: { label:'Agent',      color:'var(--amber)'    },
  error:             { label:'Error',      color:'var(--ruby)'     },
};
const srcInfo = s => SRC_MAP[s] || SRC_MAP.coordinator_agent;

const STEP_COLORS = {
  THOUGHT:     { border:'#a855f7', text:'#c084fc', bg:'#a855f708' },
  ACTION:      { border:'var(--gold)', text:'var(--gold)', bg:'#c9a84c08' },
  OBSERVATION: { border:'var(--emerald)', text:'var(--emerald)', bg:'#2dd4a008' },
  ERROR:       { border:'var(--ruby)', text:'var(--ruby)', bg:'#f0608008' },
};

/* ─── UI Primitives ─── */
function SectLabel({ children }) {
  return <div className="sect-label"><span>{children}</span></div>;
}

function Badge({ children, color, gold }) {
  const style = gold
    ? { borderColor:'var(--gold)', color:'var(--gold)', background:'#c9a84c10' }
    : { borderColor: color+'40', color, background: color+'10' };
  return <span className="badge" style={style}>{children}</span>;
}

function Card({ children, style={}, className='' }) {
  return (
    <div className={`card-gold ${className}`} style={{ padding:20, ...style }}>
      {children}
    </div>
  );
}

function GoldBtn({ children, loading, loadText='Processing…', style={}, ...props }) {
  return (
    <button className="btn-gold" style={{ padding:'13px 28px', ...style }} {...props}>
      {loading ? (
        <span style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'center' }}>
          <span className="anim-spin" style={{ width:13, height:13, border:'2px solid #00000030', borderTop:'2px solid #000', borderRadius:'50%', display:'inline-block' }} />
          {loadText}
        </span>
      ) : children}
    </button>
  );
}

function HDot({ status }) {
  const cls = status==='operational' ? 'ok' : status==='error' ? 'err' : 'unk';
  return <span className={`h-dot ${cls}`} />;
}

/* ═══════════════════════════════════ MAIN ═══════════════════════════════════ */
export default function RAGSystem() {
  const [mounted, setMounted] = useState(false);
  const [tab, setTab]         = useState('query');
  const [loading, setLoading] = useState(false);

  /* Query */
  const [queryText,   setQueryText]   = useState('');
  const [strategy,    setStrategy]    = useState('auto');
  const [topK,        setTopK]        = useState(5);
  const [selectedDoc, setSelectedDoc] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [agentTrace,  setAgentTrace]  = useState(null);
  const [feedback,    setFeedback]    = useState(null); // 'positive'|'negative'|null
  const [rlQueryId,   setRlQueryId]   = useState(null);

  /* Upload */
  const [file,      setFile]      = useState(null);
  const [uploadPct, setUploadPct] = useState(0);
  const [dragging,  setDragging]  = useState(false);
  const fileRef = useRef();

  /* Data */
  const [documents,    setDocuments]    = useState([]);
  const [queryHistory, setQueryHistory] = useState([]);
  const [stats,        setStats]        = useState({ total_documents:0, total_queries:0, total_chunks:0, average_processing_time:0, strategy_distribution:{} });
  const [health,       setHealth]       = useState(null);
  const [agentStatus,  setAgentStatus]  = useState(null);

  /* RL */
  const [rlStats,    setRlStats]    = useState(null);
  const [rlTrace,    setRlTrace]    = useState(null);
  const [rlTraining, setRlTraining] = useState(false);

  /* Init */
  useEffect(() => {
    setMounted(true);
    fetchDocuments(); fetchStats(); fetchHealth();
    try { const s = localStorage.getItem('rag_qh'); if(s) setQueryHistory(JSON.parse(s)); } catch(_){}
  }, []);

  useEffect(() => {
    const h = e => { if ((e.ctrlKey||e.metaKey) && e.key==='Enter') submitQuery(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [queryText, strategy, topK, selectedDoc]);

  /* ─ API ─ */
  const fetchDocuments   = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/documents/'); setDocuments(r.data.documents||[]); } catch(_){} };
  const fetchStats       = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/stats/');     setStats(r.data); } catch(_){} };
  const fetchHealth      = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/health/');    setHealth(r.data); } catch(_){ setHealth({ status:'error', components:{} }); } };
  const fetchAgentStatus = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/agents/status/'); setAgentStatus(r.data); } catch(_){} };
  const fetchRlStats     = async () => { try { const r = await AxiosInstance.get('/api/rag/v1/rl/stats/');  setRlStats(r.data); } catch(_){} };

  const fetchRlTrace = async (qid) => {
    try {
      const r = await AxiosInstance.get(`/api/rag/v1/rl/trace/${qid}/`);
      setRlTrace(r.data);
    } catch(_){}
  };

  /* ─ Submit Query ─ */
  const submitQuery = async () => {
    if (!queryText.trim()) { toast.warn('Enter a query first'); return; }
    setLoading(true); setQueryResult(null); setAgentTrace(null);
    setFeedback(null); setRlQueryId(null); setRlTrace(null);
    try {
      const r = await AxiosInstance.post('/api/rag/v1/query/', {
        query: queryText, strategy, top_k: topK, document_id: selectedDoc||null,
      });
      const d = r.data;
      setQueryResult(d);

      const rlMeta = d.rl_metadata || {};
      if (rlMeta.query_id) {
        setRlQueryId(rlMeta.query_id);
        fetchRlTrace(rlMeta.query_id);
      }

      if (d.execution_steps?.length) {
        setAgentTrace({
          steps: d.execution_steps, agent_type: d.agent_type||'rl_coordinator',
          source: d.source||'unknown', internet_sources: d.internet_sources||[],
          rl_metadata: rlMeta,
        });
      }

      const entry = {
        id: Date.now().toString(), query: d.query, answer: d.answer,
        strategy: d.strategy_used, processing_time: d.processing_time,
        confidence_score: d.confidence_score, agent_type: d.agent_type,
        source: d.source, steps: d.execution_steps?.length||0,
        rl_metadata: rlMeta, timestamp: new Date().toISOString(),
      };
      setQueryHistory(prev => {
        const next = [entry, ...prev.slice(0,49)];
        localStorage.setItem('rag_qh', JSON.stringify(next));
        return next;
      });
      fetchStats();
      toast.success('Query completed');
    } catch(e) { toast.error(e.response?.data?.error||'Query failed'); }
    finally { setLoading(false); }
  };

  /* ─ Feedback ─ */
  const submitFeedback = async (fb) => {
    if (!rlQueryId) { toast.warn('No RL query ID available'); return; }
    setFeedback(fb);
    try {
      await AxiosInstance.post('/api/rag/v1/rl/feedback/', { query_id: rlQueryId, feedback: fb });
      toast.success(`Feedback "${fb}" sent — Q-table updated`);
      fetchRlStats();
    } catch(e) { toast.error('Feedback failed'); setFeedback(null); }
  };

  /* ─ RL Train ─ */
  const triggerRlTrain = async (batchSize=32) => {
    setRlTraining(true);
    try {
      const r = await AxiosInstance.post('/api/rag/v1/rl/train/', { batch_size: batchSize });
      toast.success(`Replay training: ${r.data.new_updates} Q-updates`);
      fetchRlStats();
    } catch(e) { toast.error('Training failed'); }
    finally { setRlTraining(false); }
  };

  /* ─ Upload ─ */
  const submitUpload = async () => {
    if (!file) { toast.warn('Select a file first'); return; }
    const fd = new FormData(); fd.append('file', file);
    setLoading(true); setUploadPct(0);
    try {
      const r = await AxiosInstance.post('/api/rag/v1/upload/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: e => setUploadPct(e.total ? Math.round(e.loaded*100/e.total) : 50),
      });
      toast.success(`Ingested ${r.data.chunks_created} chunks`);
      setFile(null); setUploadPct(0); fetchDocuments(); fetchStats();
    } catch(e) { toast.error(e.response?.data?.error||'Upload failed'); }
    finally { setLoading(false); }
  };

  /* ─ Docs ─ */
  const deleteDoc = async (id, name) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try { await AxiosInstance.delete(`/api/rag/v1/documents/${id}/delete/`); toast.success('Removed'); fetchDocuments(); fetchStats(); }
    catch(_) { toast.error('Delete failed'); }
  };
  const clearAll = async () => {
    if (!confirm('Delete ALL documents and vectors?')) return;
    setLoading(true);
    try { await AxiosInstance.delete('/api/rag/v1/documents/clear/'); toast.success('All cleared'); fetchDocuments(); fetchStats(); }
    catch(_) { toast.error('Clear failed'); }
    finally { setLoading(false); }
  };

  /* ─ Drag-drop ─ */
  const onDrop = useCallback(e => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if(f) setFile(f);
  }, []);

  /* ─────────────────── RENDER ─────────────────── */
  const TABS = [
    { id:'query',    label:'Query'         },
    { id:'upload',   label:'Ingest'        },
    { id:'docs',     label:'Library'       },
    { id:'history',  label:'History'       },
    { id:'trace',    label:'Agent Trace'   },
    { id:'rl',       label:'RL Intelligence' },
    { id:'health',   label:'System'        },
  ];

  return (
    <>
      {mounted && <style suppressHydrationWarning>{GLOBAL_CSS}</style>}
      <div className="noise-overlay" suppressHydrationWarning />
      <Toasts />

      <div className="font-sans" style={{ background:'var(--onyx)', minHeight:'100vh', color:'var(--text)', position:'relative', zIndex:1 }}>

        {/* ═══ HEADER ═══ */}
        <header style={{ background:'#0a0a0b', borderBottom:'1px solid var(--border)', position:'sticky', top:0, zIndex:40, backdropFilter:'blur(12px)' }}>
          <div style={{ maxWidth:1400, margin:'0 auto', padding:'0 28px', height:60, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
            <div style={{ display:'flex', alignItems:'center', gap:20 }}>
              {/* Logo mark */}
              <div style={{ position:'relative', width:32, height:32 }}>
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width:32, height:32 }}>
                  <polygon points="16,2 30,10 30,22 16,30 2,22 2,10" stroke="#c9a84c" strokeWidth="1.5" fill="none"/>
                  <polygon points="16,8 24,13 24,19 16,24 8,19 8,13" stroke="#c9a84c60" strokeWidth="1" fill="none"/>
                  <circle cx="16" cy="16" r="3" fill="#c9a84c"/>
                </svg>
              </div>
              <div>
                <div className="font-serif" style={{ fontSize:'1.2rem', letterSpacing:'.04em', lineHeight:1 }}>
                  <span className="gold-text">RAGENT</span>
                  <span style={{ color:'var(--text-dim)', fontWeight:300 }}> Intelligence</span>
                </div>
                <div className="font-mono" style={{ fontSize:'.55rem', letterSpacing:'.2em', color:'var(--text-dim)', textTransform:'uppercase', marginTop:2 }}>
                  RL-Driven Multi-Agent System
                </div>
              </div>
            </div>

            <div style={{ display:'flex', alignItems:'center', gap:20 }}>
              {health && (
                <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                  <HDot status={health.status==='healthy' ? 'operational' : 'error'} />
                  <span className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.14em', textTransform:'uppercase', color:'var(--text-dim)' }}>
                    {health.status}
                  </span>
                </div>
              )}
              <div className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)' }}>
                {mounted ? new Date().toLocaleTimeString() : ''}
              </div>
            </div>
          </div>
        </header>

        {/* ═══ STATS STRIP ═══ */}
        <div style={{ background:'var(--charcoal)', borderBottom:'1px solid var(--border)', padding:'0 28px', overflowX:'auto' }}>
          <div style={{ maxWidth:1400, margin:'0 auto', display:'flex', gap:0 }}>
            {[
              { label:'Documents',  val: stats.total_documents,               color:'var(--gold)',    accent:'var(--gold-dk)'  },
              { label:'Chunks',     val: stats.total_chunks,                   color:'var(--sapphire)',accent:'#1e40af'         },
              { label:'Queries',    val: stats.total_queries,                  color:'var(--emerald)', accent:'#065f46'         },
              { label:'Avg Speed',  val: fmt.secs(stats.average_processing_time), color:'#a855f7',    accent:'#581c87'         },
            ].map((s,i) => (
              <div key={s.label} className="stat-card" style={{ borderRight:'1px solid var(--border)', minWidth:130, flex:'1' }}>
                <div className="font-serif" style={{ fontSize:'1.8rem', color: s.color, lineHeight:1, letterSpacing:'-.02em' }}>{s.val}</div>
                <div className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)', marginTop:4 }}>{s.label}</div>
                <div style={{ position:'absolute', bottom:0, left:0, right:0, height:2, background:`linear-gradient(90deg, ${s.accent}, ${s.color})` }} />
              </div>
            ))}
            {Object.entries(stats.strategy_distribution||{}).map(([k,v]) => (
              <div key={k} className="stat-card" style={{ borderRight:'1px solid var(--border)', minWidth:100, flex:'1' }}>
                <div className="font-serif" style={{ fontSize:'1.8rem', color:'var(--text-muted)', lineHeight:1 }}>{v}</div>
                <div className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)', marginTop:4 }}>{k}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ TABS ═══ */}
        <div style={{ background:'var(--charcoal)', borderBottom:'1px solid var(--border)', overflowX:'auto' }}>
          <div style={{ maxWidth:1400, margin:'0 auto', padding:'0 28px', display:'flex' }}>
            {TABS.map(t => (
              <button key={t.id} className={`tab-btn ${tab===t.id?'active':''}`}
                onClick={() => {
                  setTab(t.id);
                  if(t.id==='health'){ fetchHealth(); fetchAgentStatus(); }
                  if(t.id==='rl')   { fetchRlStats(); }
                }}>
                {t.label}
                {t.id==='rl' && <span style={{ marginLeft:6, background:'var(--gold)', color:'var(--onyx)', fontSize:'.5rem', fontWeight:700, padding:'1px 5px', borderRadius:2 }}>NEW</span>}
              </button>
            ))}
          </div>
        </div>

        {/* ═══ CONTENT ═══ */}
        <main style={{ maxWidth:1400, margin:'0 auto', padding:'28px 28px 60px' }}>

          {/* ── QUERY TAB ── */}
          {tab==='query' && (
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, alignItems:'start' }}>

              {/* Left */}
              <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                <Card>
                  <SectLabel>Query Input</SectLabel>

                  <div style={{ marginBottom:14 }}>
                    <label className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', display:'block', marginBottom:6 }}>Your Question</label>
                    <textarea
                      className="inp"
                      rows={5} value={queryText}
                      onChange={e => setQueryText(e.target.value)}
                      placeholder="Ask anything about your documents…"
                      style={{ padding:'12px 14px', resize:'vertical', lineHeight:1.6 }}
                    />
                  </div>

                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
                    <div>
                      <label className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', display:'block', marginBottom:6 }}>Strategy</label>
                      <select className="inp" value={strategy} onChange={e=>setStrategy(e.target.value)} style={{ padding:'10px 12px', cursor:'pointer' }}>
                        <option value="simple">Simple</option>
                        <option value="agentic">Agentic (ReAct)</option>
                        <option value="multi_agent">Multi-Agent</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>
                    <div>
                      <label className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', display:'block', marginBottom:6 }}>Top-K Chunks</label>
                      <input className="inp" type="number" min={1} max={50} value={topK} onChange={e=>setTopK(+e.target.value)} style={{ padding:'10px 12px' }}/>
                    </div>
                  </div>

                  <div style={{ marginBottom:20 }}>
                    <label className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', display:'block', marginBottom:6 }}>Document Filter</label>
                    <select className="inp" value={selectedDoc} onChange={e=>setSelectedDoc(e.target.value)} style={{ padding:'10px 12px', cursor:'pointer' }}>
                      <option value="">All documents</option>
                      {documents.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
                    </select>
                  </div>

                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <GoldBtn loading={loading} loadText="Processing…" onClick={submitQuery} disabled={loading} style={{ flex:1 }}>
                      ▶ Execute Query
                    </GoldBtn>
                    <span className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)', whiteSpace:'nowrap' }}>Ctrl+↵</span>
                  </div>
                </Card>

                {/* Strategy guide */}
                <Card>
                  <SectLabel>Strategy Guide</SectLabel>
                  <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
                    {[
                      { s:'simple',      c:'var(--sapphire)', d:'Direct vector search. Fastest, no agent loop.'         },
                      { s:'agentic',     c:'var(--gold)',     d:'ReAct loop: Thought → Action → Observation cycles.'    },
                      { s:'multi_agent', c:'#a855f7',         d:'Parallel sub-agents with coordinator synthesis.'       },
                      { s:'auto',        c:'var(--emerald)',  d:'RL agent auto-selects optimal strategy per query.'     },
                    ].map(r => (
                      <div key={r.s} style={{ display:'flex', gap:12, opacity: strategy===r.s ? 1 : .3, transition:'opacity .2s' }}>
                        <span className="font-mono" style={{ color:r.c, fontWeight:700, fontSize:'.7rem', width:80, flexShrink:0 }}>{r.s}</span>
                        <span style={{ fontSize:'.75rem', color:'var(--text-muted)', lineHeight:1.5 }}>{r.d}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Right */}
              <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                {queryResult ? (
                  <>
                    <Card>
                      {/* Source & badges */}
                      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:16, flexWrap:'wrap', gap:8 }}>
                        <SectLabel>Answer</SectLabel>
                        <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
                          {queryResult.source && (
                            <Badge color={srcInfo(queryResult.source).color} gold={srcInfo(queryResult.source).gold}>
                              {srcInfo(queryResult.source).label}
                            </Badge>
                          )}
                          <Badge color="var(--gold)">{fmt.secs(queryResult.processing_time)}</Badge>
                          {queryResult.confidence_score != null && <Badge color="var(--emerald)">{fmt.pct(queryResult.confidence_score)}</Badge>}
                          {queryResult.rl_metadata?.last_action && <Badge color="var(--amber)">{queryResult.rl_metadata.last_action}</Badge>}
                        </div>
                      </div>

                      {/* Answer text */}
                      <div style={{
                        background:'var(--surface2)', borderLeft:'3px solid var(--gold)',
                        padding:'16px 18px', fontSize:'.85rem', color:'var(--text)', lineHeight:1.75,
                        whiteSpace:'pre-wrap', marginBottom:16,
                      }}>
                        {queryResult.answer}
                      </div>

                      {/* Meta */}
                      <div style={{ display:'flex', flexWrap:'wrap', gap:16, fontSize:'.72rem', color:'var(--text-muted)', marginBottom:16 }}>
                        <span>Strategy: <strong style={{ color:'var(--text)' }}>{queryResult.strategy_used}</strong></span>
                        <span>Chunks: <strong style={{ color:'var(--text)' }}>{queryResult.retrieved_chunks?.length||0}</strong></span>
                        {queryResult.agent_type && <span>Agent: <strong style={{ color:'var(--text)' }}>{queryResult.agent_type}</strong></span>}
                      </div>

                      {/* RL Metadata Panel */}
                      {queryResult.rl_metadata && Object.keys(queryResult.rl_metadata).length > 0 && (
                        <div style={{ background:'#c9a84c08', border:'1px solid var(--gold-dk)', padding:'12px 14px', marginBottom:16 }}>
                          <div className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--gold)', marginBottom:8 }}>
                            RL Decision Metadata
                          </div>
                          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
                            {[
                              { k:'Steps Taken',     v: queryResult.rl_metadata.steps_taken },
                              { k:'Last Action',     v: queryResult.rl_metadata.last_action },
                              { k:'Last Reward',     v: queryResult.rl_metadata.last_reward != null ? queryResult.rl_metadata.last_reward.toFixed(3) : '—' },
                              { k:'Epsilon',         v: queryResult.rl_metadata.epsilon },
                              { k:'States Learned',  v: queryResult.rl_metadata.states_learned },
                              { k:'Query ID',        v: fmt.cut(queryResult.rl_metadata.query_id||'',18) },
                            ].map(item => (
                              <div key={item.k}>
                                <div className="font-mono" style={{ fontSize:'.56rem', letterSpacing:'.12em', textTransform:'uppercase', color:'var(--text-dim)' }}>{item.k}</div>
                                <div className="font-mono" style={{ fontSize:'.72rem', color:'var(--gold-lt)', marginTop:2 }}>{item.v ?? '—'}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Feedback buttons */}
                      {rlQueryId && (
                        <div>
                          <div className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', marginBottom:8 }}>
                            Rate this answer — updates Q-table
                          </div>
                          <div style={{ display:'flex', gap:10 }}>
                            <button
                              className={`fb-btn pos ${feedback==='positive'?'active-pos':''}`}
                              onClick={() => submitFeedback('positive')}
                              disabled={!!feedback}
                            >
                              ↑ Helpful
                            </button>
                            <button
                              className={`fb-btn neg ${feedback==='negative'?'active-neg':''}`}
                              onClick={() => submitFeedback('negative')}
                              disabled={!!feedback}
                            >
                              ↓ Not Helpful
                            </button>
                            {feedback && (
                              <span className="font-mono" style={{ fontSize:'.62rem', color: feedback==='positive' ? 'var(--emerald)' : 'var(--ruby)', display:'flex', alignItems:'center' }}>
                                ✓ Feedback recorded
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {agentTrace && (
                        <div style={{ marginTop:14 }}>
                          <button className="btn-ghost" style={{ padding:'7px 14px' }} onClick={() => setTab('trace')}>
                            View Agent Trace →
                          </button>
                        </div>
                      )}
                    </Card>

                    {/* Chunks */}
                    {queryResult.retrieved_chunks?.length > 0 && (
                      <Card>
                        <SectLabel>Retrieved Chunks ({queryResult.retrieved_chunks.length})</SectLabel>
                        <div style={{ display:'flex', flexDirection:'column', gap:8, maxHeight:220, overflowY:'auto' }}>
                          {queryResult.retrieved_chunks.slice(0,5).map((c,i) => (
                            <div key={i} style={{ borderLeft:'2px solid var(--border-lt)', paddingLeft:12, paddingTop:6, paddingBottom:6, fontSize:'.73rem', color:'var(--text-muted)', lineHeight:1.55 }}>
                              <span style={{ color:'var(--gold)', fontWeight:700, marginRight:8 }}>#{i+1}</span>
                              {fmt.cut(typeof c==='string' ? c : (c.content||JSON.stringify(c)), 140)}
                            </div>
                          ))}
                          {queryResult.retrieved_chunks.length > 5 && (
                            <p className="font-mono" style={{ fontSize:'.62rem', color:'var(--text-dim)', textAlign:'center', padding:'4px 0' }}>
                              +{queryResult.retrieved_chunks.length-5} more chunks
                            </p>
                          )}
                        </div>
                      </Card>
                    )}
                  </>
                ) : (
                  <Card style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:320, gap:16 }}>
                    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width:60, opacity:.15 }}>
                      <polygon points="32,4 60,20 60,44 32,60 4,44 4,20" stroke="#c9a84c" strokeWidth="1.5" fill="none"/>
                      <polygon points="32,16 48,26 48,38 32,48 16,38 16,26" stroke="#c9a84c" strokeWidth="1" fill="none"/>
                      <circle cx="32" cy="32" r="6" stroke="#c9a84c" strokeWidth="1" fill="none"/>
                    </svg>
                    <p className="font-mono" style={{ fontSize:'.65rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)' }}>
                      Awaiting query execution
                    </p>
                  </Card>
                )}
              </div>
            </div>
          )}

          {/* ── INGEST TAB ── */}
          {tab==='upload' && (
            <div style={{ maxWidth:560, margin:'0 auto', display:'flex', flexDirection:'column', gap:16 }}>
              <Card>
                <SectLabel>Document Ingestion</SectLabel>

                <div
                  onClick={() => fileRef.current?.click()}
                  onDragOver={e => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={onDrop}
                  style={{
                    border:`2px dashed ${dragging ? 'var(--gold)' : 'var(--border-lt)'}`,
                    padding:'48px 24px', textAlign:'center', cursor:'pointer',
                    background: dragging ? '#c9a84c08' : 'transparent', transition:'all .2s',
                  }}
                >
                  <input ref={fileRef} type="file" accept=".pdf,.txt,.docx,.csv,.tsv" className="hidden" onChange={e=>setFile(e.target.files?.[0]||null)} />
                  <div style={{ fontSize:'2.5rem', color:'var(--text-dim)', marginBottom:12 }}>⬆</div>
                  <p style={{ color: file ? 'var(--gold-lt)' : 'var(--text-muted)', marginBottom:6, fontSize:'.9rem' }}>
                    {file ? file.name : 'Drop file or click to browse'}
                  </p>
                  <p className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.14em', textTransform:'uppercase', color:'var(--text-dim)' }}>
                    PDF · TXT · DOCX · CSV · TSV
                  </p>
                </div>

                {file && (
                  <div style={{ marginTop:12, background:'var(--surface2)', border:'1px solid var(--border)', padding:'12px 16px', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                    <div>
                      <p style={{ fontSize:'.85rem', color:'var(--text)' }}>{file.name}</p>
                      <p className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)', marginTop:4 }}>{fmt.bytes(file.size)}</p>
                    </div>
                    <button onClick={() => setFile(null)} style={{ color:'var(--text-dim)', background:'none', border:'none', cursor:'pointer', fontSize:'1.1rem', transition:'color .2s' }}
                      onMouseEnter={e=>e.target.style.color='var(--ruby)'}
                      onMouseLeave={e=>e.target.style.color='var(--text-dim)'}>✕</button>
                  </div>
                )}

                {uploadPct > 0 && (
                  <div style={{ marginTop:12 }}>
                    <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
                      <span className="font-mono" style={{ fontSize:'.62rem', color:'var(--text-dim)' }}>Uploading…</span>
                      <span className="font-mono" style={{ fontSize:'.62rem', color:'var(--gold)' }}>{uploadPct}%</span>
                    </div>
                    <div className="prog-bar"><div className="prog-fill" style={{ width:`${uploadPct}%` }} /></div>
                  </div>
                )}

                <div style={{ marginTop:20 }}>
                  <GoldBtn loading={loading} loadText="Ingesting…" onClick={submitUpload} disabled={!file||loading} style={{ width:'100%' }}>
                    ▶ Ingest Document
                  </GoldBtn>
                </div>
              </Card>

              <Card>
                <SectLabel>Processing Pipeline</SectLabel>
                {['Validate & parse file','Extract raw text','Split into chunks','Generate embeddings','Store in ChromaDB','Index metadata in PostgreSQL'].map((s,i) => (
                  <div key={i} style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 0', borderBottom:'1px solid var(--border)', fontSize:'.78rem', color:'var(--text-muted)' }}>
                    <span style={{ color:'var(--gold)', fontWeight:700, width:20, textAlign:'center', flexShrink:0 }}>{i+1}</span>
                    {s}
                  </div>
                ))}
              </Card>
            </div>
          )}

          {/* ── DOCS TAB ── */}
          {tab==='docs' && (
            <div>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:20 }}>
                <h2 className="font-serif" style={{ fontSize:'1.4rem', color:'var(--text)' }}>
                  Library <span style={{ color:'var(--text-dim)', fontSize:'1rem' }}>({documents.length})</span>
                </h2>
                <div style={{ display:'flex', gap:10 }}>
                  <button className="btn-ghost" style={{ padding:'8px 16px' }} onClick={fetchDocuments}>↻ Refresh</button>
                  {documents.length > 0 && <button className="btn-danger" style={{ padding:'8px 16px' }} onClick={clearAll}>Clear All</button>}
                </div>
              </div>

              {documents.length > 0 ? (
                <Card style={{ padding:0, overflow:'hidden' }}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 90px 70px 100px 110px 32px', gap:12, padding:'10px 20px', borderBottom:'1px solid var(--border)' }}>
                    {['Filename','Size','Chunks','Status','Uploaded',''].map(h => (
                      <span key={h} className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)' }}>{h}</span>
                    ))}
                  </div>
                  {documents.map(d => (
                    <div key={d.id} style={{ display:'grid', gridTemplateColumns:'1fr 90px 70px 100px 110px 32px', gap:12, alignItems:'center', padding:'14px 20px', borderBottom:'1px solid var(--border)', transition:'background .15s' }}
                      onMouseEnter={e=>e.currentTarget.style.background='var(--surface2)'}
                      onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                      <span style={{ fontSize:'.82rem', color:'var(--text)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{d.filename}</span>
                      <span className="font-mono" style={{ fontSize:'.7rem', color:'var(--text-muted)' }}>{fmt.bytes(d.size)}</span>
                      <span className="font-mono" style={{ fontSize:'.7rem', color:'var(--sapphire)', fontWeight:700 }}>{d.chunks_count}</span>
                      <span>
                        <Badge color={d.status==='completed'?'var(--emerald)':d.status==='failed'?'var(--ruby)':'var(--amber)'}>
                          {d.status}
                        </Badge>
                      </span>
                      <span className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)' }}>{new Date(d.uploaded_at).toLocaleDateString()}</span>
                      <button onClick={() => deleteDoc(d.id, d.filename)} style={{ color:'var(--text-dim)', background:'none', border:'none', cursor:'pointer', fontSize:'.8rem', transition:'color .2s' }}
                        onMouseEnter={e=>e.target.style.color='var(--ruby)'}
                        onMouseLeave={e=>e.target.style.color='var(--text-dim)'}>✕</button>
                    </div>
                  ))}
                </Card>
              ) : (
                <Card style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'80px 20px', gap:16 }}>
                  <span style={{ fontSize:'3rem', color:'var(--text-dim)' }}>◫</span>
                  <p style={{ color:'var(--text-muted)', fontSize:'.9rem' }}>No documents ingested yet</p>
                  <GoldBtn onClick={()=>setTab('upload')} style={{ padding:'11px 28px' }}>Ingest First Document</GoldBtn>
                </Card>
              )}
            </div>
          )}

          {/* ── HISTORY TAB ── */}
          {tab==='history' && (
            <div>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:20 }}>
                <h2 className="font-serif" style={{ fontSize:'1.4rem', color:'var(--text)' }}>
                  Query History <span style={{ color:'var(--text-dim)', fontSize:'1rem' }}>({queryHistory.length})</span>
                </h2>
                {queryHistory.length > 0 && (
                  <button className="btn-danger" style={{ padding:'8px 16px' }}
                    onClick={() => { setQueryHistory([]); localStorage.removeItem('rag_qh'); toast.info('History cleared'); }}>
                    Clear History
                  </button>
                )}
              </div>

              {queryHistory.length > 0 ? (
                <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                  {queryHistory.map(h => (
                    <div key={h.id} className="card-gold anim-fade-up" style={{ padding:'16px 20px', borderLeft:'3px solid var(--border)', transition:'border-color .2s' }}
                      onMouseEnter={e=>e.currentTarget.style.borderLeftColor='var(--gold)'}
                      onMouseLeave={e=>e.currentTarget.style.borderLeftColor='var(--border)'}>
                      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12, flexWrap:'wrap', gap:8 }}>
                        <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
                          {h.source && <Badge color={srcInfo(h.source).color} gold={srcInfo(h.source).gold}>{srcInfo(h.source).label}</Badge>}
                          <Badge color="var(--gold)">{h.strategy}</Badge>
                          <Badge color="var(--sapphire)">{fmt.secs(h.processing_time)}</Badge>
                          {h.confidence_score && <Badge color="var(--emerald)">{fmt.pct(h.confidence_score)}</Badge>}
                          {h.steps>0 && <Badge color="#a855f7">{h.steps} steps</Badge>}
                          {h.rl_metadata?.last_action && <Badge color="var(--amber)">{h.rl_metadata.last_action}</Badge>}
                        </div>
                        <span className="font-mono" style={{ fontSize:'.62rem', color:'var(--text-dim)' }}>{fmt.date(h.timestamp)}</span>
                      </div>
                      <p style={{ color:'var(--gold-lt)', marginBottom:8, fontSize:'.82rem', lineHeight:1.5 }}>Q: {fmt.cut(h.query, 100)}</p>
                      <p style={{ color:'var(--text-muted)', fontSize:'.76rem', lineHeight:1.6 }}>A: {fmt.cut(h.answer, 200)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <Card style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'80px 20px', gap:12 }}>
                  <span style={{ fontSize:'3rem', color:'var(--text-dim)' }}>◌</span>
                  <p style={{ color:'var(--text-muted)' }}>No queries yet</p>
                </Card>
              )}
            </div>
          )}

          {/* ── AGENT TRACE TAB ── */}
          {tab==='trace' && (
            <div>
              {agentTrace ? (
                <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                  <Card>
                    <SectLabel>Execution Overview</SectLabel>
                    <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:12, marginBottom:16 }}>
                      {[
                        { label:'Agent Type',  val: agentTrace.agent_type,                   color:'var(--gold)'    },
                        { label:'Source',      val: srcInfo(agentTrace.source).label,         color:'var(--sapphire)'},
                        { label:'Total Steps', val: agentTrace.steps.length,                  color:'var(--emerald)' },
                        { label:'RL Action',   val: agentTrace.rl_metadata?.last_action||'—', color:'var(--amber)'   },
                      ].map(r => (
                        <div key={r.label} style={{ background:'var(--surface2)', border:'1px solid var(--border)', padding:'14px 16px' }}>
                          <div className="font-mono" style={{ fontSize:'.56rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)', marginBottom:6 }}>{r.label}</div>
                          <div className="font-mono" style={{ fontSize:'.82rem', color: r.color, fontWeight:700 }}>{r.val}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
                      {Object.entries(STEP_COLORS).map(([type, m]) => {
                        const count = agentTrace.steps.filter(s=>s.type===type).length;
                        return count > 0 ? (
                          <span key={type} className="font-mono" style={{ fontSize:'.6rem', padding:'4px 10px', border:`1px solid ${m.border}40`, color:m.text, background:m.bg }}>
                            {type}: {count}
                          </span>
                        ) : null;
                      })}
                    </div>
                  </Card>

                  {agentTrace.internet_sources?.length > 0 && (
                    <Card>
                      <SectLabel>Web Sources — Tavily ({agentTrace.internet_sources.length})</SectLabel>
                      <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                        {agentTrace.internet_sources.map((src,i) => (
                          <div key={i} style={{ borderLeft:'2px solid var(--emerald)', paddingLeft:16, paddingTop:8, paddingBottom:8, background:'#2dd4a005' }}>
                            <p style={{ fontSize:'.82rem', color:'var(--text)', fontWeight:600, marginBottom:6 }}>{src.title||'Untitled'}</p>
                            {src.snippet && <p style={{ fontSize:'.74rem', color:'var(--text-muted)', lineHeight:1.6, marginBottom:8 }}>{fmt.cut(src.snippet,160)}</p>}
                            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:12 }}>
                              {src.url && <a href={src.url} target="_blank" rel="noreferrer" style={{ fontSize:'.65rem', color:'var(--sapphire)', textDecoration:'none' }}>{fmt.cut(src.url,60)}</a>}
                              {src.score && <Badge color="var(--emerald)">{fmt.pct(src.score)}</Badge>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  <Card>
                    <SectLabel>ReAct Execution Trace</SectLabel>
                    <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                      {agentTrace.steps.map((step,i) => {
                        const m = STEP_COLORS[step.type] || STEP_COLORS.OBSERVATION;
                        return (
                          <div key={i} className="trace-step" style={{ borderColor: m.border, background: m.bg }}>
                            <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
                              <span className="font-mono" style={{ fontSize:'.62rem', fontWeight:700, color:m.text, letterSpacing:'.12em' }}>
                                [{String(i+1).padStart(2,'0')}] {step.type}
                              </span>
                              {step.timestamp && (
                                <span className="font-mono" style={{ fontSize:'.56rem', color:'var(--text-dim)' }}>
                                  {new Date(step.timestamp).toLocaleTimeString()}
                                </span>
                              )}
                            </div>
                            <div style={{ background:'var(--surface2)', border:'1px solid var(--border)', padding:'12px 16px', fontSize:'.76rem', color:'var(--text-muted)', lineHeight:1.7, whiteSpace:'pre-wrap' }}>
                              {step.content}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                </div>
              ) : (
                <Card style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'80px 20px', gap:16 }}>
                  <span style={{ fontSize:'3rem', color:'var(--text-dim)' }}>⊙</span>
                  <p style={{ color:'var(--text-muted)', textAlign:'center', lineHeight:1.7 }}>
                    No agent trace available.<br/>
                    <span style={{ fontSize:'.8rem', color:'var(--text-dim)' }}>Run a query with Agentic strategy to capture the execution trace.</span>
                  </p>
                  <GoldBtn onClick={() => { setStrategy('agentic'); setTab('query'); }} style={{ padding:'11px 28px' }}>
                    Switch to Agentic Mode
                  </GoldBtn>
                </Card>
              )}
            </div>
          )}

          {/* ── RL INTELLIGENCE TAB ── */}
          {tab==='rl' && (
            <div style={{ display:'flex', flexDirection:'column', gap:20 }}>

              {/* Header row */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
                <div>
                  <h2 className="font-serif" style={{ fontSize:'1.6rem', color:'var(--text)', letterSpacing:'-.01em' }}>
                    RL <span className="gold-text">Intelligence</span>
                  </h2>
                  <p className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)', letterSpacing:'.12em', marginTop:4 }}>
                    Q-LEARNING POLICY · EXPERIENCE REPLAY · ADAPTIVE RETRIEVAL
                  </p>
                </div>
                <div style={{ display:'flex', gap:10 }}>
                  <button className="btn-ghost" style={{ padding:'9px 18px' }} onClick={fetchRlStats}>↻ Refresh</button>
                  <button className="btn-gold anim-glow" style={{ padding:'9px 20px' }} onClick={()=>triggerRlTrain(32)} disabled={rlTraining}>
                    {rlTraining ? '⟳ Training…' : '▶ Trigger Replay Training'}
                  </button>
                </div>
              </div>

              {rlStats ? (
                <>
                  {/* Live Stats Grid */}
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:14 }}>
                    {[
                      { label:'Epsilon',        val: rlStats.epsilon?.toFixed(4),           sub:'Exploration rate',         color:'var(--gold)',     pct: rlStats.epsilon/0.3 },
                      { label:'States Learned', val: rlStats.states_learned,                sub:'Unique Q-table states',    color:'var(--sapphire)', pct: Math.min(rlStats.states_learned/50,1) },
                      { label:'Total Updates',  val: rlStats.total_updates,                 sub:'Q-table updates',          color:'var(--emerald)',  pct: Math.min(rlStats.total_updates/500,1) },
                      { label:'Replay Buffer',  val: rlStats.replay_buf_size,               sub:'Experiences stored',       color:'#a855f7',         pct: rlStats.replay_buf_size/10000 },
                    ].map(s => (
                      <div key={s.label} className="card-gold" style={{ padding:'20px' }}>
                        <div className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)', marginBottom:8 }}>{s.sub}</div>
                        <div className="font-serif" style={{ fontSize:'2rem', color:s.color, lineHeight:1, letterSpacing:'-.02em', marginBottom:12 }}>{s.val}</div>
                        <div className="rl-gauge"><div className="rl-gauge-fill" style={{ width:`${(s.pct||0)*100}%`, background:`linear-gradient(90deg, ${s.color}60, ${s.color})` }} /></div>
                        <div className="font-mono" style={{ fontSize:'.58rem', color:'var(--text-dim)', marginTop:6 }}>{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Q-table Sample + DB Stats side by side */}
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>

                    {/* Q-table sample */}
                    <Card>
                      <SectLabel>Q-Table Sample (learned policy)</SectLabel>
                      {Object.entries(rlStats.q_table_sample||{}).slice(0,4).map(([state, qvals]) => (
                        <div key={state} style={{ marginBottom:16 }}>
                          <div className="font-mono" style={{ fontSize:'.62rem', color:'var(--gold)', marginBottom:8 }}>
                            State {state}
                          </div>
                          {Object.entries(qvals).map(([action, val]) => {
                            const maxVal = Math.max(...Object.values(qvals));
                            const isMax = val === maxVal;
                            return (
                              <div key={action} className="qval-row">
                                <div className="qval-label" style={{ color: isMax ? 'var(--gold)' : 'var(--text-dim)' }}>
                                  {isMax ? '★ ' : '  '}{action}
                                </div>
                                <div className="qval-bar-wrap">
                                  <div className="qval-bar-fill" style={{
                                    width: `${Math.max((val / (maxVal||1)) * 100, 0)}%`,
                                    background: isMax ? 'linear-gradient(90deg, var(--gold-dk), var(--gold-lt))' : 'var(--border-lt)',
                                  }}/>
                                </div>
                                <div className="qval-num" style={{ color: isMax ? 'var(--gold)' : 'var(--text-dim)' }}>{val.toFixed(3)}</div>
                              </div>
                            );
                          })}
                        </div>
                      ))}
                      {Object.keys(rlStats.q_table_sample||{}).length === 0 && (
                        <p className="font-mono" style={{ fontSize:'.72rem', color:'var(--text-dim)' }}>Run queries to populate the Q-table.</p>
                      )}
                    </Card>

                    {/* DB stats */}
                    <Card>
                      <SectLabel>Database Statistics</SectLabel>
                      <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
                        {[
                          { label:'Total Experiences',   val: rlStats.db_stats?.total_experiences },
                          { label:'Avg Reward',          val: rlStats.db_stats?.avg_reward?.toFixed(4) },
                          { label:'Terminal Avg Reward', val: rlStats.db_stats?.terminal_avg_reward?.toFixed(4) },
                          { label:'Positive Feedback',   val: rlStats.db_stats?.positive_feedback, color:'var(--emerald)' },
                          { label:'Negative Feedback',   val: rlStats.db_stats?.negative_feedback, color:'var(--ruby)' },
                        ].map(r => (
                          <div key={r.label} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', borderBottom:'1px solid var(--border)', paddingBottom:10 }}>
                            <span className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-muted)' }}>{r.label}</span>
                            <span className="font-mono" style={{ fontSize:'.75rem', color: r.color||'var(--gold)', fontWeight:700 }}>{r.val ?? '—'}</span>
                          </div>
                        ))}

                        {/* Action distribution */}
                        <div>
                          <div className="font-mono" style={{ fontSize:'.6rem', letterSpacing:'.14em', textTransform:'uppercase', color:'var(--text-dim)', marginBottom:10 }}>Action Distribution</div>
                          {Object.entries(rlStats.db_stats?.action_distribution||{}).map(([action, count]) => {
                            const total = Object.values(rlStats.db_stats?.action_distribution||{}).reduce((a,b)=>a+b, 0);
                            const pct = total > 0 ? count/total : 0;
                            const actionColors = { ANSWER_NOW:'var(--emerald)', RETRIEVE_MORE:'var(--sapphire)', RE_RANK:'var(--gold)', ASK_CLARIFICATION:'#a855f7' };
                            const c = actionColors[action] || 'var(--text-muted)';
                            return (
                              <div key={action} className="qval-row">
                                <div className="qval-label" style={{ color:c, fontSize:'.6rem' }}>{action}</div>
                                <div className="qval-bar-wrap"><div className="qval-bar-fill" style={{ width:`${pct*100}%`, background:c }} /></div>
                                <div className="qval-num" style={{ color:c }}>{count}</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </Card>
                  </div>

                  {/* Recent Episodes */}
                  {rlStats.recent_episodes?.length > 0 && (
                    <Card>
                      <SectLabel>Recent Episodes ({rlStats.recent_episodes.length})</SectLabel>
                      <div style={{ overflowX:'auto' }}>
                        <table style={{ width:'100%', borderCollapse:'collapse' }}>
                          <thead>
                            <tr style={{ borderBottom:'1px solid var(--border)' }}>
                              {['Query ID','Steps','Reward','Confidence','Epsilon','Actions','Internet','Feedback','Date'].map(h => (
                                <th key={h} className="font-mono" style={{ fontSize:'.56rem', letterSpacing:'.14em', textTransform:'uppercase', color:'var(--text-dim)', padding:'8px 12px', textAlign:'left', fontWeight:500 }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {rlStats.recent_episodes.map((ep, i) => (
                              <tr key={ep.query_id||i} style={{ borderBottom:'1px solid var(--border)', transition:'background .15s', cursor:'pointer' }}
                                onMouseEnter={e=>e.currentTarget.style.background='var(--surface2)'}
                                onMouseLeave={e=>e.currentTarget.style.background='transparent'}
                                onClick={() => { fetchRlTrace(ep.query_id); toast.info('Trace loaded'); }}>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.65rem', color:'var(--gold)' }}>{fmt.cut(ep.query_id||'',14)}…</td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.7rem', color:'var(--text)' }}>{ep.total_steps}</td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.7rem', color: ep.total_reward>=0 ? 'var(--emerald)' : 'var(--ruby)' }}>{ep.total_reward?.toFixed(3)}</td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.7rem', color:'var(--sapphire)' }}>{ep.final_confidence?.toFixed(2)}</td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.7rem', color:'var(--text-muted)' }}>{ep.epsilon_at_end?.toFixed(4)}</td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.65rem', color:'var(--amber)' }}>{(ep.actions_taken||[]).join(', ')}</td>
                                <td style={{ padding:'10px 12px' }}>{ep.used_internet ? <Badge color="var(--emerald)">Yes</Badge> : <span className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)' }}>No</span>}</td>
                                <td style={{ padding:'10px 12px' }}>
                                  {ep.user_feedback && ep.user_feedback!=='none'
                                    ? <Badge color={ep.user_feedback==='positive'?'var(--emerald)':'var(--ruby)'}>{ep.user_feedback}</Badge>
                                    : <span className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)' }}>—</span>}
                                </td>
                                <td className="font-mono" style={{ padding:'10px 12px', fontSize:'.62rem', color:'var(--text-dim)' }}>{new Date(ep.created_at).toLocaleDateString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  )}

                  {/* RL Trace Panel */}
                  {rlTrace && (
                    <Card>
                      <SectLabel>RL Decision Trace — {fmt.cut(rlTrace.query_id||'',24)}</SectLabel>
                      {rlTrace.episode && (
                        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:20 }}>
                          {[
                            { label:'Total Steps',  val: rlTrace.episode.total_steps,               color:'var(--gold)'    },
                            { label:'Total Reward', val: rlTrace.episode.total_reward?.toFixed(3),   color: rlTrace.episode.total_reward>=0?'var(--emerald)':'var(--ruby)' },
                            { label:'Confidence',   val: rlTrace.episode.final_confidence?.toFixed(2), color:'var(--sapphire)'},
                            { label:'Epsilon End',  val: rlTrace.episode.epsilon_at_end?.toFixed(4), color:'var(--amber)'   },
                          ].map(r => (
                            <div key={r.label} style={{ background:'var(--surface2)', border:'1px solid var(--border)', padding:'12px 14px' }}>
                              <div className="font-mono" style={{ fontSize:'.56rem', letterSpacing:'.14em', textTransform:'uppercase', color:'var(--text-dim)', marginBottom:4 }}>{r.label}</div>
                              <div className="font-mono" style={{ fontSize:'.9rem', fontWeight:700, color:r.color }}>{r.val}</div>
                            </div>
                          ))}
                        </div>
                      )}
                      <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
                        {(rlTrace.experiences||[]).map((exp, i) => {
                          const actionColors = { ANSWER_NOW:'var(--emerald)', RETRIEVE_MORE:'var(--sapphire)', RE_RANK:'var(--gold)', ASK_CLARIFICATION:'#a855f7' };
                          const ac = actionColors[exp.action_name] || 'var(--text-muted)';
                          return (
                            <div key={exp.id||i} style={{ display:'grid', gridTemplateColumns:'24px 140px 1fr 80px 80px 80px', gap:12, alignItems:'center', padding:'10px 14px', background:'var(--surface2)', border:'1px solid var(--border)' }}>
                              <span className="font-mono" style={{ fontSize:'.65rem', color:'var(--text-dim)' }}>{i+1}</span>
                              <span className="font-mono" style={{ fontSize:'.68rem', color: ac, fontWeight:700 }}>{exp.action_name}</span>
                              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                                <span className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)' }}>S:[{(exp.rl_state||[]).join(',')}]</span>
                                <span className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)' }}>→</span>
                                <span className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)' }}>S':[{(exp.next_rl_state||[]).join(',')}]</span>
                              </div>
                              <span className="font-mono" style={{ fontSize:'.7rem', color: exp.reward>=0?'var(--emerald)':'var(--ruby)', fontWeight:700 }}>{exp.reward?.toFixed(3)}</span>
                              <span><Badge color={exp.done?'var(--gold)':'var(--text-dim)'}>{exp.done?'DONE':'MID'}</Badge></span>
                              <span>{exp.user_feedback&&exp.user_feedback!=='none' ? <Badge color={exp.user_feedback==='positive'?'var(--emerald)':'var(--ruby)'}>{exp.user_feedback}</Badge> : <span className="font-mono" style={{ fontSize:'.6rem', color:'var(--text-dim)' }}>—</span>}</span>
                            </div>
                          );
                        })}
                      </div>
                    </Card>
                  )}

                  {/* How it works */}
                  <Card>
                    <SectLabel>How the RL Agent Works</SectLabel>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
                      <div>
                        <div className="font-mono" style={{ fontSize:'.62rem', letterSpacing:'.14em', color:'var(--gold)', textTransform:'uppercase', marginBottom:12 }}>State Space (4 dims)</div>
                        {[
                          { dim:'conf_bucket',  desc:'0=low, 1=med, 2=high confidence'  },
                          { dim:'retr_bucket',  desc:'0=none, 1=few, 2=mod, 3=many chunks' },
                          { dim:'comp_bucket',  desc:'0=simple, 1=medium, 2=complex'     },
                          { dim:'has_internet', desc:'0=no web search, 1=web available'  },
                        ].map(r => (
                          <div key={r.dim} style={{ display:'flex', gap:12, marginBottom:8, fontSize:'.75rem' }}>
                            <span className="font-mono" style={{ color:'var(--gold)', width:110, flexShrink:0 }}>{r.dim}</span>
                            <span style={{ color:'var(--text-muted)' }}>{r.desc}</span>
                          </div>
                        ))}
                      </div>
                      <div>
                        <div className="font-mono" style={{ fontSize:'.62rem', letterSpacing:'.14em', color:'var(--gold)', textTransform:'uppercase', marginBottom:12 }}>Reward Shaping</div>
                        {[
                          { r:'+1.00', desc:'High-confidence final answer' },
                          { r:'+0.50', desc:'Answer with citations'        },
                          { r:'+0.30', desc:'Useful retrieval (conf +10%)' },
                          { r:'-0.50', desc:'Useless retrieval (no gain)'  },
                          { r:'-1.00', desc:'Low-confidence answer'        },
                          { r:'-0.05', desc:'Per-step cost (efficiency)'   },
                          { r:'+0.30', desc:'User thumbs up feedback'      },
                          { r:'-0.30', desc:'User thumbs down feedback'    },
                        ].map(r => (
                          <div key={r.r} style={{ display:'flex', gap:12, marginBottom:6, fontSize:'.75rem' }}>
                            <span className="font-mono" style={{ color: r.r.startsWith('+') ? 'var(--emerald)' : 'var(--ruby)', width:46, flexShrink:0, fontWeight:700 }}>{r.r}</span>
                            <span style={{ color:'var(--text-muted)' }}>{r.desc}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Card>
                </>
              ) : (
                <Card style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'80px 20px', gap:16 }}>
                  <div className="anim-pulse" style={{ fontSize:'3rem', color:'var(--gold)' }}>◈</div>
                  <p className="font-mono" style={{ fontSize:'.68rem', letterSpacing:'.16em', textTransform:'uppercase', color:'var(--text-dim)' }}>Loading RL statistics…</p>
                  <GoldBtn onClick={fetchRlStats} style={{ padding:'11px 24px' }}>Load RL Stats</GoldBtn>
                </Card>
              )}
            </div>
          )}

          {/* ── HEALTH/SYSTEM TAB ── */}
          {tab==='health' && (
            <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
              <Card>
                <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16 }}>
                  <SectLabel>System Health</SectLabel>
                  <button className="btn-ghost" style={{ padding:'8px 16px' }} onClick={() => { fetchHealth(); fetchAgentStatus(); }}>↻ Refresh</button>
                </div>
                {health ? (
                  <>
                    <div style={{ marginBottom:16 }}>
                      <Badge color={health.status==='healthy' ? 'var(--emerald)' : 'var(--ruby)'}>
                        {health.status?.toUpperCase()}
                      </Badge>
                    </div>
                    <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:10 }}>
                      {Object.entries(health.components||{}).map(([k, v]) => (
                        <div key={k} style={{ background:'var(--surface2)', border:'1px solid var(--border)', padding:'12px 16px', display:'flex', alignItems:'center', gap:12 }}>
                          <HDot status={v} />
                          <div>
                            <p style={{ fontSize:'.8rem', color:'var(--text)', textTransform:'capitalize' }}>{k.replace(/_/g,' ')}</p>
                            <p className="font-mono" style={{ fontSize:'.62rem', color: v==='operational' ? 'var(--emerald)' : 'var(--ruby)', marginTop:2 }}>{v}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="font-mono" style={{ marginTop:12, fontSize:'.62rem', color:'var(--text-dim)' }}>
                      Checked: {fmt.date(health.timestamp)} · v{health.version||'—'}
                    </p>
                  </>
                ) : (
                  <p style={{ color:'var(--text-muted)', fontSize:'.82rem' }}>Click Refresh to check health.</p>
                )}
              </Card>

              {agentStatus && (
                <Card>
                  <SectLabel>Agent Status</SectLabel>
                  {agentStatus.rl_enabled && (
                    <div style={{ marginBottom:14 }}>
                      <Badge gold>RL-Enhanced Mode Active</Badge>
                    </div>
                  )}
                  <pre style={{ fontSize:'.72rem', color:'var(--text-muted)', lineHeight:1.6, overflowX:'auto', maxHeight:280, background:'var(--surface2)', padding:16, border:'1px solid var(--border)' }}>
                    {JSON.stringify(agentStatus, null, 2)}
                  </pre>
                </Card>
              )}

              <Card>
                <SectLabel>API Reference</SectLabel>
                <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                  {[
                    { m:'POST',   c:'var(--emerald)', ep:'/api/rag/v1/query/',                   desc:'Execute RAG query'        },
                    { m:'POST',   c:'var(--emerald)', ep:'/api/rag/v1/upload/',                  desc:'Ingest document'          },
                    { m:'GET',    c:'var(--sapphire)',ep:'/api/rag/v1/documents/',               desc:'List documents'           },
                    { m:'DELETE', c:'var(--ruby)',    ep:'/api/rag/v1/documents/<id>/delete/',   desc:'Delete document'          },
                    { m:'DELETE', c:'var(--ruby)',    ep:'/api/rag/v1/documents/clear/',         desc:'Clear all'                },
                    { m:'GET',    c:'var(--sapphire)',ep:'/api/rag/v1/queries/',                 desc:'Query history'            },
                    { m:'GET',    c:'var(--sapphire)',ep:'/api/rag/v1/stats/',                   desc:'System stats'             },
                    { m:'GET',    c:'var(--sapphire)',ep:'/api/rag/v1/health/',                  desc:'Health check'             },
                    { m:'POST',   c:'var(--gold)',    ep:'/api/rag/v1/rl/feedback/',             desc:'Submit answer feedback'   },
                    { m:'GET',    c:'var(--gold)',    ep:'/api/rag/v1/rl/stats/',                desc:'Live RL statistics'       },
                    { m:'GET',    c:'var(--gold)',    ep:'/api/rag/v1/rl/trace/<id>/',           desc:'Per-query RL trace'       },
                    { m:'POST',   c:'var(--gold)',    ep:'/api/rag/v1/rl/train/',               desc:'Trigger replay training'  },
                  ].map(r => (
                    <div key={r.ep} style={{ display:'flex', alignItems:'center', gap:12, background:'var(--surface2)', border:'1px solid var(--border)', padding:'9px 14px', fontSize:'.78rem' }}>
                      <span className="font-mono" style={{ color:r.c, fontWeight:700, width:52, flexShrink:0 }}>{r.m}</span>
                      <span className="font-mono" style={{ color:'var(--text)', flex:1, fontSize:'.7rem' }}>{r.ep}</span>
                      <span className="font-mono" style={{ color:'var(--text-dim)', fontSize:'.62rem' }}>{r.desc}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

        </main>

        {/* ═══ FOOTER ═══ */}
        <footer style={{ borderTop:'1px solid var(--border)', padding:'16px 28px', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <span className="font-mono" style={{ fontSize:'.58rem', letterSpacing:'.18em', textTransform:'uppercase', color:'var(--text-dim)' }}>
            RAGENT Intelligence · RL-Driven Multi-Agent RAG · v2.0
          </span>
          <div style={{ display:'flex', gap:8 }}>
            <span style={{ width:6, height:6, borderRadius:'50%', background:'var(--gold)', opacity:.4 }}/>
            <span style={{ width:6, height:6, borderRadius:'50%', background:'var(--gold)', opacity:.7 }}/>
            <span style={{ width:6, height:6, borderRadius:'50%', background:'var(--gold)' }}/>
          </div>
        </footer>

      </div>
    </>
  );
}




