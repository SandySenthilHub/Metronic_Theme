import React, { useState } from 'react';
import { ArrowLeft, Shield, Upload, FileText, X, Check, ShieldBanIcon } from 'lucide-react';
import axios from 'axios';
import { Content } from '../../../_metronic/layout/components/content';
import { useNavigate } from 'react-router-dom';

interface WorkshopSuggestionProps {
    onBack: () => void;
}

interface WorkshopDocument {
    id: string;
    name: string;
    file?: File;
    uploaded: boolean;
}

const BACKEND_URL = " http://127.0.0.1:8000";

const WorkshopSuggestion: React.FC<WorkshopSuggestionProps> = ({ onBack }) => {

    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState(1);
    const [workshops, setWorkshops] = useState<WorkshopDocument[]>([
        { id: 'workshop1', name: 'Workshop 1', uploaded: false },
        { id: 'workshop2', name: 'Workshop 2', uploaded: false },
        { id: 'workshop3', name: 'Workshop 3', uploaded: false },
    ]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisComplete, setAnalysisComplete] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);

    const handleFileUpload = (workshopId: string, file: File) => {
        setWorkshops(prev =>
            prev.map(workshop =>
                workshop.id === workshopId
                    ? { ...workshop, uploaded: true, file }
                    : workshop
            )
        );
    };

    const handleFileRemove = (workshopId: string) => {
        setWorkshops(prev =>
            prev.map(workshop =>
                workshop.id === workshopId
                    ? { ...workshop, uploaded: false, file: undefined }
                    : workshop
            )
        );
    };

    const allUploaded = workshops.every(w => w.uploaded);

    const handleAnalyze = async () => {
        if (!allUploaded) return;

        setIsAnalyzing(true);
        setAnalysisComplete(false);

        try {
            const formData = new FormData();
            workshops.forEach(w => {
                if (w.file) formData.append(w.id, w.file);
            });

            const response = await axios.post(`${BACKEND_URL}/workshop_suggestion/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            if (response.data.status === "success") {
                setAnalysisResult(response.data.workshop_report);
                setAnalysisComplete(true);
            } else {
                alert("No valid workshop report received from backend.");
                console.error(response.data);
            }
        } catch (err: any) {
            console.error("Backend error:", err);
            alert(`Error analyzing workshops: ${err.message}`);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const currentWorkshop = workshops.find(w => w.id === `workshop${activeTab}`);

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


                {/* Card */}
                <div className="card card-flush shadow-sm p-8">

                    <div className="card-header py-4 bg-light-primary">
                        <div className="d-flex align-items-center">
                            <div className="symbol symbol-70px me-5 bg-light-primary">
                                <FileText className="text-primary" />
                            </div>
                            <div>
                                <h2 className="fw-bold text-gray-800">Workshop Suggestion</h2>
                                <p className="text-gray-600">Upload 3 workshop summaries for car damage analysis and suggestion.</p>
                            </div>
                        </div>
                    </div>

                    <div className="card-body py-8">
                        {/* Tabs */}
                        <div className="d-flex gap-3 mb-8">
                            {workshops.map((workshop, index) => (
                                <button
                                    key={workshop.id}
                                    onClick={() => setActiveTab(index + 1)}
                                    className={`btn btn-sm d-flex align-items-center gap-2
                  ${activeTab === index + 1 ? 'btn-primary' : 'btn-light'}`
                                    }
                                >
                                    {workshop.name}
                                    {workshop.uploaded && <Check className="w-4 h-4 text-success" />}
                                </button>
                            ))}
                        </div>

                        {/* Upload Section */}
                        <div className="mb-8">
                            <h3 className="fw-semibold mb-4">Upload {currentWorkshop?.name} Summary (PDF/Image)</h3>
                            {!currentWorkshop?.uploaded ? (
                                <div
                                    className="border border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer"
                                    onDragOver={(e) => e.preventDefault()}
                                    onDrop={(e) => {
                                        e.preventDefault();
                                        if (e.dataTransfer.files.length > 0) handleFileUpload(currentWorkshop.id, e.dataTransfer.files[0]);
                                    }}
                                >
                                    <input
                                        type="file"
                                        accept=".pdf,.jpg,.jpeg,.png"
                                        className="d-none"
                                        id={`file-${currentWorkshop?.id}`}
                                        onChange={(e) => {
                                            if (e.target.files && e.target.files[0]) handleFileUpload(currentWorkshop.id, e.target.files[0]);
                                        }}
                                    />
                                    <label htmlFor={`file-${currentWorkshop?.id}`} className="d-block cursor-pointer">
                                        <div className="d-flex flex-column align-items-center gap-4">
                                            <div className="symbol symbol-70px bg-light-gray d-flex align-items-center justify-content-center">
                                                <Upload className="text-gray-500" />
                                            </div>
                                            <p className="fw-semibold text-gray-700">Drag and drop file here</p>
                                            <p className="text-gray-500">Limit 50MB per file • PDF, JPG, PNG, JPEG</p>
                                            <button type="button" className="btn btn-primary">Browse files</button>
                                        </div>
                                    </label>
                                </div>
                            ) : (
                                <div className="alert alert-success d-flex justify-content-between align-items-center">
                                    <div className="d-flex align-items-center gap-3">
                                        <FileText className="text-success" />
                                        <div>
                                            <p className="fw-semibold mb-1">{currentWorkshop.file?.name}</p>
                                            <p className="text-gray-600 mb-0">{(currentWorkshop.file.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    </div>
                                    <button onClick={() => handleFileRemove(currentWorkshop.id)} className="btn btn-sm btn-light-danger">
                                        <X />
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Analyze Button */}
                        <div className="d-flex justify-content-center">
                            <button
                                onClick={handleAnalyze}
                                disabled={!allUploaded || isAnalyzing}
                                className="btn btn-danger btn-lg d-flex align-items-center gap-3"
                            >
                                {isAnalyzing ? (
                                    <span className="spinner-border spinner-border-sm"></span>
                                ) : (
                                    <>
                                        <Shield />
                                        Analyze Workshops
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Analysis Results */}
                        {analysisComplete && analysisResult && (
                            <div className="mt-8 row g-6">
                                {(() => {
                                    const sections = analysisResult.split("## ").filter(Boolean);
                                    const workshopSections: any[] = [];
                                    let comparisonText = "";
                                    let suggestedText = "";

                                    sections.forEach((section) => {
                                        const titleEnd = section.indexOf(":");
                                        const title = titleEnd !== -1 ? section.slice(0, titleEnd).trim() : section.split("\n")[0].trim();
                                        const content = titleEnd !== -1 ? section.slice(titleEnd + 1).trim() : section.replace(title, "").trim();

                                        if (title.startsWith("Workshop")) workshopSections.push({ title, content });
                                        else if (title.toLowerCase().includes("comparison")) comparisonText = content;
                                        else if (title.toLowerCase().includes("suggested")) suggestedText = content;
                                    });

                                    return (
                                        <>
                                            {workshopSections.map((ws, idx) => (
                                                <div key={idx} className="col-md-6 col-lg-4">
                                                    <div className="card card-flush shadow-sm p-6">
                                                        <h4 className="fw-semibold mb-3">{ws.title}</h4>
                                                        <p className="text-gray-700">{ws.content}</p>
                                                    </div>
                                                </div>
                                            ))}

                                            {comparisonText && (
                                                <div className="col-12">
                                                    <div className="card card-flush bg-warning-light p-6">
                                                        <h4 className="fw-semibold mb-3">Comparison</h4>
                                                        <p className="text-gray-700">{comparisonText}</p>
                                                    </div>
                                                </div>
                                            )}

                                            {suggestedText && (
                                                <div className="col-12">
                                                    <div className="card card-flush bg-success-light p-6">
                                                        <h4 className="fw-semibold mb-3">Suggested Workshop</h4>
                                                        <p className="text-gray-700">{suggestedText}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </>
                                    );
                                })()}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Content>
    );
};

export default WorkshopSuggestion;
