// Theme configuration

export interface ThemeConfig {
  themeClasses: string;
  inputClasses: string;
  cardClasses: string;
  toggleTheme: () => void;
}

// Message types
export type MessageType = 'text' | 'image' | 'file';
export type DeviceType = 'phone' | 'desktop';

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string; // Consider using Date type for better type safety, but needs serialization handling
  device: DeviceType;
  copied: boolean;
  fileSize?: string; // Only exists when type = 'file' or 'image'
  fileName?: string; // Original filename for file/image types
  fileUrl?: string;  // URL to access the file for file/image types
}

// Upload file item types
export type FileStatus = 'pending' | 'uploading' | 'success' | 'error';
export type FileType = | 'pdf' | 'doc' | 'docx' | 'xls' | 'xlsx'
  | 'jpg' | 'jpeg' | 'png' | 'gif'
  | 'mp4' | 'mov' | 'avi'
  | 'mp3' | 'wav'
  | 'zip' | 'rar'
  | string;

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  status: FileStatus;
  size?: string;
  progress?: number;
  error?: string;
  file: File;
  url?: string | null;
}