// frontend/lib/api.ts
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

interface DocumentUploadResponse {
  document_id: number;
  task_id?: string;
  status: string;
  message: string;
}

export interface DocumentStatus {
  document_id: number;
  status: string;
  progress: number | null;
  error_message: string | null;
}

interface Fund {
  id: number;
  name: string;
  gp_name?: string;
  fund_type?: string;
  vintage_year?: number;
  metrics?: FundMetrics;
}

interface Transaction {
  id: number;
  fund_id: number;
  amount: number;
}

interface TransactionList {
  items: Transaction[];
  total: number;
  page: number;
  pages: number;
}

interface FundMetrics {
  pic?: number;
  total_distributions?: number;
  dpi?: number;
  irr?: number;
  tvpi?: number;
  rvpi?: number;
}

interface ChatQueryRequest {
  query: string;
  fund_id?: number;
  conversation_id?: string;
}

interface ChatQueryResponse {
  answer: string;
  sources?: Array<{
    content: string;
    metadata?: Record<string, any>;
    score?: number;
  }>;
  metrics?: FundMetrics;
  processing_time?: number;
}

interface Conversation {
  conversation_id: string;
  fund_id?: number;
  messages: Array<{ role: string; content: string; timestamp: string }>;
  created_at: string;
  updated_at: string;
}

export const documentApi = {
  upload: async (
    file: File,
    fundId?: number
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    if (fundId !== undefined && fundId !== null) {
      formData.append("fund_id", fundId.toString());
    }

    const response = await api.post<DocumentUploadResponse>(
      "/api/documents/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  getStatus: async (documentId: number): Promise<DocumentStatus> => {
    const response = await api.get<DocumentStatus>(
      `/api/documents/${documentId}/status`
    );
    return response.data;
  },

  list: async (fundId?: number): Promise<any[]> => {
    const params = fundId ? { fund_id: fundId } : {};
    const response = await api.get<any[]>("/api/documents/", { params });
    return response.data;
  },

  delete: async (documentId: number): Promise<void> => {
    await api.delete(`/api/documents/${documentId}`);
  },
};

export const fundApi = {
  list: async (): Promise<Fund[]> => {
    const response = await api.get<Fund[]>("/api/funds/");
    return response.data;
  },

  get: async (fundId: number): Promise<Fund> => {
    const response = await api.get<Fund>(`/api/funds/${fundId}`);
    return response.data;
  },

  create: async (fundData: Omit<Fund, "id">): Promise<Fund> => {
    const response = await api.post<Fund>("/api/funds/", fundData);
    return response.data;
  },

  getTransactions: async (
    fundId: number,
    type: string,
    page: number = 1,
    limit: number = 50
  ): Promise<TransactionList> => {
    const response = await api.get<TransactionList>(
      `/api/funds/${fundId}/transactions`,
      {
        params: { transaction_type: type, page, limit },
      }
    );
    return response.data;
  },

  getMetrics: async (fundId: number): Promise<FundMetrics> => {
    const response = await api.get<FundMetrics>(`/api/funds/${fundId}/metrics`);
    return response.data;
  },
};

export const chatApi = {
  query: async (
    query: string,
    fundId?: number,
    conversationId?: string
  ): Promise<ChatQueryResponse> => {
    const requestData: ChatQueryRequest = {
      query,
      fund_id: fundId,
      conversation_id: conversationId,
    };
    const response = await api.post<ChatQueryResponse>(
      "/api/chat/query",
      requestData
    );
    return response.data;
  },

  createConversation: async (fundId?: number): Promise<Conversation> => {
    const requestData =
      fundId !== undefined && fundId !== null ? { fund_id: fundId } : {};
    const response = await api.post<Conversation>(
      "/api/chat/conversations",
      requestData
    );
    return response.data;
  },

  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get<Conversation>(
      `/api/chat/conversations/${conversationId}`
    );
    return response.data;
  },
};

export const metricsApi = {
  getFundMetrics: async (
    fundId: number,
    metric?: string
  ): Promise<FundMetrics> => {
    const params = metric ? { metric } : {};
    const response = await api.get<FundMetrics>(
      `/api/metrics/funds/${fundId}/metrics`,
      { params }
    );
    return response.data;
  },
};
