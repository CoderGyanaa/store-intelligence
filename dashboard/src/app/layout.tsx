import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'StoreMind AI — Store Intelligence Platform',
  description: 'Real-time retail analytics powered by CCTV intelligence',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-dark-900 text-slate-200 antialiased">{children}</body>
    </html>
  )
}
