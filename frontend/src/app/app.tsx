import {useEffect, useRef, useState} from 'react';
import axios from 'axios';

import {useTheme} from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import Login from "../components/auth/login.tsx";
import Register from "../components/auth/register.tsx";
import type {Message} from "../types/type.tsx";

const API_BASE_URL = 'http://localhost:8000/api/v1';

const SendMeResponsive = () => {
    const themeConfig = useTheme();
    const [inputText, setInputText] = useState<string>('');
    const [messages, setMessages] = useState<Message[]>([]);

    const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
    const [isRegisterView, setIsRegisterView] = useState<boolean>(false);
    const [authError, setAuthError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [authLoading, setAuthLoading] = useState<boolean>(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    };

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

    const getTokenHeader = () => {
        const token = localStorage.getItem('authToken');
        return token ? {'Authorization': `Bearer ${token}`} : {};
    };

    const mapServerStatus = (status: string): Message['status'] => {
        if (status === 'SENT') return 'success';
        if (status === 'PROCESSING') return 'uploading';
        return 'error';
    };

    const fetchProtectedImageUrl = async (messageId: string): Promise<string | undefined> => {
        try {
            const response = await axios.get(`${API_BASE_URL}/messages/${messageId}/view`, {
                headers: getTokenHeader(),
                responseType: 'blob',
            });
            return URL.createObjectURL(response.data);
        } catch (error) {
            console.error(`Error fetching protected image ${messageId}:`, error);
            return undefined;
        }
    };

    const fetchMessages = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setIsLoggedIn(false);
                setIsLoading(false);
                return;
            }

            const response = await axios.get(`${API_BASE_URL}/messages/history`, {
                headers: getTokenHeader(),
            });

            const data: Message[] = await Promise.all(response.data.map(async (msg: any) => {
                const mapped: Message = {
                    ...msg,
                    status: mapServerStatus(msg.status),
                    created_at: formatTimestamp(new Date(msg.created_at)),
                };

                if (mapped.type === 'image' && mapped.status === 'success' && mapped.id) {
                    mapped.imageUrl = await fetchProtectedImageUrl(mapped.id);
                }

                return mapped;
            }));

            setMessages(data);
        } catch (error) {
            console.error("Error fetching messages:", error);
            handleLogout();
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (token) {
            setIsLoggedIn(true);
            fetchMessages();
        } else {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
    }, [messages]);

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        setIsLoggedIn(false);
        setMessages([]);
        setAuthError(null);
    };

    const handleLoginAttempt = async (username: string, password: string) => {
        setAuthError(null);
        setAuthLoading(true);

        try {
            const tokenResponse = await axios.post(`${API_BASE_URL}/auth/login`, new URLSearchParams({
                username,
                password,
            }).toString(), {
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            });

            const {access_token} = tokenResponse.data;
            localStorage.setItem('authToken', access_token);
            setIsLoggedIn(true);
            setIsRegisterView(false);
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

    const handleRequestOtp = async (email: string, username: string, password: string) => {
        await axios.post(`${API_BASE_URL}/auth/request-otp`, {
            email,
            username,
            password,
        });
    };

    const handleRegisterAttempt = async (email: string, otpCode: string, username: string, password: string) => {
        setAuthError(null);
        setAuthLoading(true);

        try {
            await axios.post(`${API_BASE_URL}/auth/register-with-otp`, {
                email,
                otp_code: otpCode,
            });

            await handleLoginAttempt(username, password);
        } catch (err) {
            const message = axios.isAxiosError(err) && err.response?.data?.detail
                ? err.response.data.detail
                : 'Register failed. Please check email/otp.';
            setAuthError(message);
        } finally {
            setAuthLoading(false);
        }
    };

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

        setMessages(prev => [...prev, textMessage]);
        const messageContent = inputText.trim();
        setInputText('');

        try {
            const response = await axios.post(`${API_BASE_URL}/messages/text`, {
                content: messageContent,
                device: 'desktop'
            }, {
                headers: getTokenHeader(),
            });

            const savedMessage: Message = {
                ...response.data,
                status: 'success',
                created_at: formatTimestamp(new Date(response.data.created_at)),
            };

            setMessages(prev => prev.map(msg =>
                msg.id === tempId ? savedMessage : msg
            ));
        } catch (error) {
            console.error("Error sending message:", error);

            let errorMessage = 'Failed to send';
            if (axios.isAxiosError(error) && error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            }

            setMessages(prev => prev.map(msg =>
                msg.id === tempId
                    ? {...msg, status: 'error', error: errorMessage}
                    : msg
            ));
        }
    };

    const handleFileUpload = async (files: File[]) => {
        const newMessages: Message[] = files.map(file => ({
            id: `file_${crypto.randomUUID()}`,
            type: file.type.startsWith('image/') ? 'image' : 'file',
            status: 'uploading',
            file,
            fileName: file.name,
            fileSize: formatFileSize(file.size),
            fileType: file.type,
            imageUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
            progress: 0,
            created_at: formatTimestamp(new Date()),
            device: 'desktop',
        }));

        setMessages(prev => [...prev, ...newMessages]);

        for (const message of newMessages) {
            if (message.file) {
                await uploadFile(message, message.file);
            }
        }
    };

    const uploadFile = async (message: Message, file: File) => {
        const tempImageUrl = message.imageUrl;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('device', message.device);

        try {
            const response = await axios.post(`${API_BASE_URL}/messages/upload`, formData, {
                onUploadProgress: (progressEvent) => {
                    const total = progressEvent.total ?? file.size;
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / total);
                    setMessages(prev => prev.map(msg =>
                        msg.id === message.id ? {...msg, progress: percentCompleted} : msg
                    ));
                },
                headers: {
                    'Content-Type': 'multipart/form-data',
                    ...getTokenHeader(),
                },
            });

            await fetchMessages();

            const savedMessage: Message = {
                ...response.data,
                status: 'success',
                progress: 100,
                created_at: formatTimestamp(new Date(response.data.created_at)),
            };

            setMessages(prev => prev.map(msg =>
                msg.id === message.id ? savedMessage : msg
            ));

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

            if (tempImageUrl && tempImageUrl.startsWith('blob:')) {
                URL.revokeObjectURL(tempImageUrl);
            }

            setMessages(prev => prev.map(msg =>
                msg.id === message.id
                    ? {...msg, status: 'error', progress: 0, error: errorMessage, imageUrl: undefined}
                    : msg
            ));
        }
    };

    const handleCopy = async (_id: string, content: string) => {
        try {
            await navigator.clipboard.writeText(content);
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    };

    if (!isLoggedIn) {
        if (isRegisterView) {
            return (
                <Register
                    themeConfig={themeConfig}
                    onRequestOtp={handleRequestOtp}
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
