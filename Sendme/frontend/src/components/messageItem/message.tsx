// Message Item Component
import {Check, Copy, FileImage, FileText, Monitor, Smartphone} from "lucide-react";
import type {Message, ThemeConfig} from "../../types/type.tsx";

const MessageItem = ({ message, onCopy, themeConfig }: {
  message: Message;
  onCopy: (id: number, content: string) => void;
  themeConfig: ThemeConfig;
}) => {
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
          {message.type === 'image' ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-sm opacity-70">
                <FileImage className="w-4 h-4" />
                <span>Image</span>
              </div>
              <img
                src={message.content}
                alt="Shared content"
                className="max-w-md h-auto rounded-lg shadow-md"
                loading="lazy"
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-sm opacity-70">
                <FileText className="w-4 h-4" />
                <span>Text</span>
              </div>
              <p className="text-base leading-relaxed break-words">{message.content}</p>
            </div>
          )}

          {/* Copy button */}
          <button
            onClick={() => onCopy(message.id, message.content)}
            className={`absolute top-0 right-0 p-2 rounded-lg transition-all duration-200 ${
              themeConfig.isDark ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'
            } opacity-0 group-hover:opacity-100 shadow-md`}
          >
            {message.copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MessageItem;
