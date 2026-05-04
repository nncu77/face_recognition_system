"use client";

import { useEffect, useState } from "react";
import { listLogs, type LogEntry } from "@/lib/api";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);

  async function refresh() {
    setError(null);
    try {
      setLogs(await listLogs(limit));
    } catch (e) {
      setError(e instanceof Error ? e.message : "讀取記錄失敗");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium">辨識記錄</h1>
          <p className="text-sm text-slate-500 mt-1">
            最近 {limit} 筆 /api/recognize 結果
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value, 10))}
            className="text-sm border border-slate-300 rounded-lg px-3 py-1.5"
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={500}>500</option>
          </select>
          <button
            type="button"
            onClick={refresh}
            className="text-sm text-slate-600 hover:text-slate-900 underline"
          >
            🔄
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 rounded-lg whitespace-pre-wrap">
          {error}
        </div>
      )}

      {logs && logs.length === 0 && (
        <div className="bg-white border border-dashed border-slate-200 rounded-xl p-8 text-center text-slate-400">
          尚無辨識記錄
        </div>
      )}

      {logs && logs.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="text-left px-4 py-3">時間</th>
                <th className="text-left px-4 py-3">姓名 / user_id</th>
                <th className="text-right px-4 py-3">similarity</th>
                <th className="text-center px-4 py-3">活體</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-600 text-xs font-mono">
                    {log.timestamp}
                  </td>
                  <td className="px-4 py-3">
                    {log.name ? (
                      <>
                        <div className="font-medium">{log.name}</div>
                        <div className="text-xs text-slate-500 font-mono">
                          {log.user_id}
                        </div>
                      </>
                    ) : (
                      <span className="text-amber-700 text-sm">
                        未匹配
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {log.similarity.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {log.is_live ? (
                      <span className="text-emerald-700">✓</span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
