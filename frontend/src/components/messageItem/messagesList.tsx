import MessageItem from "./message.tsx";
import type {Message, ThemeConfig} from "../../types/type.tsx";
import {RefObject} from "react";

interface MessagesListProps {
    messages: Message[];
    onCopy: (id: string, content: string) => void;
    themeConfig: ThemeConfig;
    messagesEndRef: RefObject<HTMLDivElement | null>;
}

const MessagesList: React.FC<MessagesListProps> = ({messages, onCopy, themeConfig, messagesEndRef}) => {
    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-4 max-w-3xl mx-auto">
                {messages.length === 0 ? (
                    <div className="text-center py-12">
                        <p className={`text-lg ${
                            themeConfig.cardClasses === 'bg-gray-800 border-gray-700'
                                ? 'text-gray-400'
                                : 'text-gray-500'
                        }`}>
                            No messages yet. Start by typing or uploading files!
                        </p>
                    </div>
                ) : (
                    <>
                        {messages.map((message) => (
                            <MessageItem
                                key={message.id}
                                message={message}
                                onCopy={onCopy}
                                themeConfig={themeConfig}
                            />
                        ))}
                        {/* Scroll anchor at the end */}
                        <div ref={messagesEndRef}/>
                    </>
                )}
            </div>
        </div>
    );
};

export default MessagesList;