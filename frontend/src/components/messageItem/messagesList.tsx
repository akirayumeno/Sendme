// Messages List Component
import MessageItem from "./message.tsx";
import type { Message, ThemeConfig } from "../../types/type.tsx";

interface MessagesListProps {
  messages: Message[];
  onCopy: (id: string, content: string) => Promise<void> | void;
  themeConfig: ThemeConfig;
}

const MessagesList: React.FC<MessagesListProps> = ({ messages, onCopy, themeConfig }) => {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="space-y-4 max-w-3xl mx-auto">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            onCopy={onCopy}
            themeConfig={themeConfig}
          />
        ))}
      </div>
    </div>
  );
};

export default MessagesList;
