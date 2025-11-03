import React, {useState} from 'react';
import {UserPlus} from 'lucide-react';
import type {ThemeConfig} from '../../types/type.tsx'; // Ensure path is correct

interface RegisterProps {
    themeConfig: ThemeConfig;
    onRegisterAttempt: (username: string, password: string) => void;
    onSwitchToLogin: () => void;
    error: string | null;
    isLoading: boolean;
}

const Register: React.FC<RegisterProps> = ({themeConfig, onRegisterAttempt, onSwitchToLogin, error, isLoading}) => {
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [confirmPassword, setConfirmPassword] = useState<string>('');
    const [localError, setLocalError] = useState<string | null>(null);

    const isDark = themeConfig.themeClasses.includes('bg-gray-900');

    const handleRegister = (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (password !== confirmPassword) {
            setLocalError('Passwords do not match!');
            return;
        }

        onRegisterAttempt(username, password);
    };

    const {cardClasses, inputClasses} = themeConfig;

    // Clear local error state
    React.useEffect(() => {
        if (password === confirmPassword) {
            setLocalError(null);
        }
    }, [password, confirmPassword]);

    return (
        <div
            className={`min-h-screen flex items-center justify-center transition-colors duration-200 ${themeConfig.themeClasses}`}>
            <div className={`w-full max-w-md mx-auto ${cardClasses} p-8 md:p-10 rounded-xl shadow-2xl border`}>
                <div className="flex items-center justify-center mb-6">
                    <div
                        className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                        <UserPlus className="w-6 h-6 text-white"/>
                    </div>
                </div>
                <h2 className="text-3xl font-bold text-center mb-2">
                    Create Account
                </h2>
                <p className={`text-center mb-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Start your file sharing journey now
                </p>

                <form onSubmit={handleRegister} className="space-y-6">
                    {/* Username Input */}
                    <div>
                        <label
                            htmlFor="username"
                            className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                        >
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
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className={`w-full p-3 border rounded-xl focus:ring-blue-500 focus:border-blue-500 transition-all duration-150 ${inputClasses}`}
                            placeholder="Enter password"
                            disabled={isLoading}
                        />
                    </div>

                    {/* Confirm Password Input */}
                    <div>
                        <label
                            htmlFor="confirmPassword"
                            className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                        >
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
                            disabled={isLoading}
                        />
                    </div>

                    {/* Error Messages */}
                    {(error || localError) && (
                        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm"
                             role="alert">
                            {error || localError}
                        </div>
                    )}

                    {/* Register Button */}
                    <button
                        type="submit"
                        disabled={isLoading || !username.trim() || !password.trim() || !confirmPassword.trim() || password !== confirmPassword}
                        className={`w-full py-3 px-4 rounded-xl font-semibold transition-colors duration-200 shadow-md
                            ${
                            isLoading || !username.trim() || !password.trim() || !confirmPassword.trim()
                                ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                                : 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white'
                        }`}
                    >
                        {isLoading ? (
                            <div className="flex items-center justify-center">
                                <div
                                    className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                Signing Up...
                            </div>
                        ) : (
                            'Sign Up'
                        )}
                    </button>
                </form>

                {/* Switch to Log in */}
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