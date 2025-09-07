import React, { useRef, useEffect } from "react";
import { Send, Upload } from "lucide-react";
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

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const newFiles: FileItem[] = selectedFiles.map(file => ({
        id: Date.now().toString() + Math.random().toString(),
        name: file.name,
        type: file.type,
        status: "success", // 直接设为成功状态
        size: formatFileSize(file.size),
        progress: 100,
        file,
        url: null
      }));
      setFiles([...files, ...newFiles]);

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
          const newFile: FileItem = {
            id: Date.now().toString() + Math.random().toString(),
            name: file.name || 'pasted-image.png',
            type: file.type,
            status: "success",
            size: formatFileSize(file.size),
            progress: 100,
            file,
            url: null
          };
          setFiles([...files, newFile]);
        }
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      const newFiles: FileItem[] = droppedFiles.map(file => ({
        id: Date.now().toString() + Math.random().toString(),
        name: file.name,
        type: file.type,
        status: "success",
        size: formatFileSize(file.size),
        progress: 100,
        file,
        url: null
      }));
      setFiles([...files, ...newFiles]);
    }
  };

  const handleSend = () => {
    if (inputText.trim() || files.length > 0) {
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
        {/* 文件预览区域 */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map(file => (
              <div key={file.id} className={`flex items-center space-x-2 px-3 py-2 ${themeConfig.cardClasses} border rounded-lg`}>
                <span className="text-sm truncate max-w-32">{file.name}</span>
                <button
                  onClick={() => setFiles(files.filter(f => f.id !== file.id))}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  ✕
                </button>
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
            disabled={!inputText.trim() && files.length === 0}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-2xl transition-all duration-200 font-medium ${
              (inputText.trim() || files.length > 0)
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