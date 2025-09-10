import React, { useRef, useEffect, useState } from "react";
import { Send, Upload, X, File, Image as ImageIcon } from "lucide-react";
import { FileItem, ThemeConfig } from "../../types/type.tsx";

interface InputAreaProps {
  inputText: string;
  setInputText: (text: string) => void;
  files: FileItem[];
  setFiles: (files: FileItem[]) => void;
  onSend: () => void;
  themeConfig: ThemeConfig;
  isUploading?: boolean;
}


// 圆形进度条组件
const CircularProgress = ({ progress, size = 40 }: { progress: number; size?: number }) => {
  const radius = (size - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* 背景圆圈 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth="3"
          fill="transparent"
          className="text-gray-300 dark:text-gray-600"
        />
        {/* 进度圆圈 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth="3"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="text-blue-500 transition-all duration-300 ease-in-out"
          strokeLinecap="round"
        />
      </svg>
      {/* 中心百分比文字 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
          {Math.round(progress)}%
        </span>
      </div>
    </div>
  );
};

const InputArea: React.FC<InputAreaProps> = ({
  inputText,
  setInputText,
  onSend,
  themeConfig,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [uploadingFiles, setUploadingFiles] = useState<Set<string>>(new Set());
  const [files, setFiles] = useState<FileItem[]>([]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  // 模拟文件上传进度
  const simulateUploadProgress = (fileId: string) => {
    setUploadingFiles(prev => new Set(prev).add(fileId));

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15 + 5; // 随机增长5-20%

      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);

        // 更新文件状态为成功
        setFiles(prevFiles =>
          prevFiles.map(file =>
            file.id === fileId
              ? { ...file, status: 'success', progress: 100 }
              : file
          )
        );

        setUploadingFiles(prev => {
          const newSet = new Set(prev);
          newSet.delete(fileId);
          return newSet;
        });
      } else {
        // 更新进度
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
          status: "uploading",
          size: formatFileSize(file.size),
          progress: 0,
          file,
          url: null
        };
      });

      setFiles([...files, ...newFiles]);

      // 开始模拟上传进度
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
            status: "uploading",
            size: formatFileSize(file.size),
            progress: 0,
            file,
            url: null
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
          status: "uploading",
          size: formatFileSize(file.size),
          progress: 0,
          file,
          url: null
        };
      });
      setFiles([...files, ...newFiles]);

      newFiles.forEach(file => {
        setTimeout(() => simulateUploadProgress(file.id), 100);
      });
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(files.filter(f => f.id !== fileId));
    setUploadingFiles(prev => {
      const newSet = new Set(prev);
      newSet.delete(fileId);
      return newSet;
    });
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
        {/* 改进的文件预览区域 */}
        {files.length > 0 && (
          <div className="space-y-3">
            {files.map(file => (
              <div key={file.id} className={`p-4 ${themeConfig.cardClasses} border rounded-xl shadow-sm`}>
                <div className="flex items-center space-x-4">
                  {/* 文件图标或进度条 */}
                  <div className="flex-shrink-0">
                    {file.status === 'uploading' ? (
                      <CircularProgress progress={file.progress || 0} />
                    ) : (
                      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
                        {file.type.startsWith('image/') ? (
                          <ImageIcon className="w-5 h-5 text-white" />
                        ) : (
                          <File className="w-5 h-5 text-white" />
                        )}
                      </div>
                    )}
                  </div>

                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium truncate max-w-48">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {file.size}
                        </p>
                      </div>

                      {/* 状态指示器 */}
                      <div className="flex items-center space-x-2">
                        {file.status === 'success' && (
                          <div className="flex items-center space-x-1 text-green-600 dark:text-green-400">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-xs font-medium">Ready</span>
                          </div>
                        )}

                        {file.status === 'uploading' && (
                          <div className="flex items-center space-x-1 text-blue-600 dark:text-blue-400">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            <span className="text-xs font-medium">Uploading...</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 改进的删除按钮 */}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-2 rounded-full transition-all duration-200 hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400"
                    aria-label="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 文本输入框 */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPaste={handlePaste}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            placeholder="Type a message, paste an image, or drag & drop files..."
            className={`w-full p-3 border rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${themeConfig.inputClasses}`}
            rows={1}
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
        </div>

        {/* 操作按钮 */}
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
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 border rounded-2xl transition-all duration-200 ${
              themeConfig.cardClasses === 'bg-gray-800 border-gray-700' 
                ? 'border-gray-600 hover:bg-gray-700 active:bg-gray-600' 
                : 'border-gray-300 hover:bg-gray-50 active:bg-gray-100'
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