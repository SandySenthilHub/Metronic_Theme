export interface DocumentType {
  id: string;
  name: string;
  description: string;
  required: boolean;
  uploaded: boolean;
file?: File | File[];
}

export interface ClaimData {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  documents: DocumentType[];
  createdAt: Date;
  lastUpdated: Date;
}

export interface PolicyQuestion {
  id: string;
  question: string;
  answer?: string;
  timestamp: Date;
}