import React, { useState } from "react";
import SendButton from "./sendButton.tsx";
import TextInput from "./textInput.tsx";
import FileInput from "./fileInput.tsx";
import type { ThemeConfig } from "../../types/type.tsx";

const InputArea = ({
  inputText,
  setInputText,
  onSend,
  onFileUpload,
  themeConfig
}: {
  inputText: string;
  setInputText: (text: string) => void;
  onSend: () => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  themeConfig: ThemeConfig;
}) => {
  const [dragOver, setDragOver] = useState<boolean>(false);

  const handlePaste = async (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {  // 检查是否是文件类型
        const file = item.getAsFile();
        if (file) {
          handleFile(file);
        }
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    // 创建符合类型要求的事件对象
    const event = {
      target: {
        files: [file],
        value: '',
      },
      currentTarget: {
        files: [file],
        value: '',
      },
      nativeEvent: new Event('change'),
      preventDefault: () => {},
      stopPropagation: () => {},
      persist: () => {},
      type: 'change',
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    onFileUpload(event);
    setInputText(inputText + `[File: ${file.name}]`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className={`${themeConfig.cardClasses} border-t p-6`}>
      <div className="max-w-3xl mx-auto">
        <div className="space-y-4">
          <TextInput
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPaste={handlePaste}
            onKeyDown={handleKeyDown}
            dragOver={dragOver}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            themeConfig={themeConfig}
          />

          <div className="flex space-x-3">
            <FileInput onFileUpload={onFileUpload} themeConfig={themeConfig}/>
            <SendButton
              onClick={onSend}
              disabled={!inputText.trim()}
              themeConfig={themeConfig}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default InputArea;