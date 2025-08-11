// Types
export interface Message {
  id: number;
  type: 'text' | 'image';
  content: string;
  timestamp: string;
  device: 'phone' | 'desktop';
  copied: boolean;
}

export interface ThemeConfig {
    isDark: boolean;
    themeClasses: string;
    cardClasses: string;
    inputClasses: string;
}

