import React, { useState } from 'react';
import { Send, MessageCircle, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Content } from '../../../_metronic/layout/components/content';

interface PolicyQAProps {
  onBack: () => void;
}

const BACKEND_URL = " http://127.0.0.1:8000";

const prompts = [
  "Central Bank Insurance Rules",
  "General UAE, Oman and Saudi Rules",
  "Motor Vehicle Underwriting",
  "Motor Vehicle - Indian Underwriting Policy"
];

const PolicyQA: React.FC<PolicyQAProps> = ({ onBack }) => {

  const navigate = useNavigate();

  const [question, setQuestion] = useState('');
  const [selectedPrompt, setSelectedPrompt] = useState(prompts[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {

    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/policy_qa/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: `${selectedPrompt}: ${question}`,
          thread_id: sessionStorage.getItem('thread_id') || ''
        }),
      });

      if (!response.ok) throw new Error(`Error ${response.status}`);
      const data = await response.json();
      setAnswer(data.answer || 'No answer returned from backend.');
    } catch (error) {
      console.error(error);
      setAnswer('Failed to get answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Content>
      <div className="d-flex flex-column gap-6 mx-auto">
        {/* Back Button */}
        <div>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn btn-clean btn-sm btn-active-color-primary d-flex align-items-center"
          >
            <ArrowLeft className="me-2" />
            Back to Dashboard
          </button>
        </div>

        {/* Card Container */}
        <div className="card card-flush shadow-sm p-8">

          <div className="card-header py-4 bg-light-primary">
            <div className="d-flex align-items-center">
              <div className="symbol symbol-70px bg-light-primary me-4">
                <MessageCircle className="text-primary" />
              </div>
              <div>
                <h2 className="fw-bold text-gray-800">Policy Q&A</h2>
                <p className="text-gray-600">Ask questions about central government details or insurance policies.</p>
              </div>
            </div>
          </div>

          <div className="card-body py-8">
            <form onSubmit={handleSubmit} className="d-flex flex-column gap-5">
              {/* Prompt Select */}
              <div>
                <label htmlFor="prompt" className="form-label fw-semibold mb-2">Select a prompt:</label>
                <select
                  id="prompt"
                  value={selectedPrompt}
                  onChange={(e) => setSelectedPrompt(e.target.value)}
                  className="form-select form-select-solid"
                >
                  {prompts.map((p, idx) => (
                    <option key={idx} value={p}>{p}</option>
                  ))}
                </select>
              </div>

              {/* Question Input */}
              <div>
                <label htmlFor="question" className="form-label fw-semibold mb-2">Ask a question:</label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g., What are the terms for motor insurance claims?"
                  className="form-control form-control-solid"
                  rows={5}
                  disabled={isLoading}
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!question.trim() || isLoading}
                className="btn btn-primary d-flex align-items-center justify-content-center"
              >
                {isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="me-2" />
                    Get Answer
                  </>
                )}
              </button>
            </form>

            {/* Answer */}
            {answer && (
              <div className="mt-6 card card-flush bg-light rounded p-4">
                <h4 style={{ color: 'red', fontWeight: 'bold', marginBottom: '1rem' }}>
                  AI Response:
                </h4>
                <div className="text-gray-700" style={{ whiteSpace: 'pre-line' }}>
                  {answer
                    // Remove markdown '#' symbols and convert headings to bold red
                    .replace(/^###\s*(.*)$/gm, (_, title) => `\n${title.toUpperCase()}\n`)
                    .replace(/^##\s*(.*)$/gm, (_, title) => `\n${title.toUpperCase()}\n`)}
                </div>
              </div>
            )}


          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 small">
          <span className="d-inline-flex align-items-center gap-1">
            <span className="w-2 h-2 bg-danger rounded-circle d-inline-block"></span>
            Insurance AI Application
          </span>
        </div>
      </div>
    </Content>
  );
};

export default PolicyQA;
