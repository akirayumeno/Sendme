import {useEffect, useLayoutEffect, useRef, useState} from 'react';
import axios from 'axios';

import {useTheme} from "../components/themes/theme.tsx";
import Header from "../components/header/header.tsx";
import MessagesList from "../components/messageItem/messagesList.tsx";
import InputArea from "../components/input/inputArea.tsx";
import Login from "../components/auth/login.tsx";
import Register from "../components/auth/register.tsx";
import type {Message} from "../types/type.tsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_BASE_URL = `${API_BASE.replace(/\/$/, '')}/messages`;

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
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const uploadingIdsRef = useRef<Set<string>>(new Set());
    const wsRef = useRef<WebSocket | null>(null);
    const wsReconnectRef = useRef<number | null>(null);
    const wsFetchDebounceRef = useRef<number | null>(null);
    const pollingRef = useRef<number | null>(null);
    const shouldStickToBottomRef = useRef<boolean>(true);
    const preserveDistanceFromBottomRef = useRef<number | null>(null);
    const deletingMessageIdRef = useRef<string | null>(null);
    const scrollToBottom = (behavior: ScrollBehavior = 'auto') => {
        messagesEndRef.current?.scrollIntoView({behavior, block: 'end'});
    };

    const isNearBottom = () => {
        const el = messagesContainerRef.current;
        if (!el) return true;
        const gap = el.scrollHeight - el.scrollTop - el.clientHeight;
        return gap < 120;
    };

    // Convert raw bytes into a readable size string for UI display.
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    };

    // Normalize backend timestamps to a consistent local display format.
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

    // Build Authorization header from localStorage token.
    const getTokenHeader = () => {
        const token = localStorage.getItem('authToken');
        return token ? {'Authorization': `Bearer ${token}`} : {};
    };

    // Map backend message status enum to frontend UI status.
    const mapServerStatus = (status: string): Message['status'] => {
        if (status === 'SENT') return 'success';
        if (status === 'PROCESSING') return 'uploading';
        return 'error';
    };

    // Fetch protected image blob and convert to object URL for preview rendering.
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

    // Pull history from backend and merge with local pending messages.
    const fetchMessages = async ({silent = false}: { silent?: boolean } = {}) => {
        if (!silent) setIsLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setIsLoggedIn(false);
                if (!silent) setIsLoading(false);
                return;
            }

            const response = await axios.get(`${API_BASE_URL}/messages/history`, {
                headers: getTokenHeader(),
            });

            const sortedServerMessages = [...response.data].sort(
                (a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            );

            const data: Message[] = await Promise.all(sortedServerMessages.map(async (msg: any) => {
                const mapped: Message = {
                    ...msg,
                    id: String(msg.id),
                    status: mapServerStatus(msg.status),
                    created_at: formatTimestamp(new Date(msg.created_at)),
                };

                if (mapped.type === 'image' && mapped.status === 'success' && mapped.id) {
                    mapped.imageUrl = await fetchProtectedImageUrl(mapped.id);
                }

                return mapped;
            }));

            setMessages(prev => {
                const pendingLocal = prev.filter(msg =>
                    msg.status !== 'success' &&
                    (msg.id.startsWith('text_') || msg.id.startsWith('file_'))
                );
                return [...data, ...pendingLocal];
            });
        } catch (error) {
            console.error("Error fetching messages:", error);
            handleLogout();
        } finally {
            if (!silent) setIsLoading(false);
        }
    };

    // Stop fallback polling timer when websocket is healthy.
    const stopPolling = () => {
        if (pollingRef.current) {
            window.clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    };

    // Start 3-second polling fallback when websocket is unavailable.
    const startPolling = () => {
        if (pollingRef.current) return;
        pollingRef.current = window.setInterval(() => {
            fetchMessages({silent: true});
        }, 3000);
    };

    // Debounce repeated realtime events to avoid bursty history requests.
    const scheduleFetchMessages = () => {
        if (wsFetchDebounceRef.current) {
            window.clearTimeout(wsFetchDebounceRef.current);
        }
        wsFetchDebounceRef.current = window.setTimeout(() => {
            fetchMessages({silent: true});
        }, 120);
    };

    // Connect realtime websocket; auto fallback to polling on disconnect.
    const connectWebSocket = () => {
        const token = localStorage.getItem('authToken');
        if (!token) return;
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

        const wsBase = (import.meta as any).env?.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/, 'ws');
        const wsUrl = `${wsBase.replace(/\/api\/v1$/, '')}/api/v1/ws/messages?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            stopPolling();
        };

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                const deletingId = deletingMessageIdRef.current;
                if (
                    deletingId &&
                    payload?.event === 'message.deleted' &&
                    String(payload?.message_id) === String(deletingId)
                ) {
                    deletingMessageIdRef.current = null;
                    return;
                }
            } catch {
                // Non-JSON payload; keep fallback behavior.
            }
            scheduleFetchMessages();
        };

        ws.onclose = () => {
            if (!isLoggedIn) return;
            startPolling();
            wsReconnectRef.current = window.setTimeout(() => {
                connectWebSocket();
            }, 2000);
        };

        ws.onerror = () => {
            ws.close();
        };
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

    useLayoutEffect(() => {
        if (preserveDistanceFromBottomRef.current !== null) {
            const container = messagesContainerRef.current;
            if (container) {
                const nextTop = container.scrollHeight - preserveDistanceFromBottomRef.current;
                container.scrollTop = Math.max(0, nextTop);
            }
            preserveDistanceFromBottomRef.current = null;
            return;
        }
        if (!shouldStickToBottomRef.current) return;
        scrollToBottom('auto');
        const timer = window.setTimeout(() => scrollToBottom('auto'), 80);
        return () => window.clearTimeout(timer);
    }, [messages]);

    useEffect(() => {
        if (!isLoggedIn) {
            stopPolling();
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            return;
        }

        connectWebSocket();

        return () => {
            stopPolling();
            if (wsReconnectRef.current) {
                window.clearTimeout(wsReconnectRef.current);
            }
            if (wsFetchDebounceRef.current) {
                window.clearTimeout(wsFetchDebounceRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [isLoggedIn]);

    // Clear session state and close realtime channels.
    const handleLogout = () => {
        stopPolling();
        if (wsReconnectRef.current) {
            window.clearTimeout(wsReconnectRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        localStorage.removeItem('authToken');
        setIsLoggedIn(false);
        setMessages([]);
        setAuthError(null);
    };

    // Login flow: exchange credentials for JWT then bootstrap messages.
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

    // Trigger OTP email for registration step 1.
    const handleRequestOtp = async (email: string, username: string, password: string) => {
        setAuthError(null);
        setAuthLoading(true);
        try {
            await axios.post(`${API_BASE_URL}/auth/request-otp`, {
                email,
                username,
                password,
            });
        } catch (err) {
            const message = axios.isAxiosError(err) && err.response?.data?.detail
                ? err.response.data.detail
                : 'Failed to send mail.';
            setAuthError(message);
            throw err;
        } finally {
            setAuthLoading(false);
        }
    };

    // Complete registration by verifying OTP code.
    const handleRegisterAttempt = async (email: string, otpCode: string) => {
        setAuthError(null);
        setAuthLoading(true);

        try {
            await axios.post(`${API_BASE_URL}/auth/register-with-otp`, {
                email,
                otp_code: otpCode,
            });
            setIsRegisterView(false);
        } catch (err) {
            const message = axios.isAxiosError(err) && err.response?.data?.detail
                ? err.response.data.detail
                : 'Register failed. Please check email/otp.';
            setAuthError(message);
            throw err;
        } finally {
            setAuthLoading(false);
        }
    };

    // Optimistic text send with temporary local message replacement.
    const handleTextSend = async () => {
        if (!inputText.trim()) return;
        shouldStickToBottomRef.current = true;

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
                id: String(response.data.id),
                status: mapServerStatus(response.data.status),
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

    // Queue selected files as optimistic messages, then upload sequentially.
    const handleFileUpload = async (files: File[]) => {
        shouldStickToBottomRef.current = true;
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

        // Sync once after batch upload finishes, avoid per-file UI flicker.
        await fetchMessages();
    };

    // Upload a single file with progress tracking and result reconciliation.
    const uploadFile = async (message: Message, file: File) => {
        if (uploadingIdsRef.current.has(message.id)) {
            return;
        }
        uploadingIdsRef.current.add(message.id);

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

            const savedMessage: Message = {
                ...response.data,
                id: String(response.data.id),
                status: mapServerStatus(response.data.status),
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
        } finally {
            uploadingIdsRef.current.delete(message.id);
        }
    };

    // Copy message content to clipboard.
    const handleCopy = async (_id: string, content: string) => {
        try {
            await navigator.clipboard.writeText(content);
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    };

    // Delete message both in backend and local list.
    const handleDeleteMessage = async (id: string) => {
        const container = messagesContainerRef.current;
        const nearBottom = isNearBottom();
        shouldStickToBottomRef.current = nearBottom;
        if (container && !nearBottom) {
            preserveDistanceFromBottomRef.current = container.scrollHeight - container.scrollTop;
        }
        deletingMessageIdRef.current = id;
        if (id.startsWith('text_') || id.startsWith('file_')) {
            setMessages(prev => prev.filter(msg => msg.id !== id));
            return;
        }
        try {
            await axios.delete(`${API_BASE_URL}/messages/${id}`, {
                headers: getTokenHeader(),
            });
            setMessages(prev => prev.filter(msg => msg.id !== id));
        } catch (error) {
            console.error("Failed to delete message:", error);
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
                        onDelete={handleDeleteMessage}
                        themeConfig={themeConfig}
                        messagesEndRef={messagesEndRef}
                        messagesContainerRef={messagesContainerRef}
                        onMessagesScroll={() => {
                            shouldStickToBottomRef.current = isNearBottom();
                        }}
                        onMediaLoad={() => {
                            if (shouldStickToBottomRef.current) {
                                scrollToBottom('auto');
                            }
                        }}
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
