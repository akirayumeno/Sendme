import {useEffect, useRef, useState} from 'react';
import {useTheme} from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import type {Message} from "../types/type.tsx";
import axios from 'axios';
import Login from "../components/auth/login.tsx";
import Register from "../components/auth/register.tsx";

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Main App Component
const SendMeResponsive = () => {
    const themeConfig = useTheme();
    const [inputText, setInputText] = useState<string>('');
    const [messages, setMessages] = useState<Message[]>([]);

    // Auth
    const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
    const [isRegisterView, setIsRegisterView] = useState<boolean>(false);
    const [authError, setAuthError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [authLoading, setAuthLoading] = useState<boolean>(false);

    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Initial login in and get messages
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (token) {
            setIsLoggedIn(true);
            // 假设已登录，继续加载消息
            fetchMessages();
        } else {
            setIsLoading(false); // 如果未登录，停止加载动画，显示登录页
        }
    }, []);

    // Automatic scrolling logic: runs when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
    }, [messages]);

    // Initialize: Fetch all messages from backend
    useEffect(() => {
        const fetchMessages = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}`);
                const data: Message[] = response.data.map((msg: any) => {
                    return {
                        ...msg,
                        created_at: formatTimestamp(new Date(msg.created_at)),
                    }
                });
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

    // Format timestamp consistently (utility function)
    const formatTimestamp = (date: Date | string): string => {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const options: Intl.DateTimeFormatOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
            timeZone: 'Asia/Tokyo'
        };
        return dateObj.toLocaleTimeString('ja-JP', options);
    };

    // JWT Auth
    const fetchMessages = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                // 如果没有 Token，则不能获取消息
                setIsLoggedIn(false);
                setIsLoading(false);
                return;
            }
            const response = await axios.get(`${API_BASE_URL}/messages`, { // 假设消息获取路由为 /messages
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data: Message[] = response.data.map((msg: any) => {
                return {
                    ...msg,
                    created_at: formatTimestamp(new Date(msg.created_at)),
                }
            });
            setMessages(data);
        } catch (error) {
            console.error("Error fetching messages:", error);
            // 认证失败或 Token 过期，强制登出
            handleLogout();
        } finally {
            setIsLoading(false);
        }
    };

    // Log out
    const handleLogout = () => {
        localStorage.removeItem('authToken');
        setIsLoggedIn(false);
        setMessages([]);
        setAuthError(null);
    };

    // Login in
    const handleLoginAttempt = async (username: string, password: string) => {
        setAuthError(null);
        setAuthLoading(true);

        try {
            const tokenResponse = await axios.post(`${API_BASE_URL}/auth/token`, new URLSearchParams({
                username: username,
                password: password,
            }).toString(), {
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            });

            const {access_token} = tokenResponse.data;
            localStorage.setItem('authToken', access_token);
            setIsLoggedIn(true);
            setIsRegisterView(false);

            // login in succeed and send message.s
            await fetchMessages();

        } catch (err) {
            const message = axios.isAxiosError(err) && err.response?.data?.detail
                ? err.response.data.detail
                : 'Login failed. Please check your username and password.';
            setAuthError(message);
        } finally {
            setAuthLoading(false);
        }
    };

    // <--- 实现注册 (使用与登录类似的逻辑)
    const handleRegisterAttempt = async (username: string, password: string) => {
        setAuthError(null);
        setAuthLoading(true);

        try {
            await axios.post(`${API_BASE_URL}/auth/register`, {
                username: username,
                password: password,
            });

            // 注册成功后自动登录
            await handleLoginAttempt(username, password);

        } catch (err) {
            const message = axios.isAxiosError(err) && err.response?.data?.detail
                ? err.response.data.detail
                : '注册失败，用户名可能已被占用。';
            setAuthError(message);
        } finally {
            setAuthLoading(false);
        }
    };

    // 初始化: 检查登录状态并尝试获取消息
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (token) {
            setIsLoggedIn(true);
            // 如果已登录，则尝试获取消息
            fetchMessages();
        } else {
            setIsLoading(false); // 未登录时停止全局加载
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // 仅在组件挂载时运行一次

    const getTokenHeader = () => {
        const token = localStorage.getItem('authToken');
        return token ? {'Authorization': `Bearer ${token}`} : {};
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
            created_at: formatTimestamp(new Date()),
            device: 'desktop',
        };

        // Optimistic update: Show message immediately
        setMessages(prev => [...prev, textMessage]);
        const messageContent = inputText.trim();
        setInputText('');

        try {
            const response = await axios.post(`${API_BASE_URL}/text`, {
                content: messageContent,
                type: 'text',
                device: 'desktop'
            });

            const savedMessage: Message = response.data;
            console.log(savedMessage.created_at)
            // Replace temp message with server response
            setMessages(prev => prev.map(msg =>
                msg.id === tempId ? {
                    ...savedMessage,
                    status: 'success',
                    created_at: formatTimestamp(new Date(savedMessage.created_at))
                } : msg
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
                    ? {...msg, status: 'error', error: errorMessage}
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
            created_at: formatTimestamp(new Date()),
            device: 'desktop',
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
        const tempImageUrl = message.imageUrl;
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
                            ? {...msg, progress: percentCompleted}
                            : msg
                    ));
                },
                headers: {
                    'Content-Type': 'multipart/form-data',
                    ...getTokenHeader()
                },
            });
            fetchMessages();

            const savedMessage: Message = response.data;

            // Replace temp message with server response
            setMessages(prev => prev.map(msg =>
                msg.id === message.id
                    ? {
                        ...savedMessage,
                        status: 'success',
                        progress: 100,
                        created_at: formatTimestamp(new Date(savedMessage.created_at))
                    }
                    : msg
            ));
            // Clean up blob URL if it's an image
            if (tempImageUrl && tempImageUrl.startsWith('blob:')) {
                URL.revokeObjectURL(tempImageUrl);
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

            // Release the Blob URL even if the upload fails
            if (tempImageUrl && tempImageUrl.startsWith('blob:')) {
                URL.revokeObjectURL(tempImageUrl);
            }

            // Update to error state
            setMessages(prev => prev.map(msg =>
                msg.id === message.id
                    ? {
                        ...msg,
                        status: 'error',
                        progress: 0,
                        error: errorMessage,
                        imageUrl: undefined
                    }
                    : msg
            ));
        }
    };

    // Copy message content to clipboard
    const handleCopy = async (content: string) => {
        try {
            await navigator.clipboard.writeText(content)
        } catch (err) {
            console.error('Failed to copy: ', err)
        }
    }

    if (!isLoggedIn) {
        // Render the Login or Register page when not logged in.
        if (isRegisterView) {
            return (
                <Register
                    themeConfig={themeConfig}
                    onRegisterAttempt={handleRegisterAttempt}
                    onSwitchToLogin={() => {
                        setIsRegisterView(false);
                        setAuthError(null);
                    }}
                    error={authError}
                    isLoading={authLoading}
                />
            );
        }

        return (
            <Login
                themeConfig={themeConfig}
                onLoginAttempt={handleLoginAttempt}
                onSwitchToRegister={() => {
                    setIsRegisterView(true);
                    setAuthError(null);
                }}
                error={authError}
                isLoading={authLoading}
            />
        );
    }
    return (
        <div className={`min-h-screen transition-colors duration-200 ${themeConfig.themeClasses}`}>
            <div className="w-full h-screen flex flex-col">
                <Header
                    messageCount={messages.filter(m => m.status === 'success').length}
                    themeConfig={themeConfig}
                    onLogout={handleLogout}
                />

                {isLoading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <div
                                className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
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