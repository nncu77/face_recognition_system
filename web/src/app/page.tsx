"use client";

import { useState } from "react";
import { Dropzone } from "@/components/Dropzone";
import { recognize, type RecognizeResponse } from "@/lib/api";

export default function RecognizePage() {
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  const [result, setResult] = useState<RecognizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onFile(file: File) {
    setError(null);
    setResult(null);
    setImgSize(null);
    const reader = new FileReader();
    reader.onload = () => setImgUrl(reader.result as string);
    reader.readAsDataURL(file);

    setLoading(true);
    try {
      const r = await recognize(file);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "recognize 失敗");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-medium">人臉辨識</h1>
        <p className="text-sm text-slate-500 mt-1">
          上傳照片 → InsightFace buffalo_l 偵測 + 跟資料庫 1:N 比對
        </p>
      </header>

      <Dropzone onFile={onFile} disabled={loading} />

      {loading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-3 rounded-lg">
          辨識中…
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 rounded-lg whitespace-pre-wrap">
          {error}
        </div>
      )}

      {imgUrl && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
              照片
            </div>
            <div className="relative">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imgUrl}
                alt="uploaded"
                className="w-full rounded-xl border border-slate-200"
                onLoad={(e) => {
                  const t = e.currentTarget;
                  setImgSize({ w: t.naturalWidth, h: t.naturalHeight });
                }}
              />
              {result?.bbox && imgSize && (
                <svg
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  <rect
                    x={result.bbox[0]}
                    y={result.bbox[1]}
                    width={result.bbox[2] - result.bbox[0]}
                    height={result.bbox[3] - result.bbox[1]}
                    fill="none"
                    stroke={result.matched ? "rgb(34,197,94)" : "rgb(239,68,68)"}
                    strokeWidth={Math.max(2, imgSize.w / 250)}
                  />
                  {result.name && (
                    <text
                      x={result.bbox[0]}
                      y={Math.max(20, result.bbox[1] - 8)}
                      fontSize={Math.max(14, imgSize.w / 35)}
                      fill={result.matched ? "rgb(34,197,94)" : "rgb(239,68,68)"}
                      fontWeight="bold"
                    >
                      {result.name} · {(result.similarity * 100).toFixed(1)}%
                    </text>
                  )}
                </svg>
              )}
            </div>
          </div>

          <aside className="space-y-3">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              結果
            </div>
            {result ? (
              <div className="space-y-3">
                {result.matched ? (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
                    <div className="text-emerald-700 text-sm font-medium">
                      ✅ 比對成功
                    </div>
                    <div className="text-2xl font-medium mt-1">
                      {result.name}
                    </div>
                    <div className="text-xs font-mono text-slate-500 mt-1">
                      {result.user_id}
                    </div>
                  </div>
                ) : (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <div className="text-amber-800 text-sm font-medium">
                      ❌ 找不到匹配人臉
                    </div>
                    <div className="text-xs text-amber-700 mt-1">
                      {result.bbox === null
                        ? "未偵測到任何臉"
                        : `最高相似度 ${(result.similarity * 100).toFixed(1)}% 低於閾值`}
                    </div>
                  </div>
                )}

                <div className="bg-white border border-slate-200 rounded-xl p-4 text-xs space-y-2 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-500">similarity</span>
                    <span>{result.similarity.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">det_score</span>
                    <span>{result.det_score.toFixed(3)}</span>
                  </div>
                  {result.bbox && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">bbox</span>
                      <span>
                        [{result.bbox.join(", ")}]
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white border border-dashed border-slate-200 rounded-xl p-4 text-sm text-slate-400">
                上傳後顯示結果
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
