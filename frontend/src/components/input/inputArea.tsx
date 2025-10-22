import React, {useEffect, useRef} from "react";
import {Send, Upload} from "lucide-react";
import {ThemeConfig} from "../../types/type.tsx";

interface InputAreaProps {
    inputText: string;
    setInputText: (text: string) => void;
    onTextSend: () => void;
    onFileUpload: (files: File[]) => void;
    themeConfig: ThemeConfig;
}

const InputArea: React.FC<InputAreaProps> = ({
                                                 inputText,
                                                 setInputText,
                                                 onTextSend,
                                                 onFileUpload,
                                                 themeConfig,
                                             }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const selectedFiles = Array.from(e.target.files);
            onFileUpload(selectedFiles);

            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handlePaste = async (e: React.ClipboardEvent) => {
        const items = e.clipboardData.items;
        const pastedFiles: File[] = [];

        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                if (file) {
                    // Create a new File with a proper name for pasted images
                    const renamedFile = new File([file], 'pasted-image.png', {type: file.type});
                    pastedFiles.push(renamedFile);
                }
            }
        }

        if (pastedFiles.length > 0) {
            onFileUpload(pastedFiles);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const droppedFiles = Array.from(e.dataTransfer.files);

        if (droppedFiles.length > 0) {
            onFileUpload(droppedFiles);
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
        <div className="space-y-4">
            <div className="max-w-[50rem] mx-auto">
                <div className={`${themeConfig.cardClasses} border p-4 rounded-3xl bottom-0`}>
                    <div className="space-y-3">
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
                  if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                      e.preventDefault();
                      onTextSend();
                  }
              }}
              placeholder="Type a message, or drag & drop files..."
              className={`w-full p-3 border rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${themeConfig.inputClasses}`}
              rows={1}
              style={{minHeight: '48px', maxHeight: '120px'}}
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
                                        : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 hover:text-gray-900 active:bg-gray-100'
                                }`}
                            >
                                <Upload className="w-4 h-4"/>
                                <span className="font-medium">Upload</span>
                            </button>

                            <button
                                onClick={onTextSend}
                                disabled={!inputText.trim()}
                                className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-2xl transition-all duration-200 font-medium ${
                                    (inputText.trim())
                                        ? 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white'
                                        : themeConfig.cardClasses === 'bg-gray-800 border-gray-700'
                                            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                }`}
                            >
                                <Send className="w-4 h-4"/>
                                <span>Send</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InputArea;