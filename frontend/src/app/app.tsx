import { useRef, useEffect, useState } from 'react';
import { useTheme } from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import type { Message } from "../types/type.tsx";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Main App Component
const SendMeResponsive = () => {
  const themeConfig = useTheme();
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Automatic scrolling logic: runs when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize: Fetch all messages from backend
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}`);
        const data: Message[] = response.data;
        setMessages(data);
      } catch (error) {
        console.error("Error fetching messages:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMessages();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  // Send text message
  const handleTextSend = async () => {
    if (!inputText.trim()) return;

    const tempId = `text_${crypto.randomUUID()}`;
    const textMessage: Message = {
      id: tempId,
      type: 'text',
      status: 'uploading',
      content: inputText,
      created_at: new Date().toISOString(),
      device: 'desktop',
      copied: false,
    };

    // Optimistic update: Show message immediately
    setMessages(prev => [...prev, textMessage]);
    const messageContent = inputText.trim();
    setInputText('');

    try {
      const response = await axios.post(`${API_BASE_URL}/messages/text`, {
        content: messageContent,
        type: 'text',
        device: 'desktop'
      });

      const savedMessage: Message = response.data;

      // Replace temp message with server response
      setMessages(prev => prev.map(msg =>
        msg.id === tempId ? { ...savedMessage, status: 'success' } : msg
      ));
    } catch (error) {
      console.error("Error sending message:", error);

      let errorMessage = 'Failed to send';
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      // Update message to error state
      setMessages(prev => prev.map(msg =>
        msg.id === tempId
          ? { ...msg, status: 'error', error: errorMessage }
          : msg
      ));
    }
  };

  // Upload files
  const handleFileUpload = async (files: File[]) => {
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
      created_at: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
      device: 'desktop',
      copied: false,
    }));

    // Add uploading messages immediately
    setMessages(prev => [...prev, ...newMessages]);

    // Upload each file
    for (const message of newMessages) {
      if (message.file) {
        await uploadFile(message, message.file);
      }
    }
  };

  // Upload single file with progress tracking
  const uploadFile = async (message: Message, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('device', message.device);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total ?? file.size;
          const percentCompleted = Math.round((progressEvent.loaded * 100) / total);

          // Update progress in real-time
          setMessages(prev => prev.map(msg =>
            msg.id === message.id
              ? { ...msg, progress: percentCompleted }
              : msg
          ));
        },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const savedMessage: Message = response.data;

      // Replace temp message with server response
      setMessages(prev => prev.map(msg =>
        msg.id === message.id
          ? { ...savedMessage, status: 'success', progress: 100 }
          : msg
      ));

      // Clean up blob URL if it's an image
      if (message.imageUrl && message.imageUrl.startsWith('blob:')) {
        URL.revokeObjectURL(message.imageUrl);
      }
    } catch (error) {
      console.error(`Upload error for ${file.name}:`, error);

      let errorMessage = 'Upload failed';
      if (axios.isAxiosError(error)) {
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
      }

      // Update to error state
      setMessages(prev => prev.map(msg =>
        msg.id === message.id
          ? {
              ...msg,
              status: 'error',
              progress: 0,
              error: errorMessage
            }
          : msg
      ));
    }
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

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-500">Loading messages...</p>
            </div>
          </div>
        ) : (
          <MessagesList
            messages={messages}
            onCopy={handleCopy}
            themeConfig={themeConfig}
            messagesEndRef={messagesEndRef}
          />
        )}

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