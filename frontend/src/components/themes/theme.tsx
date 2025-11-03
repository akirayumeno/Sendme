// theme.tsx
import {useState} from "react";
import type {ThemeConfig} from "../../types/type.tsx";

export const useTheme = () => {
    const [isDark, setIsDark] = useState<boolean>(true);

    const toggleTheme = () => setIsDark(!isDark);
    const themeConfig: ThemeConfig = {
        themeClasses: isDark ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900',
        cardClasses: isDark ? 'bg-gray-800 border-gray-700 text-gray-300' : 'bg-white border-gray-200 text-gray-600',
        inputClasses: isDark ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
        downloadClasses: isDark ? 'bg-green-900 text-green-300 hover:bg-green-800' : 'bg-green-100 text-green-700 hover:bg-green-200',
        viewClasses: isDark ? 'bg-blue-900 text-blue-300 hover:bg-blue-800' : 'bg-blue-100 text-blue-700 hover:bg-blue-200',
        toggleTheme
    };

    return themeConfig;
};

export default useTheme;