"use client";

import { useEffect, useState } from "react";
import { listUsers, deleteUser, type UserInfo } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState<UserInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      setUsers(await listUsers());
    } catch (e) {
      setError(e instanceof Error ? e.message : "讀取用戶失敗");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onDelete(u: UserInfo) {
    if (!confirm(`確定刪除「${u.name}」(${u.user_id}) ？`)) return;
    setBusyId(u.user_id);
    try {
      await deleteUser(u.user_id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "刪除失敗");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium">用戶管理</h1>
          <p className="text-sm text-slate-500 mt-1">
            {users === null
              ? "載入中…"
              : `${users.length} 位已註冊用戶`}
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="text-sm text-slate-600 hover:text-slate-900 underline"
        >
          🔄 重整
        </button>
      </header>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 rounded-lg whitespace-pre-wrap">
          {error}
        </div>
      )}

      {users && users.length === 0 && (
        <div className="bg-white border border-dashed border-slate-200 rounded-xl p-8 text-center text-slate-400">
          尚無註冊用戶。
          <br />
          去
          <a href="/register" className="text-slate-700 underline mx-1">
            註冊
          </a>
          頁加一個吧。
        </div>
      )}

      {users && users.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="text-left px-4 py-3">姓名</th>
                <th className="text-left px-4 py-3 font-mono">user_id</th>
                <th className="text-left px-4 py-3">註冊時間</th>
                <th className="px-4 py-3 w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.user_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{u.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {u.user_id}
                  </td>
                  <td className="px-4 py-3 text-slate-600 text-xs">
                    {u.created_at ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => onDelete(u)}
                      disabled={busyId === u.user_id}
                      className="text-red-600 hover:text-red-800 disabled:opacity-30 text-sm"
                    >
                      🗑️
                    </button>
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
