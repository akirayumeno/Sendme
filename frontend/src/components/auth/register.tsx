import React, {useState} from 'react';
import {UserPlus} from 'lucide-react';
import type {ThemeConfig} from '../../types/type.tsx';

interface RegisterProps {
    themeConfig: ThemeConfig;
    onRequestOtp: (email: string, username: string, password: string) => Promise<void>;
    onRegisterAttempt: (email: string, otpCode: string, username: string, password: string) => void;
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
    const [otpSent, setOtpSent] = useState<boolean>(false);

    const isDark = themeConfig.themeClasses.includes('bg-gray-900');
    const {cardClasses, inputClasses} = themeConfig;

    const handleRequestOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (password !== confirmPassword) {
            setLocalError('Passwords do not match!');
            return;
        }

        try {
            await onRequestOtp(email, username, password);
            setOtpSent(true);
        } catch (_err) {
            // error is handled at parent level
        }
    };

    const handleVerifyAndRegister = (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (!otpCode.trim()) {
            setLocalError('Please input OTP code.');
            return;
        }

        onRegisterAttempt(email, otpCode, username, password);
    };

    React.useEffect(() => {
        if (password === confirmPassword) {
            setLocalError(null);
        }
    }, [password, confirmPassword]);

    return (
        <div className={`min-h-screen flex items-center justify-center transition-colors duration-200 ${themeConfig.themeClasses}`}>
            <div className={`w-full max-w-md mx-auto ${cardClasses} p-8 md:p-10 rounded-xl shadow-2xl border`}>
                <div className="flex items-center justify-center mb-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                        <UserPlus className="w-6 h-6 text-white"/>
                    </div>
                </div>
                <h2 className="text-3xl font-bold text-center mb-2">Create Account</h2>
                <p className={`text-center mb-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Register with email OTP verification
                </p>

                <form onSubmit={otpSent ? handleVerifyAndRegister : handleRequestOtp} className="space-y-6">
                    <div>
                        <label htmlFor="email" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                            placeholder="Enter email"
                            disabled={isLoading || otpSent}
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
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                            placeholder="Enter username"
                            disabled={isLoading || otpSent}
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
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                            placeholder="Enter password"
                            disabled={isLoading || otpSent}
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
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                            placeholder="Re-enter password"
                            disabled={isLoading || otpSent}
                        />
                    </div>

                    {otpSent && (
                        <div>
                            <label htmlFor="otpCode" className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                OTP Code
                            </label>
                            <input
                                id="otpCode"
                                type="text"
                                value={otpCode}
                                onChange={(e) => setOtpCode(e.target.value)}
                                required
                                className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                                placeholder="Enter 6-digit code"
                                disabled={isLoading}
                            />
                        </div>
                    )}

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
                            password !== confirmPassword ||
                            (otpSent && !otpCode.trim())
                        }
                        className={`w-full py-3 px-4 rounded-xl font-semibold transition-colors duration-200 shadow-md ${
                            isLoading
                                ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                                : 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white'
                        }`}
                    >
                        {isLoading ? 'Please wait...' : otpSent ? 'Verify & Register' : 'Send OTP'}
                    </button>
                </form>

                <div className="mt-8 text-center text-sm">
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Already have an account?
                        <button
                            type="button"
                            onClick={onSwitchToLogin}
                            className="font-medium text-blue-500 hover:text-blue-400 ml-1 transition-colors"
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
