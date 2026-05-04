"use client";

import { useRef, useState } from "react";

type Props = {
  onFile: (file: File) => void;
  disabled?: boolean;
  accept?: string;
  hint?: string;
};

export function Dropzone({
  onFile,
  disabled,
  accept = "image/*",
  hint = "JPG / PNG / WebP",
}: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (disabled) return;
        const f = e.dataTransfer.files[0];
        if (f) onFile(f);
      }}
      className={`cursor-pointer border-2 border-dashed rounded-2xl p-10 text-center transition aria-disabled:opacity-50 aria-disabled:cursor-not-allowed bg-white ${
        dragOver
          ? "border-slate-700 bg-slate-50"
          : "border-slate-300 hover:border-slate-500"
      }`}
      aria-disabled={disabled}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <div className="text-3xl mb-2">📷</div>
      <div className="text-sm text-slate-700 font-medium">
        拖曳照片到這 · 或點此選檔
      </div>
      <div className="text-xs text-slate-500 mt-1">{hint}</div>
    </div>
  );
}
