// Header Component
import {LogOut, Moon, Send, Sun} from "lucide-react";
import type {ThemeConfig} from "../../types/type";

interface HeaderProps {
    messageCount: number;
    themeConfig: ThemeConfig;
    onLogout: () => void; // 声明组件需要这个 prop
}

const Header: React.FC<HeaderProps> = ({messageCount, themeConfig, onLogout}) => {
    // Determine if current theme is dark by checking themeClasses
    const isDark = themeConfig.themeClasses.includes('dark') || themeConfig.themeClasses.includes('bg-gray-900');

    return (
        <div className={`${themeConfig.cardClasses} border-b px-6 py-4 flex items-center justify-between`}>
            <div className="flex items-center space-x-3">
                <div
                    className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <Send className="w-5 h-5 text-white"/>
                </div>
                <div>
                    <h1 className="text-xl font-bold">SendMe</h1>
                    <p className="text-sm opacity-70">Cross-device messaging</p>
                </div>
            </div>

            <div className="flex items-center space-x-4">
                <div className="text-sm opacity-70">
                    {messageCount} messages
                </div>

                {/* Log out button */}
                <button
                    onClick={onLogout}
                    className={`focus:outline-none p-2 rounded-lg transition-colors 
            ${isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`
                    }
                    aria-label="Logout"
                >
                    <LogOut className="w-5 h-5"/>
                </button>

                {/* Theme switching button */}
                <button
                    onClick={themeConfig.toggleTheme}
                    className={`focus:outline-none p-2 rounded-lg transition-colors ${
                        isDark ? 'bg-gray-700 hover:bg-gray-600' : 'bg-white hover:bg-gray-100'
                    }`}
                >
                    {isDark ? <Sun className="w-5 h-5"/> : <Moon className="w-5 h-5"/>}
                </button>
            </div>
        </div>
    );
};

export default Header;