import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle, Clock, FileText } from 'lucide-react';
import { DocumentType } from '../types';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Content } from '../../../_metronic/layout/components/content';
import { Card1 } from '../../../_metronic/partials/content/cards/Card1';

interface ProcessingResultsProps {
  onBack: () => void;
  documents: DocumentType[];
}

const BACKEND_URL = " http://127.0.0.1:8000";

const ProcessingResults: React.FC<ProcessingResultsProps> = ({ onBack, documents }) => {
  const [processingStage, setProcessingStage] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [claimResult, setClaimResult] = useState<any>(null);

  const stages = [
    'Validating documents...',
    'Analyzing claim details...',
    'Cross-referencing policy...',
    'Generating assessment...',
    'Finalizing results...'
  ];

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const processClaim = async () => {
      try {
        const formData = new FormData();
        documents.forEach(doc => {
          if (!doc.file) return;
          if (Array.isArray(doc.file)) {
            doc.file.forEach(f => formData.append(doc.id, f));
          } else {
            formData.append(doc.id, doc.file);
          }
        });

        const response = await fetch(`${BACKEND_URL}/process_claim/`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error('Failed to process claim');

        const data = await response.json();
        console.log("Backend response:", data);
        setClaimResult(data);

        interval = setInterval(() => {
          setProcessingStage(prev => {
            if (prev < stages.length - 1) {
              return prev + 1;
            } else {
              setIsComplete(true);
              clearInterval(interval);
              return prev;
            }
          });
        }, 1500);

      } catch (error) {
        console.error(error);
        setIsComplete(true);
        setClaimResult({
          status: 'failed',
          claimId: 'N/A',
          estimatedPayout: 'N/A',
          processingTime: 'N/A',
          nextSteps: ['There was an error processing your report. Please try again.']
        });
      }
    };

    processClaim();

    return () => clearInterval(interval);
  }, [documents]);

  if (!isComplete || !claimResult) {
    return (
      <Content>
        <div className="d-flex flex-column gap-6 mx-auto">
          <div>
            <button
              onClick={onBack}
              className="btn btn-clean btn-sm btn-active-color-primary d-flex align-items-center"
            >
              <ArrowLeft className="me-2" />
              Back to Dashboard
            </button>
          </div>
          <div className="d-flex justify-content-center">

            <div className="card shadow-sm w-50 mt-10">
              <div className="card-header bg-light-primary">
                <h3 className="card-title">Processing Your Report</h3>
                <div className="card-toolbar">
                  <p className="text-muted mb-0">Please wait while we analyze your documents.</p>
                </div>
              </div>
              <div className="card-body">
                <div className="d-flex flex-column align-items-center text-center">
                  {/* <div className="symbol symbol-70px mb-6">
                  <div className="symbol-label bg-light-primary d-flex justify-content-center align-items-center">
                    <Clock className="text-black animate-spin" size={28} />
                  </div>
                </div> */}
                  <div className="w-100">
                    {stages.map((stage, index) => (
                      <div key={index} className={`d-flex align-items-center p-3 rounded mb-3 ${index < processingStage
                        ? 'bg-light-success text-success'
                        : index === processingStage
                          ? 'bg-light-primary text-primary'
                          : 'bg-light text-muted'
                        }`}>
                        {index < processingStage ? (
                          <CheckCircle className="me-3" size={20} />
                        ) : index === processingStage ? (
                          <div className="spinner-border text-primary me-3" style={{ width: 20, height: 20 }} />
                        ) : (
                          <Clock className="me-3" size={20} />
                        )}
                        <span className="fw-semibold">{stage}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Content>
    );
  }

  return (
    <Content>
      <div className="d-flex flex-column gap-6 mx-auto">
        <div>
          <button
            onClick={onBack}
            className="btn btn-clean btn-sm btn-active-color-primary d-flex align-items-center"
          >
            <ArrowLeft className="me-2" />
            Back to Dashboard
          </button>
        </div>

        {/* Claim Status Card */}
        <div className="card shadow-sm">
          <div className="card-header bg-light-success">
            <h3 className="card-title">{claimResult.status === 'success' ? 'Report Generated Successfully!' : 'Claim Status'}</h3>
          </div>
          <div className="card-body">
            <div className="d-flex flex-column align-items-center text-center mb-6">
              <div className="symbol symbol-70px mb-4">
                <div className="symbol-label bg-success d-flex justify-content-center align-items-center">
                  <CheckCircle className="text-white" size={28} />
                </div>
              </div>
              <p className="text-muted">{claimResult.analysis?.executive_summary || 'Your insurance claim report has been processed.'}</p>
            </div>

            <div className="row g-5">
              {/* Claim Details */}
              <div className="col-md-6">
                <div className="card bg-light-info">
                  <div className="card-body">
                    <h4 className="card-title">Claim Details</h4>
                    <div className="d-flex flex-column gap-3">
                      <div className="d-flex justify-content-between"><span>Policy Number:</span><strong>{claimResult.analysis?.policy_details?.['Policy Number'] || '-'}</strong></div>
                      <div className="d-flex justify-content-between"><span>Policy Holder:</span><strong>{claimResult.analysis?.policy_details?.Holder || '-'}</strong></div>
                      <div className="d-flex justify-content-between"><span>Date of Loss:</span><strong>{claimResult.analysis?.claim_details?.['Date of Loss'] || '-'}</strong></div>
                      <div className="d-flex justify-content-between"><span>Policy Suggestion:</span><strong>{claimResult.analysis?.policy_suggestion || '-'}</strong></div>
                      <div className="d-flex justify-content-between"><span>Estimated Claim:</span><strong>{claimResult.analysis?.estimated_claim || '-'}</strong></div>
                      <div className="d-flex justify-content-between"><span>Status:</span>
                        <span className={`badge ${claimResult.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                          {claimResult.status || '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="col-md-6">
                <div className="card bg-light-primary">
                  <div className="card-body">
                    <h4 className="card-title">Description</h4>
                    <p>{claimResult.analysis?.claim_details?.Description || 'No description available.'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Claims Report */}
            {claimResult.claims_report && (
              <div className="card mt-6">
                <div className="card-header">
                  <h4 className="card-title">Claims Report</h4>
                </div>
                <div className="card-body font-monospace text-black dark:text-white">
                  {claimResult.claims_report
                    // Remove the word 'markdown'
                    .replace(/markdown/gi, '')
                    // Remove only heading symbols (#)
                    .replace(/^#+\s*/gm, '')
                    // Split by headings (lines ending with ':') to create sections
                    .split(/\n(?=[A-Za-z ].*?:)/)
                    // Skip the first section (index 0)
                    .slice(1)
                    .map((section, index) => {
                      const lines = section.split('\n');
                      const heading = lines[0].trim();
                      const content = lines.slice(1).join('\n');

                      return (
                        <div key={index} className="mb-4">
                          {/* Heading bold + red */}
                          <div style={{ color: 'red', fontWeight: 'bold', fontSize: '1.125rem', marginBottom: '0.25rem' }}>
                            {heading}
                          </div>

                          {/* Section content */}
                          <pre className="whitespace-pre-wrap text-black dark:text-white m-0">
                            {content}
                          </pre>

                          {/* Horizontal line after section */}
                          <hr className="border-t border-gray-400 mt-2 mb-2" />
                        </div>
                      );
                    })}
                </div>
              </div>
            )}





            {/* Claim Details Table */}
            {claimResult.table_rows && claimResult.table_rows.length > 0 && (
              <div className="card mt-6">
                <div className="card-header">
                  <h4 className="card-title">Claim Details Table</h4>
                </div>
                <div className="card-body table-responsive">
                  <table className="table table-bordered table-hover">
                    <thead className="table-light">
                      <tr>
                        {Object.keys(claimResult.table_rows[0]).map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {claimResult.table_rows.map((row: any, idx: number) => (
                        <tr key={idx}>
                          {Object.values(row).map((val: any, i: number) => (
                            <td key={i}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Submitted Documents */}
            {documents.some(doc => doc.uploaded) && (
              <div className="card mt-6">
                <div className="card-header">
                  <h4 className="card-title">Submitted Documents</h4>
                </div>
                <div className="card-body row g-3">
                  {documents
                    .filter(doc => doc.uploaded) // ✅ Show only uploaded ones
                    .map(doc => (
                      <div
                        key={doc.id}
                        className="col-md-4 d-flex align-items-center p-3 bg-light rounded"
                      >
                        <FileText className="me-3" />
                        <div>
                          <p className="mb-1 fw-semibold">{doc.name}</p>
                          <span className="badge badge-success">Verified</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="d-flex justify-content-center mt-6">
              <button onClick={onBack} className="btn btn-light-primary btn-lg">New Claim</button>
            </div>
          </div>
        </div>
      </div>
    </Content>
  );
};

export default ProcessingResults;
