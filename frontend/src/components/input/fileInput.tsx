import React, { useRef } from "react";
import type { ThemeConfig } from "../../types/type.tsx";

const FileInput = ({
  onFileUpload
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
    </>
  );
};

export default FileInput;

