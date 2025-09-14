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
  imageUrl: string;     // url（can be presented）
  caption?: string;     // option(picture description)
  width?: number;       // picture width
  height?: number;      // picture height
}

//file message
export interface FileMessage extends BaseMessage {
  type: 'file';
  fileItem: FileItem;   // file information
  description?: string; // option(file description)
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