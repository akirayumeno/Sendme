// Message Item Component - Unified display for all message types
import { Check, Copy, FileImage, FileText, Monitor, Smartphone, File, Download, ExternalLink } from "lucide-react";
import type { Message, ThemeConfig } from "../../types/type.tsx";

interface MessageItemProps {
  message: Message;
  onCopy: (id: string, content: string) => void;
  themeConfig: ThemeConfig;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onCopy, themeConfig }) => {
  const renderMessageContent = () => {
    // All message types are displayed in a unified format
    return (
      <div className="space-y-3">
        {/* Message content area */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border">
          {/* Text content (if any) */}
          {message.type === 'text' && (
            <div className="flex items-start space-x-3">
              <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-base leading-relaxed break-words whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
            </div>
          )}

          {/* File content */}
          {(message.type === 'file' || message.type === 'image') && (
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                {message.type === 'image' ? (
                  <FileImage className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                ) : (
                  <File className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {message.fileName || 'Unknown file'}
                      </p>
                      {message.fileSize && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {message.fileSize}
                        </p>
                      )}
                    </div>

                    {/* File actions */}
                    {message.fileUrl && (
                      <div className="flex items-center space-x-2 ml-3">
                        <button
                          onClick={() => window.open(message.fileUrl, '_blank')}
                          className="flex items-center space-x-1 px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                          title="Open in new tab"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>View</span>
                        </button>
                        <a
                          href={message.fileUrl}
                          download={message.fileName}
                          className="flex items-center space-x-1 px-2 py-1 text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                          title="Download file"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download</span>
                        </a>
                      </div>
                    )}
                  </div>

                  {/* Image preview for image files */}
                  {message.type === 'image' && message.fileUrl && (
                    <div className="mt-3">
                      <img
                        src={message.fileUrl}
                        alt={message.fileName || "Image"}
                        className="max-w-sm h-auto rounded-lg shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
                        loading="lazy"
                        onClick={() => window.open(message.fileUrl, '_blank')}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
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
          <span>{message.timestamp}</span>
        </div>

        {/* Message content */}
        <div className="relative">
          {renderMessageContent()}

          {/* Copy button */}
          <button
            onClick={() => {
              // For files and images, copy the file URL; for text, copy the content
              const contentToCopy = message.type !== 'text' && message.fileUrl
                ? message.fileUrl
                : message.content;
              onCopy(message.id, contentToCopy);
            }}
            className="absolute top-0 right-0 p-2 rounded-lg transition-all duration-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 opacity-0 group-hover:opacity-100 shadow-md"
            aria-label="Copy message content"
          >
            {message.copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MessageItem;