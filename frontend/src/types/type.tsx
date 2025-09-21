// Theme configuration
export interface ThemeConfig {
  themeClasses: string;
  inputClasses: string;
  cardClasses: string;
  toggleTheme: () => void;
}

// Device types
export type DeviceType = 'phone' | 'desktop';

// Message status
export type MessageStatus = 'uploading' | 'success' | 'error';

// Unified Message interface that handles all content types
export interface Message {
  id: string;
  type: 'text' | 'image' | 'file';
  status: MessageStatus;

  // Text content
  content?: string;

  // File content (for images and files)
  file?: File;
  fileName?: string;
  fileSize?: string;
  fileType?: string;
  imageUrl?: string;

  // Upload progress
  progress?: number;
  error?: string;

  // Metadata
  timestamp: string;
  device: DeviceType;
  copied: boolean;
}