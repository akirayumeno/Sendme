import React, { useRef, useEffect, useState } from "react";
import {File, Image as ImageIcon, FileVideo, FileAudio, FileText, X, Upload, Send, CheckCheck} from "lucide-react";
import {FileItem, FileStatus, ThemeConfig} from "../../types/type.tsx";

interface InputAreaProps {
  inputText: string;
  setInputText: (text: string) => void;
  files: FileItem[];
  setFiles: (files: FileItem[] | ((prev: FileItem[]) => FileItem[])) => void;
  onSend: () => void;
  themeConfig: ThemeConfig;
  isUploading?: boolean;
}

// Get file icon based on file name and type
const getFileIcon = (fileName: string, fileType: string) => {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';

  const iconMap: Record<string, React.ReactNode> = {
    // Document types
    'pdf': <FileText className="w-5 h-5 text-white" />,
    'doc': <FileText className="w-5 h-5 text-white" />,
    'docx': <FileText className="w-5 h-5 text-white" />,
    'xls': <FileText className="w-5 h-5 text-white" />,
    'xlsx': <FileText className="w-5 h-5 text-white" />,

    // Image types
    'jpg': <ImageIcon className="w-5 h-5 text-white" />,
    'jpeg': <ImageIcon className="w-5 h-5 text-white" />,
    'png': <ImageIcon className="w-5 h-5 text-white" />,
    'gif': <ImageIcon className="w-5 h-5 text-white" />,

    // Video types
    'mp4': <FileVideo className="w-5 h-5 text-white" />,
    'mov': <FileVideo className="w-5 h-5 text-white" />,

    // Audio types
    'mp3': <FileAudio className="w-5 h-5 text-white" />,
    'wav': <FileAudio className="w-5 h-5 text-white" />,
  };

  return iconMap[extension] || (
    fileType.startsWith('image/') ? <ImageIcon className="w-5 h-5 text-white" /> :
    fileType.startsWith('video/') ? <FileVideo className="w-5 h-5 text-white" /> :
    fileType.startsWith('audio/') ? <FileAudio className="w-5 h-5 text-white" /> :
    <File className="w-5 h-5 text-white" />
  );
};

// Enhanced progress component with hover cancel and theme support
interface CircularProgressProps {
  progress: number;
  size?: number;
  onCancel?: () => void;
  fileName?: string;
  themeConfig: ThemeConfig;
}

