import React, { useState } from 'react';
import { 
  Sparkles, 
  Send, 
  Bot, 
  User, 
  HelpCircle, 
  Receipt
} from 'lucide-react';

export default function SettlementQAChat() {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      sender: 'agent',
      text: 'Hello! I am your Settlement Intelligence Copilot. I can query reconciled ledger batches, unpack MDR fee structures, calculate claimable Input Tax Credit (ITC), and forecast upcoming cash positions.',
      timestamp: 'Just now',
    }
  ]);
  const [loading, setLoading] = useState(false);

  const suggestedQueries = [
    'What was our total GST paid on MDR?',
    'Show me all unmatched settlement exceptions',
    'Give me the MDR fee breakdown across payment methods',
    'What is our claimable ITC amount for tax filing?',
    'What is our net revenue payout after all fees?',
    'Show high-value transactions above Rs. 20,000',
  ];

  const handleSend = async (textToSend) => {
    const q = textToSend || query;
    if (!q.trim()) return;

    const userMsg = { sender: 'user', text: q, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setChatHistory(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`/api/recon/qa?question=${encodeURIComponent(q)}`, {
        method: 'POST',
      });
      const data = await res.json();

      const agentMsg = {
        sender: 'agent',
        text: data.answer || 'No response available.',
        explanation: data.explanation,
        data: data.data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setChatHistory(prev => [...prev, agentMsg]);
    } catch (err) {
      setChatHistory(prev => [
        ...prev,
        {
          sender: 'agent',
          text: 'Error connecting to Settlement Q&A Engine. Ensure the reconciliation backend is running.',
          timestamp: 'Error',
          error: true,
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[650px]">
      
      {/* Left Column: Chat Conversation */}
      <div className="lg:col-span-8 rzp-card rounded-2xl flex flex-col h-full overflow-hidden">
        
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-[#0c6cf2]">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#0c2340] flex items-center gap-2">
                Settlement Q&A Copilot
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0c6cf2] border border-blue-200 font-bold">
                  Zero Hallucination RAG
                </span>
              </h4>
              <p className="text-[11px] text-slate-500">Natural language query engine over settlement batches</p>
            </div>
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {chatHistory.map((msg, idx) => {
            const isAgent = msg.sender === 'agent';
            return (
              <div key={idx} className={`flex items-start gap-3 ${isAgent ? '' : 'flex-row-reverse'}`}>
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${
                  isAgent ? 'bg-blue-50 text-[#0c6cf2] border border-blue-100' : 'bg-[#0c6cf2] text-white'
                }`}>
                  {isAgent ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                </div>

                <div className={`max-w-xl rounded-2xl p-4 text-xs leading-relaxed ${
                  isAgent 
                    ? 'bg-slate-50 border border-slate-200 text-slate-800' 
                    : 'bg-[#0c6cf2] text-white font-medium shadow-sm'
                }`}>
                  <div className="whitespace-pre-line">{msg.text}</div>

                  {msg.explanation && (
                    <div className="mt-2.5 pt-2.5 border-t border-slate-200 text-[11px] text-slate-600 flex items-start gap-1.5">
                      <HelpCircle className="h-3.5 w-3.5 text-purple-600 shrink-0 mt-0.5" />
                      <span>{msg.explanation}</span>
                    </div>
                  )}

                  <div className={`text-[10px] mt-1.5 ${isAgent ? 'text-slate-400' : 'text-blue-100'} text-right`}>
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-[#0c6cf2] bg-blue-50 p-3 rounded-xl border border-blue-100 w-fit">
              <Sparkles className="h-4 w-4 animate-spin" />
              <span>Querying settlement ledger & computing variances...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/80">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about settlements, MDR fees, GST, ITC, or forecasting..."
              className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-[#0c2340] placeholder-slate-400 focus:outline-none focus:border-[#0c6cf2] focus:ring-1 focus:ring-[#0c6cf2]"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="rzp-btn-primary px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Query</span>
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Suggested Query Pills */}
      <div className="lg:col-span-4 rzp-card rounded-2xl p-5 flex flex-col justify-between">
        <div>
          <h4 className="text-sm font-bold text-[#0c2340] flex items-center gap-2 mb-1">
            <Receipt className="h-4 w-4 text-[#0c6cf2]" />
            Quick Settlement Queries
          </h4>
          <p className="text-[11px] text-slate-500 mb-4">
            Click any prompt to execute instant deterministic queries across the reconciled batch.
          </p>

          <div className="space-y-2">
            {suggestedQueries.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(sq)}
                className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-blue-50/60 border border-slate-200 hover:border-blue-200 text-xs text-slate-700 hover:text-[#0c6cf2] transition-all flex items-center justify-between group cursor-pointer"
              >
                <span>{sq}</span>
                <span className="text-slate-400 group-hover:text-[#0c6cf2] group-hover:translate-x-0.5 transition-all text-sm font-bold">
                  →
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 p-3 rounded-xl bg-blue-50/70 border border-blue-200 text-[11px] text-slate-700">
          <strong className="text-[#0c2340]">Deterministic RAG:</strong> Unlike open-ended chatbots, queries are mapped to typed Python aggregation methods to guarantee 0% hallucination in accounting answers.
        </div>
      </div>

    </div>
  );
}
