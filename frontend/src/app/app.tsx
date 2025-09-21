import { useState } from 'react';
import { useTheme } from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import type { Message } from "../types/type.tsx";

// Main App Component
const SendMeResponsive = () => {
  const themeConfig = useTheme();
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  // Send text message
  const handleTextSend = () => {
    if (inputText.trim()) {
      const textMessage: Message = {
        id: `text_${crypto.randomUUID()}`,
        type: 'text',
        status: 'success',
        content: inputText,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
        device: 'desktop',
        copied: false,
      };

      setMessages(prev => [...prev, textMessage]);
      setInputText('');
    }
  };

  // Add files and start upload simulation
  const handleFileUpload = (files: File[]) => {
    const newMessages: Message[] = files.map(file => ({
      id: `file_${crypto.randomUUID()}`,
      type: file.type.startsWith('image/') ? 'image' : 'file',
      status: 'uploading',
      file: file,
      fileName: file.name,
      fileSize: formatFileSize(file.size),
      fileType: file.type,
      imageUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      progress: 0,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
      device: 'desktop',
      copied: false,
    }));

    // Add uploading messages immediately
    setMessages(prev => [...prev, ...newMessages]);

    // Simulate upload for each file
    newMessages.forEach(message => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20 + 10;

        if (progress >= 100) {
          clearInterval(interval);
          // Mark as complete
          setMessages(prev => prev.map(msg =>
            msg.id === message.id
              ? { ...msg, status: 'success', progress: 100 }
              : msg
          ));
        } else {
          // Update progress
          setMessages(prev => prev.map(msg =>
            msg.id === message.id
              ? { ...msg, progress: Math.round(progress) }
              : msg
          ));
        }
      }, 150);
    });
  };

  // Copy message content to clipboard
  const handleCopy = async (messageId: string, content: string) => {
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
      <div className="w-full h-screen flex flex-col">
        <Header
          messageCount={messages.filter(m => m.status === 'success').length}
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
          onTextSend={handleTextSend}
          onFileUpload={handleFileUpload}
          themeConfig={themeConfig}
        />
      </div>
    </div>
  );
};

export default SendMeResponsive;