const CircularProgress = ({ progress, size = 40, onCancel, fileName, themeConfig }: CircularProgressProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const radius = (size - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const handleCancel = () => {
    if (onCancel && window.confirm(`Are you sure you want to cancel uploading "${fileName}"?`)) {
      onCancel();
    }
  };

  return (
    <div
      className="relative cursor-pointer transition-transform hover:scale-105"
      style={{ width: size, height: size }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCancel}
    >
      {!isHovered ? (
        // Show progress circle
        <>
          <svg
            className="transform -rotate-90"
            width={size}
            height={size}
            viewBox={`0 0 ${size} ${size}`}
          >
            {/* Background circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="currentColor"
              strokeWidth="3"
              fill="transparent"
              className={themeConfig.cardClasses === 'bg-gray-800 border-gray-700'
                ? 'text-gray-600'
                : 'text-gray-300'
              }
            />
            {/* Progress circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="currentColor"
              strokeWidth="3"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={`transition-all duration-300 ease-in-out ${
                themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                  ? 'text-blue-400' 
                  : 'text-blue-500'
              }`}
              strokeLinecap="round"
            />
          </svg>
          {/* Center percentage text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-xs font-medium ${
              themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                ? 'text-gray-300' 
                : 'text-gray-700'
            }`}>
              {Math.round(progress)}%
            </span>
          </div>
        </>
      ) : (
        // Show cancel button
        <div className={`w-full h-full rounded-full flex items-center justify-center transition-colors duration-200 shadow-lg ${
          themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
            ? 'bg-red-600 hover:bg-red-700' 
            : 'bg-red-500 hover:bg-red-600'
        }`}>
          <X className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
};

const InputArea: React.FC<InputAreaProps> = ({
  inputText,
  setInputText,
  files,
  setFiles,
  onSend,
  themeConfig,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const uploadingFiles = useRef<Set<string>>(new Set());

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  // Simulate file upload progress
  const simulateUploadProgress = (fileId: string) => {
    uploadingFiles.current.add(fileId);

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15 + 5; // Random increment 5-20%

      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);

        // Update file status to success
        setFiles(prevFiles =>
          prevFiles.map(file =>
            file.id === fileId
              ? { ...file, status: 'success', progress: 100 }
              : file
          )
        );

        uploadingFiles.current.delete(fileId)
      } else {
        // Update progress
        setFiles(prevFiles =>
          prevFiles.map(file =>
            file.id === fileId
              ? { ...file, progress: Math.round(progress) }
              : file
          )
        );
      }
    }, 200);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const newFiles: FileItem[] = selectedFiles.map(file => {
        const fileId = Date.now().toString() + Math.random().toString();
        return {
          id: fileId,
          name: file.name,
          type: file.type,
          status: "uploading" as FileStatus,
          size: formatFileSize(file.size),
          progress: 0,
          file,
          url: URL.createObjectURL(file), // Add display URL
        };
      });

      setFiles([...files, ...newFiles]);

      // Start simulating upload progress
      newFiles.forEach(file => {
        setTimeout(() => simulateUploadProgress(file.id), 100);
      });

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handlePaste = async (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;

    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        if (file) {
          const fileId = Date.now().toString() + Math.random().toString();
          const newFile: FileItem = {
            id: fileId,
            name: file.name || 'pasted-image.png',
            type: file.type,
            status: "uploading" as FileStatus,
            size: formatFileSize(file.size),
            progress: 0,
            file,
            url: URL.createObjectURL(file),
          };
          setFiles([...files, newFile]);
          setTimeout(() => simulateUploadProgress(fileId), 100);
        }
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      const newFiles: FileItem[] = droppedFiles.map(file => {
        const fileId = Date.now().toString() + Math.random().toString();
        return {
          id: fileId,
          name: file.name,
          type: file.type,
          status: "uploading" as const,
          size: formatFileSize(file.size),
          progress: 0,
          file,
          url: URL.createObjectURL(file),
        };
      });
      setFiles([...files, ...newFiles]);

      newFiles.forEach(file => {
        setTimeout(() => simulateUploadProgress(file.id), 100);
      });
    }
  };

  const removeFile = (fileId: string) => {
    // Find the file to be deleted and clean up URL
    const fileToRemove = files.find(f => f.id === fileId);
    if (fileToRemove?.url && fileToRemove.url.startsWith('blob:')) {
      URL.revokeObjectURL(fileToRemove.url);
    }

    setFiles(files.filter(f => f.id !== fileId));
    uploadingFiles.current.delete(fileId);
  };

  // Handle upload cancellation
  const handleCancelUpload = (fileId: string) => {
    setFiles(prevFiles =>
      prevFiles.map(file =>
        file.id === fileId
          ? { ...file, status: 'error' as FileStatus, error: 'Upload cancelled by user' }
          : file
      )
    );
  };

  const handleSend = () => {
    if (inputText.trim() || files.some(f => f.status === 'success')) {
      onSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [inputText]);

  return (
    <div className={`${themeConfig.cardClasses} border-t p-4 sticky bottom-0`}>
      <div className="space-y-3">
        {/* File upload area */}
        {files.length > 0 && (
          <div className="space-y-3">
            {files.map(file => (
              <div key={file.id} className={`p-4 ${themeConfig.cardClasses} border rounded-xl shadow-sm`}>
                <div className="flex items-center justify-between">
                  {/* Left side: File icon and info */}
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      {file.type.startsWith('image/') && file.url ? (
                        <img
                          src={file.url}
                          alt={file.name}
                          className="w-10 h-10 object-cover rounded"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-500 dark:bg-gray-600 rounded-full flex items-center justify-center">
                          {getFileIcon(file.name, file.type)}
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${
                        themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                          ? 'text-gray-100' 
                          : 'text-gray-900'
                      }`}>
                        {file.name}
                      </p>
                      <p className={`text-xs ${
                        themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                          ? 'text-gray-400' 
                          : 'text-gray-500'
                      }`}>
                        {file.size}
                        {file.status === 'uploading' && ' • Uploading...'}
                        {file.status === 'success' && ' • Complete'}
                        {file.status === 'error' && ' • Failed'}
                      </p>
                      {file.error && (
                        <p className={`text-xs mt-1 ${
                          themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                            ? 'text-red-400' 
                            : 'text-red-500'
                        }`}>
                          {file.error}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right side: Progress bar or status */}
                  <div className="flex-shrink-0 ml-3">
                    {file.status === 'uploading' ? (
                      <CircularProgress
                        progress={file.progress || 0}
                        onCancel={() => handleCancelUpload(file.id)}
                        fileName={file.name}
                        themeConfig={themeConfig}
                      />
                    ) : file.status === 'success' ? (
                        <CheckCheck className={`w-5 h-5 ${
                            themeConfig.cardClasses === 'bg-gray-800 border-gray-700'
                                ? 'text-green-500'
                                : 'text-green-600'
                        }`} />
                    ) : file.status === 'error' ? (
                      <button
                        onClick={() => removeFile(file.id)}
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                          themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                            ? 'bg-red-600 hover:bg-red-700' 
                            : 'bg-red-500 hover:bg-red-600'
                        }`}
                      >
                        <X className="w-5 h-5 text-white" />
                      </button>
                    ) : (
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                          ? 'bg-gray-600' 
                          : 'bg-gray-300'
                      }`}>
                        <span className={`text-sm ${
                          themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                            ? 'text-gray-400' 
                            : 'text-gray-500'
                        }`}>⏳</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Input textarea */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPaste={handlePaste}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault(); // Prevent default line break behavior
              handleSend();
            }
          }}
            placeholder="Type a message, or drag & drop files..."
            className={`w-full p-3 border rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${themeConfig.inputClasses}`}
            rows={2}
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
        </div>

        {/* Action buttons */}
        <div className="flex space-x-2">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileInputChange}
            className="hidden"
            accept="*/*"
            multiple
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 border rounded-2xl transition-all duration-200 focus:outline-none ${
              themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                ? 'border-gray-600 text-white bg-gray-600 hover:bg-gray-700 hover:text-white active:bg-gray-600'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 active:bg-gray-100'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span className="font-medium">Upload</span>
          </button>

          <button
            onClick={handleSend}
            disabled={!inputText.trim() && !files.some(f => f.status === 'success')}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-2xl transition-all duration-200 font-medium ${
              (inputText.trim() || files.some(f => f.status === 'success'))
                ? 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white'
                : themeConfig.cardClasses === 'bg-gray-800 border-gray-700'
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputArea;