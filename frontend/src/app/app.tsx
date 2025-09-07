import { useState } from 'react';
import { useTheme } from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import type { Message, FileItem } from "../types/type.tsx";

// Main App Component
const SendMeResponsive = () => {
  const themeConfig = useTheme();
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);

  // Create a text message
  const createTextMessage = (text: string): Message => ({
    id: Date.now().toString(),
    type: 'text',
    content: text,
    timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
    device: 'desktop',
    copied: false,
  });

  // Create a file message
  const createFileMessage = (fileItem: FileItem): Message => ({
    id: fileItem.id,
    type: fileItem.type.startsWith('image/') ? 'image' : 'file',
    content: fileItem.name,
    timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
    device: 'desktop',
    copied: false,
    fileSize: fileItem.size,
  });

  // Send messages (text + successfully uploaded files)
  const handleSend = () => {
    const newMessages: Message[] = [];

    if (inputText.trim()) {
      newMessages.push(createTextMessage(inputText));
    }

    files
      .filter(f => f.status === 'success')
      .forEach(f => {
        newMessages.push(createFileMessage(f));
      });

    if (newMessages.length > 0) {
      setMessages(prev => [...prev, ...newMessages]);
      setInputText('');
      setFiles([]);
    }
  };

  // Copy message content to clipboard
  const handleCopy = async (messageId: number | string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, copied: true } : msg
      ));
      setTimeout(() => {
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, copied: false } : msg
        ));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-200 ${themeConfig.themeClasses}`}>
      <div className="w-full max-w-4xl mx-auto h-screen flex flex-col">
        <Header
          messageCount={messages.length}
          themeConfig={themeConfig}
        />

        <MessagesList
          messages={messages}
          onCopy={handleCopy}
          themeConfig={themeConfig}
        />

        <InputArea
          inputText={inputText}
          setInputText={setInputText}
          files={files}
          setFiles={setFiles}
          onSend={handleSend}
          themeConfig={themeConfig}
        />
      </div>
    </div>
  );
};

export default SendMeResponsive;
