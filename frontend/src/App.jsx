import React, { useState } from 'react';
import { Upload, MessageSquare, Book, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument, queryRAG, listDocuments, checkHealth } from './api';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

function App() {
  // Connection State
  const [backendStatus, setBackendStatus] = useState({ connected: false, checking: true });
  
  // Documents List
  const [documents, setDocuments] = useState([]);

  // Upload State
  const [uploadData, setUploadData] = useState({
    curriculum_book_name: 'GOV_SSC_PHYSICS',
    document_id: '1',
    subject: 'Physics',
    jsonFile: null,
    mdFile: null,
  });
  const [uploadStatus, setUploadStatus] = useState({ loading: false, success: null, error: null });

  // Query State
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);

  // Initial Fetch
  React.useEffect(() => {
    const init = async () => {
      try {
        await checkHealth();
        setBackendStatus({ connected: true, checking: false });
        
        const docs = await listDocuments();
        setDocuments(Array.isArray(docs) ? docs : []);
      } catch (err) {
        console.error('Backend connection failed:', err);
        setBackendStatus({ connected: false, checking: false });
        setDocuments([]);
      }
    };
    init();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadData.jsonFile || !uploadData.mdFile) {
      setUploadStatus({ loading: false, success: null, error: 'Please select both JSON and Markdown files.' });
      return;
    }

    setUploadStatus({ loading: true, success: null, error: null });
    const formData = new FormData();
    formData.append('json_file', uploadData.jsonFile);
    formData.append('md_file', uploadData.mdFile);
    formData.append('curriculum_book_name', uploadData.curriculum_book_name);
    formData.append('document_id', uploadData.document_id);
    formData.append('subject', uploadData.subject);

    try {
      await uploadDocument(formData);
      setUploadStatus({ loading: false, success: 'Document processed and stored successfully!', error: null });
      // Refresh documents list
      const docs = await listDocuments();
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (err) {
      setUploadStatus({ loading: false, success: null, error: err.response?.data?.detail || 'Failed to process document.' });
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setQueryLoading(true);
    setQueryResult(null);
    try {
      // Find if we should filter by the currently selected book in ingestion
      // or if we should add a separate "Filter by Book" dropdown for queries
      const result = await queryRAG(query);
      setQueryResult(result);
    } catch (err) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || 'Failed to get answer from AI Tutor.';
      alert(errorMsg);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans">
      <header className="max-w-4xl mx-auto mb-12 text-center">
        <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center justify-center gap-2">
          <Book className="text-purple-600" size={36} />
          AI Tutor RAG
        </h1>
        <p className="text-slate-600">Production-ready Retrieval Augmented Generation</p>
        <div className="mt-4 flex justify-center items-center gap-2 text-sm">
          <span className={cn(
            "w-2 h-2 rounded-full",
            backendStatus.checking ? "bg-slate-400 animate-pulse" : (backendStatus.connected ? "bg-green-500" : "bg-red-500")
          )} />
          <span className="text-slate-500">
            {backendStatus.checking ? "Checking backend..." : (backendStatus.connected ? "Backend Connected" : "Backend Disconnected")}
          </span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ingestion Section */}
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 text-slate-800">
            <Upload className="text-purple-500" size={20} />
            Ingest Knowledge
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Curriculum Book</label>
              <select
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                value={uploadData.curriculum_book_name}
                onChange={(e) => setUploadData({ ...uploadData, curriculum_book_name: e.target.value })}
              >
                <option value="GOV_SSC_PHYSICS">GOV_SSC_PHYSICS</option>
                <option value="GOV_SSC_CHEMISTRY">GOV_SSC_CHEMISTRY</option>
                <option value="GOV_SSC_ENGLISH">GOV_SSC_ENGLISH</option>
                {Array.isArray(documents) && documents.map((doc, idx) => (
                  doc?.curriculum_book_name && !["GOV_SSC_PHYSICS", "GOV_SSC_CHEMISTRY", "GOV_SSC_ENGLISH"].includes(doc.curriculum_book_name) && (
                    <option key={idx} value={doc.curriculum_book_name}>{doc.curriculum_book_name}</option>
                  )
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Document ID</label>
                <input
                  type="number"
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                  value={uploadData.document_id}
                  onChange={(e) => setUploadData({ ...uploadData, document_id: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
                <input
                  type="text"
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                  value={uploadData.subject}
                  onChange={(e) => setUploadData({ ...uploadData, subject: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">JSON Parse File</label>
              <input
                type="file"
                accept=".json"
                onChange={(e) => setUploadData({ ...uploadData, jsonFile: e.target.files[0] })}
                className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Markdown File</label>
              <input
                type="file"
                accept=".md"
                onChange={(e) => setUploadData({ ...uploadData, mdFile: e.target.files[0] })}
                className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer"
              />
            </div>

            <button
              type="submit"
              disabled={uploadStatus.loading}
              className={cn(
                "w-full py-3 px-4 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2",
                uploadStatus.loading ? "bg-purple-400 cursor-not-allowed" : "bg-purple-600 hover:bg-purple-700 active:scale-[0.98]"
              )}
            >
              {uploadStatus.loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Processing...
                </>
              ) : (
                <>
                  <CheckCircle size={20} />
                  Generate Chunks & Embed
                </>
              )}
            </button>

            {uploadStatus.success && (
              <div className="p-3 bg-green-50 border border-green-100 text-green-700 rounded-lg flex items-center gap-2 text-sm">
                <CheckCircle size={16} />
                {uploadStatus.success}
              </div>
            )}
            {uploadStatus.error && (
              <div className="p-3 bg-red-50 border border-red-100 text-red-700 rounded-lg flex items-center gap-2 text-sm">
                <AlertCircle size={16} />
                {uploadStatus.error}
              </div>
            )}
          </form>
        </section>

        {/* Query Section */}
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-column h-full">
          <div className="flex-1">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 text-slate-800">
              <MessageSquare className="text-blue-500" size={20} />
              Ask AI Tutor
            </h2>

            <form onSubmit={handleQuery} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  placeholder="e.g. How to balance chemical equations?"
                  className="w-full p-4 pr-12 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={queryLoading}
                />
                <button
                  type="submit"
                  disabled={queryLoading || !query.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:text-slate-400"
                >
                  {queryLoading ? <Loader2 className="animate-spin" size={20} /> : <MessageSquare size={20} />}
                </button>
              </div>
            </form>

            <div className="space-y-4 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">
              {queryResult ? (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="bg-blue-50 p-4 rounded-xl mb-4 border border-blue-100">
                    <p className="text-slate-800 leading-relaxed">{queryResult.answer}</p>
                  </div>
                  
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Sources</h3>
                  <div className="space-y-2">
                    {queryResult.sources?.map((source, idx) => (
                      <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                        <div className="flex justify-between items-center mb-1 text-slate-500 font-medium">
                          <span>{source.book_name} • Ch: {source.chapter}</span>
                          <span>Page {source.page_number}</span>
                        </div>
                        <p className="text-slate-600 line-clamp-2 italic">"{source.content}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 py-12">
                  <MessageSquare size={48} strokeWidth={1} className="mb-2" />
                  <p>Ask a question to see the RAG results</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
