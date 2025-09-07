// Send Button Component
import {Send} from "lucide-react";
import type {ThemeConfig} from "../../types/type.tsx";

const SendButton = ({ onClick, disabled, themeConfig }: {
  onClick: () => void;
  disabled: boolean;
  themeConfig: ThemeConfig;
}) => {
  // Check if current theme is dark by examining theme classes
  const isDark = themeConfig.themeClasses.includes('bg-gray-900') || themeConfig.themeClasses.includes('dark');

  const getButtonClasses = () => {
    if (disabled) {
      return isDark
        ? 'bg-gray-800 text-white border-gray-600 hover:bg-gray-800 cursor-text'
        : 'bg-gray-50 text-black border-gray-300 hover:bg-gray-50 cursor-text';
    } else {
      return isDark
        ? 'bg-gradient-to-r from-blue-600 to-purple-700 hover:from-blue-700 hover:to-purple-800 text-white cursor-pointer'
        : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white cursor-pointer';
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`outline-none hover:outline-none 
        focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
        transition-none hover:cursor-text flex items-center space-x-2 py-3 px-8 rounded-xl transition-all duration-200 font-medium ${
        getButtonClasses()
      }`}
    >
      <Send className="w-5 h-5" />
      <span>Send</span>
    </button>
  );
};

export default SendButton;