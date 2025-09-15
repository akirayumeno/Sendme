// Theme configuration

export interface ThemeConfig {
  themeClasses: string;
  inputClasses: string;
  cardClasses: string;
  toggleTheme: () => void;
}

// Message types
export type DeviceType = 'phone' | 'desktop';

export type Message = TextMessage | ImageMessage | FileMessage;

export interface BaseMessage {
  id: string;
  timestamp: string;
  device: DeviceType;
  copied: boolean;
}

// text message
export interface TextMessage extends BaseMessage {
  type: 'text';
  content: string;  // text content
}

//image message
export interface ImageMessage extends BaseMessage {
  type: 'image';
  originalFile: File;
  imageUrl: string;     // url（can be presented）
  fileName: string;
  fileSize?: string;
  width?: number;       // picture width
  height?: number;      // picture height
}

//file message
export interface FileMessage extends BaseMessage {
  type: 'file';
  fileItem: FileItem;   // file information
}

// Upload file item types
export type FileStatus = 'pending' | 'uploading' | 'success' | 'error';

export interface FileItem {
  id: string;
  name: string;
  type: string;
  status: FileStatus;
  size?: string;
  progress?: number;
  error?: string;
  file: File;
  url?: string;
}