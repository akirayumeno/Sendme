// Text Input Component
import {useEffect, useRef} from "react";
import type {ThemeConfig} from "../../types/type.tsx";

const TextInput = ({
  value,
  onChange,
  onPaste,
  onKeyDown,
  dragOver,
  onDragOver,
  onDragLeave,
  onDrop,
  themeConfig
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onPaste: (e: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  dragOver: boolean;
  onDragOver: (e: React.DragEvent<HTMLDivElement>) => void;
  onDragLeave: (e: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (e: React.DragEvent<HTMLDivElement>, files: FileList) => void;
  themeConfig: ThemeConfig;
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [value]);

  return (
    <div
      className={`relative transition-all duration-200 ${
        dragOver ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
      }`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={(e) => {
    e.preventDefault();
    onDrop(e, e.dataTransfer.files);
  }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={onChange}
        onPaste={onPaste}
        onKeyDown={onKeyDown}
        placeholder="Type your message..."
        className={`w-full p-4 border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${themeConfig.inputClasses}`}
        rows={1}
        style={{ minHeight: '48px', maxHeight: '120px' }}
      />

      {dragOver && (
        <div className="absolute inset-0 bg-blue-500 bg-opacity-10 border-2 border-blue-500 border-dashed rounded-xl flex items-center justify-center">
          <div className="text-blue-500 text-base font-medium">Drop files here</div>
        </div>
      )}
    </div>
  );
};

export default TextInput;