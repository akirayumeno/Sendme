// Message Item Component
import {Check, Copy, Download, ExternalLink, File, Monitor, Smartphone, X} from "lucide-react";
import type {Message, ThemeConfig} from "../../types/type.tsx";
import React, {useCallback, useRef, useState} from "react";

interface MessageItemProps {
    message: Message,
    onCopy: (id: string, content: string) => void,
    themeConfig: ThemeConfig
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

const MessageItem: React.FC<MessageItemProps> = ({message, onCopy, themeConfig}) => {
    const [isCopied, setIsCopied] = useState(false);
    const timeoutRef = useRef<number | null>(null);
    // File download handler
    const handleDownload = () => {
        // Use the path provided by the backend
        const backendFilePath = message.filePath
        if (backendFilePath) {
            //url
            const downloadUrl = `${API_BASE_URL}/download/${backendFilePath}`
            const link = document.createElement('a');
            link.href = downloadUrl;

            link.download = message.fileName || 'download';

            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            return;
        } else if (message.file) {
            // Local memory file download logic (only available when uploading)
            console.log("Downloading from local memory (only valid before refresh).");
            const link = document.createElement('a');
            link.href = URL.createObjectURL(message.file);
            link.download = message.fileName || 'download';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setTimeout(() => {
                URL.revokeObjectURL(link.href);
            }, 100);
            return;
        }
        console.error("Download Error: No file path or file data available");
    };

    // copy button
    const copyText = useCallback(() => {
        const content = getContentToCopy()
        // Call the copy function passed from the parent component (responsible for the actual clipboard operation).
        onCopy(message.id, content)

        // Set local state and clear old timers
        setIsCopied(true)
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current)
        }

        // Set a new timer to reset the state after 2 seconds.
        timeoutRef.current = setTimeout(() => {
            setIsCopied(false)
        }, 2000)
    }, [message.content, onCopy])

    // Clean up timers to prevent memory leaks
    React.useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    // Get the content to copy
    const getContentToCopy = (): string => {
        switch (message.type) {
            case 'text':
                return message.content || '';
            case 'image':
                return message.imageUrl || '';
            case 'file':
                return message.fileName || '';
            default:
                return '';
        }
    };

    const renderContent = () => {
        if (message.type === 'text') {
            return (
                <div className="flex items-start space-x-3">
                    <div className="flex-1">
                        <p className="text-base leading-relaxed break-words whitespace-pre-wrap">
                            {message.content}
                        </p>
                    </div>
                </div>
            );
        }

        if (message.type === 'image') {
            return (
                <div className="space-y-3">
                    {/* Show upload progress or completed image */}
                    {message.status === 'uploading' ? (
                        <div className="flex items-center justify-center p-8 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            <div className="text-center">
                                <div
                                    className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                                <p className={`text-sm ${themeConfig.cardClasses}`}>
                                    Uploading... {message.progress}%
                                </p>
                            </div>
                        </div>
                    ) : message.status === 'success' && message.imageUrl ? (
                        <>
                            <div className="flex justify-center">
                                <img
                                    src={message.imageUrl}
                                    alt={message.fileName}
                                    className="max-w-full h-auto rounded-lg shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
                                    loading="lazy"
                                    onClick={() => window.open(message.imageUrl, '_blank')}
                                />
                            </div>
                            <div className="flex justify-center space-x-2">
                                <button
                                    onClick={() => window.open(message.imageUrl, '_blank')}
                                    className={`flex items-center space-x-1 px-3 py-2 text-sm rounded-lg transition-colors ${themeConfig.viewClasses}`}
                                >
                                    <ExternalLink className="w-4 h-4"/>
                                    <span>View Original</span>
                                </button>
                                <button
                                    onClick={handleDownload}
                                    className={`flex items-center space-x-1 px-3 py-2 text-sm rounded-lg transition-colors ${themeConfig.downloadClasses}`}
                                >
                                    <Download className="w-4 h-4"/>
                                    <span>Download</span>
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center justify-center p-8 bg-red-100 dark:bg-red-900 rounded-lg">
                            <div className="text-center">
                                <X className="w-8 h-8 text-red-500 mx-auto mb-2"/>
                                <p className="text-sm text-red-600 dark:text-red-400">Upload failed</p>
                                {message.error && <p className="text-xs text-red-500 mt-1">{message.error}</p>}
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        if (message.type === 'file') {
            return (
                <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                        <File className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0"/>

                        <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <p className={`text-sm font-medium truncate ${themeConfig.cardClasses}`}>
                                        {message.fileName}
                                    </p>
                                    <p className={`text-xs ${themeConfig.cardClasses}`}>
                                        {message.fileSize}
                                        {message.status === 'uploading' && ` • Uploading... ${message.progress}%`}
                                        {message.status === 'success' && ' • Complete'}
                                        {message.status === 'error' && ' • Failed'}
                                    </p>
                                    {message.error && (
                                        <p className={`text-xs mt-1 ${
                                            themeConfig.cardClasses === 'bg-gray-800 border-gray-700' ? 'text-red-400' : 'text-red-500'
                                        }`}>
                                            {message.error}
                                        </p>
                                    )}
                                </div>

                                {message.status === 'success' && (
                                    <button
                                        onClick={handleDownload}
                                        className={`flex items-center space-x-1 px-3 py-2 text-sm rounded-lg transition-colors ml-3 ${themeConfig.downloadClasses}`}
                                    >
                                        <Download className="w-4 h-4"/>
                                        <span>Download</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <div className="group">
            <div
                className={`${themeConfig.cardClasses} border rounded-xl p-4 transition-all duration-200 hover:shadow-lg`}>
                {/* Message header */}
                <div className="flex items-center justify-between mb-3 text-sm opacity-80 w-full">
                    <div className="flex-1"></div>

                    <div className="flex-1 text-center">
                        <span>{message.created_at}</span>
                    </div>

                    <div className="flex items-center justify-end space-x-2 flex-1">
                        {message.device === 'phone' ? (
                            <Smartphone className="w-4 h-4"/>
                        ) : (
                            <Monitor className="w-4 h-4"/>
                        )}
                    </div>
                </div>

                {/* Message content */}
                <div className="relative">
                    <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
                        {renderContent()}
                    </div>

                    {/* Copy button - only for text messages that are successful */}
                    {message.type === 'text' && message.status === 'success' && (
                        <button
                            onClick={copyText}
                            className={`absolute top-2 right-2 p-1.5 w-8 h-8 flex items-center justify-center rounded-lg
                                       transition-all duration-200 opacity-0 group-hover:opacity-100 focus:outline-none ${
                                themeConfig.cardClasses === 'bg-gray-800 border-gray-700 text-gray-300'
                                    ? 'bg-gray-800 hover:bg-black text-gray-300'
                                    : 'bg-white hover:bg-gray-200 text-gray-600'
                            }`}
                            aria-label="Copy message content"
                        >
                            {isCopied ? (
                                <Check className="w-4 h-4 text-green-500 focus:outline-none"/>
                            ) : (
                                <Copy className="w-4 h-4 "/>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MessageItem;