import {Check, Copy, Download, ExternalLink, File, Monitor, Smartphone, X} from "lucide-react";
import type {Message, ThemeConfig} from "../../types/type.tsx";
import React, {useCallback, useRef, useState} from "react";
import axios from "axios";

interface MessageItemProps {
    message: Message,
    onCopy: (id: string, content: string) => void,
    themeConfig: ThemeConfig
}

const API_BASE_URL = 'http://localhost:8000/api/v1/messages';

const MessageItem: React.FC<MessageItemProps> = ({message, onCopy, themeConfig}) => {
    const [isCopied, setIsCopied] = useState(false);
    const timeoutRef = useRef<number | null>(null);

    const getTokenHeader = () => {
        const token = localStorage.getItem('authToken');
        return token ? {'Authorization': `Bearer ${token}`} : {};
    };

    const downloadBlob = (blob: Blob, filename: string) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 100);
    };

    const handleDownload = async () => {
        if (message.id && message.status === 'success') {
            try {
                const response = await axios.get(`${API_BASE_URL}/${message.id}/download`, {
                    headers: getTokenHeader(),
                    responseType: 'blob',
                });
                downloadBlob(response.data, message.fileName || 'download');
                return;
            } catch (error) {
                console.error('Download failed:', error);
            }
        }

        if (message.file) {
            downloadBlob(message.file, message.fileName || 'download');
            return;
        }

        console.error("Download Error: No file path or file data available");
    };

    const handleViewOriginal = async () => {
        if (message.imageUrl && message.imageUrl.startsWith('blob:')) {
            window.open(message.imageUrl, '_blank');
            return;
        }

        if (message.id) {
            try {
                const response = await axios.get(`${API_BASE_URL}/${message.id}/view`, {
                    headers: getTokenHeader(),
                    responseType: 'blob',
                });
                const url = URL.createObjectURL(response.data);
                window.open(url, '_blank');
                setTimeout(() => URL.revokeObjectURL(url), 60_000);
            } catch (error) {
                console.error('View original failed:', error);
            }
        }
    };

    const copyText = useCallback(() => {
        const content = getContentToCopy();
        onCopy(message.id, content);

        setIsCopied(true);
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
            setIsCopied(false);
        }, 2000);
    }, [message.id, onCopy]);

    React.useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

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
                    {message.status === 'uploading' ? (
                        <div className="flex items-center justify-center p-8 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            <div className="text-center">
                                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
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
                                    onClick={handleViewOriginal}
                                />
                            </div>
                            <div className="flex justify-center space-x-2">
                                <button
                                    onClick={handleViewOriginal}
                                    className={`flex items-center space-x-1 px-3 py-2 text-sm rounded-lg transition-colors focus:outline-none ${themeConfig.viewClasses}`}
                                >
                                    <ExternalLink className="w-4 h-4"/>
                                    <span>View Original</span>
                                </button>
                                <button
                                    onClick={handleDownload}
                                    className={`flex items-center space-x-1 px-3 py-2 text-sm rounded-lg transition-colors focus:outline-none ${themeConfig.downloadClasses}`}
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
            <div className={`${themeConfig.cardClasses} border rounded-xl p-4 transition-all duration-200 hover:shadow-lg`}>
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

                <div className="relative">
                    <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
                        {renderContent()}
                    </div>

                    {message.type === 'text' && message.status === 'success' && (
                        <button
                            onClick={copyText}
                            className={`absolute top-2 right-2 p-1.5 w-8 h-8 flex items-center justify-center rounded-lg
                                       opacity-0 group-hover:opacity-100 focus:outline-none ${
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
