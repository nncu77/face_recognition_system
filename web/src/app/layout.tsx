import type { Metadata } from "next";
import localFont from "next/font/local";
import Link from "next/link";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Face Recognition System",
  description: "InsightFace + FastAPI 端到端人臉辨識 (Next.js 前端)",
};

const NAV = [
  { href: "/", label: "🔍 辨識" },
  { href: "/register", label: "📝 註冊" },
  { href: "/users", label: "👥 用戶" },
  { href: "/logs", label: "📜 記錄" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hant">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-slate-50 min-h-screen text-slate-900`}
      >
        <header className="border-b border-slate-200 bg-white">
          <div className="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
            <Link href="/" className="font-medium text-lg">
              👤 Face Recognition
            </Link>
            <nav className="flex gap-1 text-sm sm:ml-auto">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3 py-1.5 rounded-lg hover:bg-slate-100 transition"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
