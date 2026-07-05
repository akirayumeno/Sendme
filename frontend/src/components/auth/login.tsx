import React, {useEffect, useRef, useState} from 'react';
import {Moon, Send, Sun} from 'lucide-react';
import type {ThemeConfig} from '../../types/type.tsx'; // Ensure path is correct

interface LoginProps {
    themeConfig: ThemeConfig;
    onLoginAttempt: (username: string, password: string) => void;
    onSwitchToRegister: () => void;
    error: string | null;
    isLoading: boolean;
}

const Login: React.FC<LoginProps> = ({themeConfig, onLoginAttempt, onSwitchToRegister, error, isLoading}) => {
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [, setAutofillTick] = useState<number>(0);
    const usernameRef = useRef<HTMLInputElement>(null);
    const passwordRef = useRef<HTMLInputElement>(null);

    const isDark = themeConfig.themeClasses.includes('bg-gray-900');

    const syncAutofillValues = () => {
        const nextUsername = usernameRef.current?.value ?? '';
        const nextPassword = passwordRef.current?.value ?? '';
        if (nextUsername !== username) setUsername(nextUsername);
        if (nextPassword !== password) setPassword(nextPassword);
        setAutofillTick(tick => tick + 1);
    };

    useEffect(() => {
        let attempts = 0;
        const interval = window.setInterval(() => {
            syncAutofillValues();
            attempts += 1;
            if (attempts >= 20) {
                window.clearInterval(interval);
            }
        }, 150);
        syncAutofillValues();
        return () => window.clearInterval(interval);
    }, []);

    const currentUsername = usernameRef.current?.value || username;
    const currentPassword = passwordRef.current?.value || password;
    const canSubmit = Boolean(currentUsername.trim() && currentPassword.trim()) && !isLoading;

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        const nextUsername = usernameRef.current?.value ?? username;
        const nextPassword = passwordRef.current?.value ?? password;
        setUsername(nextUsername);
        setPassword(nextPassword);
        if (!nextUsername.trim() || !nextPassword.trim()) return;
        onLoginAttempt(nextUsername, nextPassword);
    };

    const {cardClasses, inputClasses} = themeConfig;

    return (
        <div
            className={`min-h-screen flex items-center justify-center transition-colors duration-200 ${themeConfig.themeClasses}`}>
            <button
                type="button"
                onClick={themeConfig.toggleTheme}
                className={`absolute right-5 top-5 focus:outline-none p-2 rounded-lg transition-colors ${
                    isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-100' : 'bg-white hover:bg-gray-100 text-gray-700'
                }`}
                aria-label="Toggle theme"
            >
                {isDark ? <Sun className="w-5 h-5"/> : <Moon className="w-5 h-5"/>}
            </button>
            <div className={`w-full max-w-md mx-auto ${cardClasses} p-8 md:p-10 rounded-xl shadow-2xl border`}>
                <div className="flex items-center justify-center mb-6">
                    <div
                        className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                        <Send className="w-6 h-6 text-white"/>
                    </div>
                </div>
                <h2 className="text-3xl font-bold text-center mb-2">
                    Welcome Back
                </h2>
                <p className={`text-center mb-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Sign in to your SendMe account
                </p>

                <form onSubmit={handleLogin} className="space-y-6">
                    {/* Username Input */}
                    <div>
                        <label
                            htmlFor="username"
                            className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                        >
                            Username
                        </label>
                        <input
                            ref={usernameRef}
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            onInput={syncAutofillValues}
                            onFocus={syncAutofillValues}
                            autoComplete="username"
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent ${inputClasses} autofill-fix`}
                            placeholder="Enter your username"
                            disabled={isLoading}
                        />
                    </div>

                    {/* Password Input */}
                    <div>
                        <label
                            htmlFor="password"
                            className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                        >
                            Password
                        </label>
                        <input
                            ref={passwordRef}
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onInput={syncAutofillValues}
                            onFocus={syncAutofillValues}
                            autoComplete="current-password"
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent ${inputClasses} autofill-fix`}
                            placeholder="Enter your password"
                            disabled={isLoading}
                        />
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm"
                             role="alert">
                            {error}
                        </div>
                    )}

                    {/* Login Button */}
                    <button
                        type="submit"
                        disabled={!canSubmit}
                        className={`w-full py-3 px-4 rounded-xl font-semibold transition-colors duration-200 shadow-md
                            ${
                            !canSubmit
                                ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                                : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white'
                        }`}
                    >
                        {isLoading ? (
                            <div className="flex items-center justify-center">
                                <div
                                    className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                Signing In...
                            </div>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>

                {/* Switch to Register */}
                <div className="mt-8 text-center text-sm">
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Don't have an account yet?
                        <button
                            type="button"
                            onClick={onSwitchToRegister}
                            className="font-medium text-blue-500 hover:text-blue-400 ml-3 transition-colors bg-transparent border-0 p-0 shadow-none"
                            disabled={isLoading}
                        >
                            Sign Up Now
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
