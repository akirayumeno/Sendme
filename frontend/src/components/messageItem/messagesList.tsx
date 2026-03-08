import MessageItem from "./message.tsx";
import type {Message, ThemeConfig} from "../../types/type.tsx";
import {RefObject} from "react";

interface MessagesListProps {
    messages: Message[];
    onCopy: (id: string, content: string) => void;
    onDelete: (id: string) => void;
    themeConfig: ThemeConfig;
    messagesEndRef: RefObject<HTMLDivElement | null>;
    onMediaLoad?: () => void;
}

const MessagesList: React.FC<MessagesListProps> = ({messages, onCopy, onDelete, themeConfig, messagesEndRef, onMediaLoad}) => {
    const isDark = themeConfig.themeClasses.includes('bg-gray-900');

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-4 max-w-3xl mx-auto">
                {messages.length === 0 ? (
                    <div className="text-center py-12">
                        <p className={`text-lg ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
                                onDelete={onDelete}
                                themeConfig={themeConfig}
                                onMediaLoad={onMediaLoad}
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
