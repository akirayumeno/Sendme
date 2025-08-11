import React, { useRef } from "react";
import type { ThemeConfig } from "../../types/type.tsx";

const FileInput = ({
  onFileUpload,
  themeConfig
}: {
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  themeConfig: ThemeConfig;
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={onFileUpload}
        className="hidden"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        className={`flex items-center space-x-2 py-3 px-6 rounded-xl border transition-all duration-200 font-medium ${
          themeConfig.isDark
              ? 'bg-gray-800 border-gray-600 hover:bg-gray-700 active:bg-gray-600' 
              : 'bg-gray-50 border-gray-300 hover:bg-gray-50 active:bg-gray-100'
        }`}
      >
        <span>Upload File</span>
      </button>
    </>
  );
};

export default FileInput;

