"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, FileText } from "lucide-react";
import { chatApi, fundApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import remarkGfm from "remark-gfm";
import ReactMarkdown from "react-markdown";

interface Fund {
  id: number;
  name: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  metrics?: any;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [selectedFundId, setSelectedFundId] = useState<number | null>(null);
  const [availableFunds, setAvailableFunds] = useState<Fund[]>([]);
  const [fetchingFunds, setFetchingFunds] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchFunds = async () => {
      setFetchingFunds(true);
      try {
        const funds = await fundApi.list();
        setAvailableFunds(funds);
        if (funds.length > 0 && selectedFundId === null) {
          setSelectedFundId(funds[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch funds:", err);
      } finally {
        setFetchingFunds(false);
      }
    };

    fetchFunds();
  }, []);

  useEffect(() => {
    const createNewConversation = async () => {
      try {
        const conv = await chatApi.createConversation(
          selectedFundId ?? undefined
        );
        setConversationId(conv.conversation_id);
        setMessages([]);
      } catch (err) {
        console.error("Failed to create conversation:", err);
      }
    };

    if (selectedFundId !== null) {
      createNewConversation();
    }
  }, [selectedFundId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !conversationId) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatApi.query(
        input,
        selectedFundId ?? undefined,
        conversationId
      );

      const assistantMessage: Message = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        metrics: response.metrics,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error("Chat query error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: `Sorry, I encountered an error: ${
          error.response?.data?.detail || error.message || "Unknown error"
        }`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-12rem)]">
      <div className="mb-4">
        <h1 className="text-4xl font-bold mb-2">Fund Analysis Chat</h1>
        <p className="text-gray-600">
          Ask questions about fund performance, metrics, and transactions
        </p>
        <div className="mt-4">
          <label
            htmlFor="fund-select"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Select Fund:
          </label>
          {fetchingFunds ? (
            <p className="text-sm text-gray-500">Loading funds...</p>
          ) : (
            <select
              id="fund-select"
              value={selectedFundId || ""}
              onChange={(e) =>
                setSelectedFundId(
                  e.target.value ? Number(e.target.value) : null
                )
              }
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              disabled={availableFunds.length === 0 || loading}
            >
              <option value="">-- Select a Fund --</option>
              {availableFunds.map((fund) => (
                <option key={fund.id} value={fund.id}>
                  {fund.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md flex flex-col h-full">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && !loading && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <FileText className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Start a conversation
              </h3>
              <p className="text-gray-600 mb-6">Try asking questions like:</p>
              <div className="space-y-2 max-w-md mx-auto">
                <SampleQuestion
                  question="What is the current DPI?"
                  onClick={() => setInput("What is the current DPI?")}
                />
                <SampleQuestion
                  question="Calculate the IRR for this fund"
                  onClick={() => setInput("Calculate the IRR for this fund")}
                />
                <SampleQuestion
                  question="What does Paid-In Capital mean?"
                  onClick={() => setInput("What does Paid-In Capital mean?")}
                />
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {loading && (
            <div className="flex items-center space-x-2 text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about the fund..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading || !selectedFundId}
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !selectedFundId}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-3xl ${isUser ? "ml-12" : "mr-12"}`}>
        <div
          className={`rounded-lg p-4 ${
            isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
          }`}
        >
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Metrics Display */}
        {message.metrics && (
          <div className="mt-3 bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-sm text-gray-700 mb-2">
              Calculated Metrics
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(message.metrics).map(([key, value]) => {
                if (value === null || value === undefined) return null;

                let displayValue: string;
                const displayKey = key;

                if (typeof value === "number") {
                  if (key.toLowerCase().includes("irr")) {
                    displayValue = `${value.toFixed(2)}%`;
                  } else if (key.toLowerCase().includes("dpi")) {
                    displayValue = `${value.toFixed(4)}x`;
                  } else if (
                    key.toLowerCase().includes("pic") ||
                    key.toLowerCase().includes("total_distribution")
                  ) {
                    displayValue = `${formatCurrency(value)}`;
                  } else {
                    displayValue = value.toString();
                  }
                } else {
                  displayValue = String(value);
                }

                let displayName: string;
                switch (key) {
                  case "pic":
                    displayName = "Paid-In Capital";
                    break;
                  case "total_distributions":
                    displayName = "Total Distribution";
                    break;
                  case "dpi":
                    displayName = "DPI";
                    break;
                  case "irr":
                    displayName = "IRR";
                    break;
                  default:
                    displayName = key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase());
                }

                return (
                  <div key={key} className="text-sm">
                    <span className="text-gray-600">{displayName}:</span>{" "}
                    <span className="font-semibold">{displayValue}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <details className="bg-white border border-gray-200 rounded-lg">
              <summary className="px-4 py-2 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50">
                View Sources ({message.sources.length})
              </summary>
              <div className="px-4 py-3 space-y-2 border-t">
                {message.sources.slice(0, 3).map((source, idx) => (
                  <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                    <div className="prose prose-xs max-w-none">
                      <style jsx>{`
                        /* Sembunyikan semua heading level 1, 2, 3 */
                        .prose h1,
                        .prose h2,
                        .prose h3 {
                          display: none;
                        }
                        /* Sembunyikan paragraf yang berisi "Mock Fund Performance Report" */
                        .prose p {
                          /* Jika Anda tahu bahwa teks ini selalu ada di awal, Anda bisa gunakan ini:
                          &:first-of-type {
                            display: none;
                          }
                          */
                          /* Atau, jika Anda ingin menyembunyikan semua paragraf yang mengandung teks tertentu, Anda bisa gunakan JavaScript, 
                             tapi dalam CSS murni, kita tidak bisa mencocokkan isi teks.
                             Sebagai gantinya, kita bisa menyembunyikan paragraf pertama jika itu adalah judul laporan.
                          */
                          /* Solusi sederhana: sembunyikan paragraf pertama */
                          &:first-of-type {
                            display: none;
                          }
                        }
                        /* Tambahkan padding dan margin ke tabel agar tidak saling menempel */
                        .prose table {
                          margin-top: 1rem;
                          margin-bottom: 1rem;
                          border-collapse: collapse;
                          width: 100%;
                          border: 1px solid #d1d5db; /* border-gray-300 */
                          background-color: #f9fafb; /* bg-gray-50 */
                        }
                        .prose table th,
                        .prose table td {
                          border: 1px solid #d1d5db; /* border-gray-300 */
                          padding: 0.5rem;
                          text-align: left;
                        }
                        .prose table thead th {
                          background-color: #f3f4f6; /* bg-gray-100 */
                          font-weight: bold;
                          border-bottom: 2px solid #d1d5db; /* border-gray-300 lebih tebal */
                        }
                        /* Beri warna latar belakang yang sedikit berbeda untuk setiap tabel */
                        .prose table:nth-of-type(odd) {
                          background-color: #f9fafb; /* bg-gray-50 */
                        }
                        .prose table:nth-of-type(even) {
                          background-color: #f3f4f6; /* bg-gray-100 */
                        }
                        /* Gaya khusus untuk judul tabel (jika ada) */
                        .prose p:first-child {
                          font-weight: bold;
                          margin-bottom: 0.5rem;
                          color: #111827; /* gray-900 */
                        }
                      `}</style>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {source.content}
                      </ReactMarkdown>
                    </div>
                    {source.score && (
                      <p className="text-gray-500 mt-1">
                        Relevance: {(source.score * 100).toFixed(0)}%
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        <p className="text-xs text-gray-500 mt-2">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

function SampleQuestion({
  question,
  onClick,
}: {
  question: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition"
    >
      &quot;{question}&quot;
    </button>
  );
}
