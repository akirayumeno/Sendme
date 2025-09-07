// theme.tsx
import { useState } from "react";
import type { ThemeConfig } from "../../types/type.tsx";

export const useTheme = () => {
  const [isDark, setIsDark] = useState<boolean>(true);

  const toggleTheme = () => setIsDark(!isDark);

  const themeConfig: ThemeConfig = {
    themeClasses: isDark ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900',
    cardClasses: isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200',
    inputClasses: isDark ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
    toggleTheme
  };

  return themeConfig;
};

export default useTheme;