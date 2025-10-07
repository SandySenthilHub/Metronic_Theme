import React, { useCallback } from 'react';
import { Upload, FileText, X, Check } from 'lucide-react';
import { DocumentType } from '../types';

interface DocumentUploadProps {
  document: DocumentType;
  onFileUpload: (docId: string, file: File | File[], index?: number) => void;
  onFileRemove: (docId: string, fileIndex?: number) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  document,
  onFileUpload,
  onFileRemove
}) => {
  const isMultiple = document.id === 'damaged_photos';
  const uploadedFiles: File[] = Array.isArray(document.file) ? document.file : document.file ? [document.file] : [];

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const files = Array.from(e.dataTransfer.files);
    if (isMultiple) {
      const newFiles = [...uploadedFiles, ...files].slice(0, 5);
      onFileUpload(document.id, newFiles);
    } else if (files.length > 0) {
      onFileUpload(document.id, files[0]);
    }
  }, [document.id, onFileUpload, uploadedFiles, isMultiple]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (isMultiple) {
      const newFiles = [...uploadedFiles, ...files].slice(0, 5);
      onFileUpload(document.id, newFiles);
    } else if (files.length > 0) {
      onFileUpload(document.id, files[0]);
    }
  }, [document.id, onFileUpload, uploadedFiles, isMultiple]);

  const handleRemoveFile = (index: number) => {
    if (isMultiple) {
      const newFiles = [...uploadedFiles];
      newFiles.splice(index, 1);
      onFileUpload(document.id, newFiles);
    } else {
      onFileRemove(document.id);
    }
  };

  return (
    <div className="mb-8">
      <h3 className="fw-semibold mb-4">
        Upload {document.name} {document.required && <span className="text-danger">*</span>}
      </h3>

      {!uploadedFiles.length ? (
        <div
          className="border border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-primary transition-colors"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.pdf"
            multiple={isMultiple}
            onChange={handleFileSelect}
            className="d-none"
            id={`file-${document.id}`}
          />
          <label htmlFor={`file-${document.id}`} className="d-block cursor-pointer">
            <div className="d-flex flex-column align-items-center gap-4">
              <div className="symbol symbol-70px bg-light-gray d-flex align-items-center justify-content-center">
                <Upload className="text-gray-500" />
              </div>
              <p className="fw-semibold text-gray-700">Drag and drop file{isMultiple ? 's' : ''} here</p>
              <p className="text-gray-500">Limit 200MB per file • JPG, PNG, PDF, JPEG</p>
              <button type="button" className="btn btn-primary" >Browse files</button>
            </div>
          </label>
        </div>
      ) : (
        <div className="space-y-3">
          {uploadedFiles.map((file, index) => (
            <div
              key={index}
              className="alert alert-success d-flex justify-content-between align-items-center"
            >
              <div className="d-flex align-items-center gap-3">
                <FileText className="text-primary" />
                <div>
                  <p className="fw-semibold mb-1">{file.name}</p>
                  <p className="text-gray-600 mb-0">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button
                onClick={() => handleRemoveFile(index)}
                className="btn btn-sm btn-light-danger"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
