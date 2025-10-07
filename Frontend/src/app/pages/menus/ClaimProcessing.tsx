import React, { useState } from 'react';
import { ArrowLeft, Shield, Upload, Check, ShieldAlert } from 'lucide-react';
import { DocumentType } from '../types';
import DocumentUpload from './DocumentUpload';
import { Content } from '../../../_metronic/layout/components/content';
import { Card1 } from '../../../_metronic/partials/content/cards/Card1';
import { useNavigate } from 'react-router-dom';

interface ClaimProcessingProps {
    onBack: () => void;
    onProcessClaim: (documents: DocumentType[]) => void;
}



const ClaimProcessing: React.FC<ClaimProcessingProps> = ({ onBack, onProcessClaim }) => {
    const navigate = useNavigate();

    const [selectedTab, setSelectedTab] = useState('emirates_id');
    const [documents, setDocuments] = useState<DocumentType[]>([
        { id: 'emirates_id', name: 'Emirates ID', description: 'Valid Emirates ID (Image/PDF)', required: true, uploaded: false },
        { id: 'driving_license', name: 'Driving License', description: 'Valid UAE Driving License', required: true, uploaded: false },
        { id: 'vehicle_registry', name: 'Vehicle Registration', description: 'Vehicle registration documents', required: true, uploaded: false },
        { id: 'policy-document', name: 'Policy Document', description: 'Insurance policy document', required: true, uploaded: false },
        { id: 'police_report', name: 'Police Report', description: 'Official police report for the incident', required: false, uploaded: false },
        { id: 'claim_form', name: 'Claim Form', description: 'Completed claim form', required: true, uploaded: false },
        { id: 'damaged_photos', name: 'Damaged Photos', description: 'Photos of vehicle damage', required: true, uploaded: false },
    ]);

    const handleFileUpload = (docId: string, file: File | File[]) => {
        setDocuments(prev => prev.map(doc => doc.id === docId ? { ...doc, uploaded: true, file } : doc));
    };

    const handleFileRemove = (docId: string) => {
        setDocuments(prev => prev.map(doc => doc.id === docId ? { ...doc, uploaded: false, file: undefined } : doc));
    };

    const uploadedCount = documents.filter(doc => doc.uploaded).length;
    const canProcessClaim = documents.filter(doc => doc.required).every(doc => doc.uploaded);
    const remainingRequired = documents.filter(doc => doc.required && !doc.uploaded).length;

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

                <div className="card card-flush shadow-sm p-8">

                    <div className="card-header py-4 bg-light-primary">
                        <div className="d-flex align-items-center">
                            <div className="symbol symbol-70px me-3 bg-light-primary">
                                <ShieldAlert className="text-primary" />
                            </div>
                            <div>
                                <h2 className="fw-bold text-gray-800">Claim Processing</h2>
                                <p className="text-gray-600">Upload required documents for claim analysis.</p>
                            </div>
                        </div>
                    </div>


                    {/* Progress Bar */}
                    <div className="mb-6 mt-8">
                        <div className="d-flex justify-content-between mb-4">
                            <span className="fw-semibold text-gray-700 fs-7">Document Upload Progress</span>
                            <span className="text-gray-500 fs-8" style={{ marginLeft: "8px" }} >{uploadedCount}/{documents.length} completed</span>
                        </div>
                        <div className="h-5px w-100 bg-light rounded">
                            <div className="bg-primary rounded h-5px" style={{ width: `${(uploadedCount / documents.length) * 100}%`, transition: 'all 0.3s' }}></div>
                        </div>
                    </div>

                    {/* Document Tabs */}
                    <div className="d-flex flex-wrap gap-3">
                        {documents.map(doc => (
                            <button
                                key={doc.id}
                                onClick={() => setSelectedTab(doc.id)}
                                className={`btn btn-sm d-flex align-items-center gap-2 fs-7 fw-semibold ${selectedTab === doc.id ? 'btn-light-primary' : 'btn-light'} ${doc.uploaded ? 'btn-active-light-success' : ''}`}
                            >
                                {doc.name}
                                {doc.uploaded && <Check className="text-success" size={16} />}
                                {doc.required && !doc.uploaded && <span className="text-danger">*</span>}
                            </button>
                        ))}
                    </div>

                    <div className="card-body pt-8">
                        {/* Current Document Upload */}
                        <DocumentUpload
                            document={documents.find(doc => doc.id === selectedTab)!}
                            onFileUpload={handleFileUpload}
                            onFileRemove={handleFileRemove}
                        />

                        {/* Process Claim Button */}
                        <div className="mt-8 d-flex justify-content-center">
                            <button
                                onClick={() => canProcessClaim && onProcessClaim(documents)}
                                disabled={!canProcessClaim}
                                className="btn btn-primary fw-bold btn-shadow-sm"
                            >
                                <Upload className="me-2" />
                                {canProcessClaim ? 'Process Claim' : `Upload ${remainingRequired} more required document${remainingRequired === 1 ? '' : 's'}`}
                            </button>
                        </div>
                    </div>
                </div>

                <div className="text-center mt-6">
                    <p className="fs-8 text-gray-500 d-flex align-items-center justify-content-center gap-2">
                        <div className="w-5px h-5px rounded-circle bg-danger"></div> Insurance AI Application
                    </p>
                </div>
            </div>
        </Content>
    );
};

export default ClaimProcessing;
