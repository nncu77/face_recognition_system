"use client";

import { useState } from "react";
import { Dropzone } from "@/components/Dropzone";
import { registerUser, type RegisterResponse } from "@/lib/api";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RegisterResponse | null>(null);

  async function onFile(file: File) {
    if (!name.trim()) {
      setError("請先輸入姓名");
      return;
    }
    setError(null);
    setResult(null);
    const reader = new FileReader();
    reader.onload = () => setImgUrl(reader.result as string);
    reader.readAsDataURL(file);

    setLoading(true);
    try {
      const r = await registerUser(name.trim(), file);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "註冊失敗");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <header>
        <h1 className="text-2xl font-medium">註冊新用戶</h1>
        <p className="text-sm text-slate-500 mt-1">
          每張臉抽 512-dim ArcFace embedding 存進 SQLite，之後可被辨識比對
        </p>
      </header>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          姓名
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例：王小明"
          className="w-full bg-white border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-slate-700"
        />
      </div>

      <Dropzone onFile={onFile} disabled={loading || !name.trim()} />

      {loading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-3 rounded-lg">
          產生 embedding 中…
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 rounded-lg whitespace-pre-wrap">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
          <div className="text-emerald-700 text-sm font-medium">
            ✅ {result.message}
          </div>
          <div className="mt-2 text-sm">
            <span className="text-slate-500">姓名：</span>
            <span className="font-medium">{result.name}</span>
          </div>
          <div className="mt-1 text-xs text-slate-500 font-mono">
            user_id: {result.user_id}
          </div>
        </div>
      )}

      {imgUrl && (
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
            上傳的照片
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgUrl}
            alt="registered"
            className="max-w-md rounded-xl border border-slate-200"
          />
        </div>
      )}
    </div>
  );
}
