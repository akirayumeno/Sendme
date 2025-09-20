// Message Item Component - Unified display for all message types
import { Check, Copy, Monitor, Smartphone, File, Download, ExternalLink } from "lucide-react";
import type {FileItem, FileMessage, ImageMessage, Message, TextMessage, ThemeConfig} from "../../types/type.tsx";

interface MessageItemProps {
  message: Message;
  onCopy: (id: string, content: string) => void;
  themeConfig: ThemeConfig;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onCopy, themeConfig }) => {
  // Image download handler
    const handleImageDownload = (message: ImageMessage) => {
      try {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(message.originalFile);
        link.download = message.fileName;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean URL temporarily
        setTimeout(() => {
          URL.revokeObjectURL(link.href);
        }, 100);

      } catch (error) {
        console.error('Image Download Error:', error);
      }
    };

    // File download handler
    const handleFileDownload = (fileItem: FileItem) => {
      if (!fileItem.file) {
        console.error("Download Error: Original file data not available");
        return;
      }

      try {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(fileItem.file);
        link.download = fileItem.name;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setTimeout(() => {
          URL.revokeObjectURL(link.href);
        }, 100);

      } catch (error) {
        console.error('File download failed:', error);
      }
    };

    const renderMessageContent = () => {
    // All message types are displayed in a unified format
    switch (message.type) {
      case 'text':
        return renderTextMessage(message);
      case 'image':
        return renderImageMessage(message);
      case 'file':
        return renderFileMessage(message);
      default:
        return null;
    }
  };

  // Render text message
  const renderTextMessage = (message: TextMessage) => (
    <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
      <div className="flex items-start space-x-3">
        <div className="flex-1">
          <p className="text-base leading-relaxed break-words whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
      </div>
    </div>
  );

  // Render image message
  const renderImageMessage = (message: ImageMessage) => (
    <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
      <div className="space-y-3">
        {/* Display image directly */}
        <div className="flex justify-center">
          <img
            src={message.imageUrl}
            alt={message.fileName}
            className="max-w-full h-auto rounded-lg shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
            loading="lazy"
            onClick={() => window.open(message.imageUrl, '_blank')}
          />
        </div>

        {/* Action buttons */}
        <div className="flex justify-center space-x-2">
          <button
            onClick={() => window.open(message.imageUrl, '_blank')}
            className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            <span>View Original</span>
          </button>
          <button
            onClick={() => handleImageDownload(message)}
            className="flex items-center space-x-1 px-3 py-2 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
            aria-label="Download"
          >
            <Download className="w-4 h-4" />
            <span>Download</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Render file message
  const renderFileMessage = (message: FileMessage) => (
    <div className={`${themeConfig.cardClasses} rounded-lg p-4 border`}>
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <File className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${themeConfig.inputClasses} truncate`}>
                  {message.fileItem.name}
                </p>
                <p className={`text-xs ${themeConfig.inputClasses}`}>
                  {message.fileItem.size}
                </p>
              </div>

              {/* File download button */}
              <div className="flex items-center space-x-2 ml-3">
                  <button
                    onClick={() => handleFileDownload(message.fileItem)}
                    className="flex items-center space-x-1 px-3 py-2 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                    aria-label="Download"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download</span>
                  </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Get the content to copy
  const getContentToCopy = (): string => {
  switch (message.type) {
    case 'text':
      return message.content || '';
    case 'image':
      return message.imageUrl || '';
    case 'file':
      return message.fileItem?.url || '';
    default:
      return '';
  }
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
          {message.type === 'text' &&(
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