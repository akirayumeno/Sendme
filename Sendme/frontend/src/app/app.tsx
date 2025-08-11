import React, { useState } from 'react';
import {useTheme} from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import type {Message} from "../types/type.tsx";

// Main App Component
const SendMeResponsive = () => {
  const themeConfig = useTheme();
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'text',
      content: 'Hello! This is a test message.',
      timestamp: '10:30 AM',
      device: 'phone',
      copied: false
    },
    {
      id: 2,
      type: 'image',
      content: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDIwMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTIwIiBmaWxsPSIjNEY0NkU1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iNjAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iI0Y5RkFGQiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIFByZXZpZXc8L3RleHQ+Cjwvc3ZnPgo=',
      timestamp: '10:32 AM',
      device: 'desktop',
      copied: false
    },
    {
      id: 3,
      type: 'text',
      content: 'https://example.com/shared-file.pdf',
      timestamp: '10:35 AM',
      device: 'phone',
      copied: false
    },
    {
      id: 4,
      type: 'text',
      content: 'This is a longer message to demonstrate how text wraps in different screen sizes. It should look good on both mobile and desktop.',
      timestamp: '10:37 AM',
      device: 'desktop',
      copied: false
    }
  ]);

  const handleSend = () => {
    if (inputText.trim()) {
      const newMessage: Message = {
        id: Date.now(),
        type: inputText.includes('[Image:') ? 'image' : 'text',
        content: inputText,
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        }),
        device: 'desktop',
        copied: false
      };
      setMessages(prev => [...prev, newMessage]);
      setInputText('');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          setInputText(prev => prev + `[Image: ${file.name}]`);
        };
        reader.readAsDataURL(file);
      } else {
        setInputText(prev => prev + `[File: ${file.name}]`);
      }
    }
  };

  const handleCopy = async (messageId: number, content: string) => {
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
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-200 ${themeConfig.themeClasses}`}>
      <div className="w-full max-w-4xl mx-auto h-screen flex flex-col">
        <Header
          messageCount={messages.length}
          onThemeToggle={themeConfig.toggleTheme}
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
          onSend={handleSend}
          onFileUpload={handleFileUpload}
          themeConfig={themeConfig}
        />
      </div>
    </div>
  );
};

export default SendMeResponsive;