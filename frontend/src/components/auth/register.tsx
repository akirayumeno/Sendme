import React, {useEffect, useState} from 'react';
import {ArrowLeft, UserPlus} from 'lucide-react';
import type {ThemeConfig} from '../../types/type.tsx';

interface RegisterProps {
    themeConfig: ThemeConfig;
    onRequestOtp: (email: string, username: string, password: string) => Promise<void>;
    onRegisterAttempt: (email: string, otpCode: string) => Promise<void>;
    onSwitchToLogin: () => void;
    error: string | null;
    isLoading: boolean;
}

const Register: React.FC<RegisterProps> = ({
                                               themeConfig,
                                               onRequestOtp,
                                               onRegisterAttempt,
                                               onSwitchToLogin,
                                               error,
                                               isLoading,
                                           }) => {
    const [email, setEmail] = useState<string>('');
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [confirmPassword, setConfirmPassword] = useState<string>('');
    const [otpCode, setOtpCode] = useState<string>('');
    const [localError, setLocalError] = useState<string | null>(null);
    const [step, setStep] = useState<'credentials' | 'verify'>('credentials');
    const [resendCooldown, setResendCooldown] = useState<number>(0);

    const isDark = themeConfig.themeClasses.includes('bg-gray-900');
    const {cardClasses, inputClasses} = themeConfig;

    const handleNext = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (password !== confirmPassword) {
            setLocalError('Passwords do not match!');
            return;
        }

        try {
            await onRequestOtp(email, username, password);
            setStep('verify');
            setResendCooldown(60);
        } catch {
            setLocalError('Failed to send verification code.');
        }
    };

    const handleResend = async () => {
        setLocalError(null);
        try {
            await onRequestOtp(email, username, password);
            setResendCooldown(60);
        } catch {
            setLocalError('Failed to resend verification code.');
        }
    };

    useEffect(() => {
        if (resendCooldown <= 0) return;
        const timer = window.setTimeout(() => {
            setResendCooldown((prev) => Math.max(0, prev - 1));
        }, 1000);
        return () => window.clearTimeout(timer);
    }, [resendCooldown]);

    const handleCreateAccount = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (!otpCode.trim()) {
            setLocalError('Please input verification code.');
            return;
        }

        try {
            await onRegisterAttempt(email, otpCode);
            onSwitchToLogin();
        } catch {
            // parent error already displayed
        }
    };

    return (
        <div className={`min-h-screen flex items-center justify-center transition-colors duration-200 px-4 py-4 ${themeConfig.themeClasses}`}>
            <div className={`w-full max-w-md mx-auto ${cardClasses} p-5 md:p-6 rounded-xl shadow-2xl border max-h-[92vh] overflow-hidden`}>
                <div className="flex items-center justify-center mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                        <UserPlus className="w-6 h-6 text-white"/>
                    </div>
                </div>
                <h2 className="text-2xl font-bold text-center mb-1">Create Account</h2>
                <p className={`text-center mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {step === 'credentials' ? 'Set your account info' : 'Enter email verification code'}
                </p>

                <div className="overflow-hidden">
                    <div
                        className="flex w-[200%] transition-transform duration-300 ease-out"
                        style={{transform: step === 'credentials' ? 'translateX(0%)' : 'translateX(-50%)'}}
                    >
                        <form onSubmit={handleNext} className="w-1/2 pr-2 space-y-4">
                            <div>
                                <label htmlFor="email" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    autoComplete="email"
                                    required
                                    className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent transition-all duration-150 ${inputClasses} autofill-fix`}
                                    placeholder="Enter email"
                                    disabled={isLoading}
                                />
                            </div>

                            <div>
                                <label htmlFor="username" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Username
                                </label>
                                <input
                                    id="username"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    autoComplete="username"
                                    required
                                    className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent transition-all duration-150 ${inputClasses} autofill-fix`}
                                    placeholder="Enter username"
                                    disabled={isLoading}
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Password
                                </label>
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    autoComplete="new-password"
                                    required
                                    className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent transition-all duration-150 ${inputClasses} autofill-fix`}
                                    placeholder="Enter password"
                                    disabled={isLoading}
                                />
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Confirm Password
                                </label>
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    autoComplete="new-password"
                                    required
                                    className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent transition-all duration-150 ${inputClasses} autofill-fix`}
                                    placeholder="Re-enter password"
                                    disabled={isLoading}
                                />
                            </div>

                            {(error || localError) && (
                                <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm" role="alert">
                                    {error || localError}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={
                                    isLoading ||
                                    !email.trim() ||
                                    !username.trim() ||
                                    !password.trim() ||
                                    !confirmPassword.trim() ||
                                    password !== confirmPassword
                                }
                                className={`w-full py-3 px-4 rounded-xl font-semibold transition-colors duration-200 shadow-md ${
                                    isLoading
                                        ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                                        : 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white'
                                }`}
                            >
                                {isLoading ? 'Please wait...' : 'Next'}
                            </button>
                        </form>

                        <form onSubmit={handleCreateAccount} className="w-1/2 pl-2 space-y-4">
                            <div>
                                <label htmlFor="otpCode" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Verification Code
                                </label>
                                <input
                                    id="otpCode"
                                    type="text"
                                    value={otpCode}
                                    onChange={(e) => setOtpCode(e.target.value)}
                                    autoComplete="one-time-code"
                                    required
                                    className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 focus:placeholder-transparent transition-all duration-150 ${inputClasses} autofill-fix`}
                                    placeholder="Enter 6-digit code"
                                    disabled={isLoading}
                                />
                            </div>

                            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                Verification code has been sent to: <span className="font-medium">{email}</span>
                            </p>

                            <div className="flex items-center justify-between text-xs">
                                <span className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                    Didn’t receive it?
                                </span>
                                <button
                                    type="button"
                                    onClick={handleResend}
                                    disabled={isLoading || resendCooldown > 0}
                                    className={`font-medium ${
                                        isLoading || resendCooldown > 0
                                            ? 'text-gray-400 cursor-not-allowed'
                                            : 'text-blue-500 hover:text-blue-400'
                                    }`}
                                >
                                    {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                                </button>
                            </div>

                            {(error || localError) && (
                                <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm" role="alert">
                                    {error || localError}
                                </div>
                            )}

                            <div className="flex gap-2">
                                <button
                                    type="button"
                                    onClick={() => setStep('credentials')}
                                    disabled={isLoading}
                                    className="flex items-center justify-center gap-1 px-4 py-3 rounded-xl border border-gray-400 text-sm"
                                >
                                    <ArrowLeft className="w-4 h-4"/>
                                    Back
                                </button>
                                <button
                                    type="submit"
                                    disabled={isLoading || !otpCode.trim()}
                                    className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-colors duration-200 shadow-md ${
                                        isLoading
                                            ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                                            : 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white'
                                    }`}
                                >
                                    {isLoading ? 'Please wait...' : 'Create Account'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <div className="mt-5 text-center text-sm">
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Already have an account?
                        <button
                            type="button"
                            onClick={onSwitchToLogin}
                            className="font-medium text-blue-500 hover:text-blue-400 ml-3 transition-colors bg-transparent border-0 p-0 shadow-none"
                            disabled={isLoading}
                        >
                            Go to Login
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
