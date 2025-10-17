// Message Item Component - Unified display for all message types
import { Check, Copy, Monitor, Smartphone, File, Download, ExternalLink, X } from "lucide-react";
import type {Message, ThemeConfig} from "../../types/type.tsx";

interface MessageItemProps {
  message: Message;
  onCopy: (id: string, content: string) => void;
  themeConfig: ThemeConfig;
}
const API_BASE_URL = 'http://localhost:8000/api/v1';

const MessageItem: React.FC<MessageItemProps> = ({ message, onCopy, themeConfig }) => {
    // Unified formatting function: Convert ISO string to user-readable local time
    const formateTime = (isoString: string): string => {
        try {
            const date = new Date(isoString)
            return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
        } catch (e) {
            return "Invalid Time"
        }
    }

  const displayTime = formateTime(message.created_at)

  // File download handler
  const handleDownload = () => {
    // Use the path provided by the backend
    const backendFilePath = message.filePath
    if (backendFilePath) {
        //url
        const downloadUrl = `${API_BASE_URL}/files/${backendFilePath}`
        console.log("Downloading from server:", downloadUrl);

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
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className={`text-sm ${themeConfig.cardClasses === 'bg-gray-800 border-gray-700' ? 'text-gray-300' : 'text-gray-600'}`}>
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
                  className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>View Original</span>
                </button>
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-1 px-3 py-2 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center p-8 bg-red-100 dark:bg-red-900 rounded-lg">
              <div className="text-center">
                <X className="w-8 h-8 text-red-500 mx-auto mb-2" />
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
            <File className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${
                    themeConfig.cardClasses === 'bg-gray-800 border-gray-700' ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    {message.fileName}
                  </p>
                  <p className={`text-xs ${
                    themeConfig.cardClasses === 'bg-gray-800 border-gray-700' ? 'text-gray-400' : 'text-gray-500'
                  }`}>
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
                    className="flex items-center space-x-1 px-3 py-2 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors ml-3"
                  >
                    <Download className="w-4 h-4" />
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
        {/* Message header */}
        <div className="flex items-center justify-between mb-3 text-sm opacity-70">
          <div className="flex items-center space-x-2">
            {message.device === 'phone' ? (
              <Smartphone className="w-4 h-4" />
            ) : (
              <Monitor className="w-4 h-4" />
            )}
            <span className="capitalize">{message.device}</span>
          </div>
          <span className="created_at">{displayTime}</span>
        </div>

        {/* Message content */}
        <div className="relative">
          <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
            {renderContent()}
          </div>

          {/* Copy button - only for text messages that are successful */}
          {message.type === 'text' && message.status === 'success' && (
            <button
              onClick={() => onCopy(message.id, getContentToCopy())}
              className="absolute top-0 right-0 p-2 rounded-lg transition-all duration-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 opacity-0 group-hover:opacity-100 shadow-md"
              aria-label="Copy message content"
            >
              {message.copied ? (
                <Check className="w-4 h-4 text-green-500 focus:outline-none" />
              ) : (
                <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageItem;