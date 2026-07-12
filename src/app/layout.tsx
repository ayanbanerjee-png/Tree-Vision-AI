import type { Metadata } from 'next';
import { Inter, Outfit } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { LayoutWrapper } from '@/components/layout-wrapper';
import './globals.css';

const inter = Inter({
  variable: '--font-sans',
  subsets: ['latin'],
  display: 'swap',
});

const outfit = Outfit({
  variable: '--font-outfit',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'TreeVision AI - AI-powered Tree Species Identification and Assessment',
  description: 'Identify tree species and assess tree health instantly using advanced deep learning. Explore analytics, track batch uploads, and manage historical predictions.',
  keywords: ['AI tree identification', 'tree species assessment', 'arboriculture AI', 'tree health monitoring', 'deep learning forestry'],
  authors: [{ name: 'TreeVision AI Team' }],
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full font-sans antialiased bg-slate-50 dark:bg-zinc-950 text-slate-900 dark:text-zinc-50">
        <ThemeProvider>
          <LayoutWrapper>
            {children}
          </LayoutWrapper>
        </ThemeProvider>
      </body>
    </html>
  );
}
