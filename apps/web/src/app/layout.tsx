import type { Metadata, Viewport } from 'next';
import { GeistSans } from 'geist/font/sans';
import './globals.css';
import { ibmPlexSansThai, jetBrainsMono, notoSerifThai } from '@/lib/fonts';
import { cn } from '@/lib/utils';

// Metadata
export const metadata: Metadata = {
  title: {
    default: 'TreeQ Carbon Platform — Tree Biomass Carbon Assessment',
    template: '%s | TreeQ Carbon Platform',
  },
  description:
    'แพลตฟอร์มประเมินชีวมวล คาร์บอน และ CO₂e จาก 3D point cloud พร้อมหลักฐานที่ตรวจสอบย้อนกลับได้ทุกตัวเลข',
  keywords: [
    'TreeQ Carbon Platform',
    'Carbon Stock Estimate',
    'LiDAR',
    'Point Cloud',
    'Terrestrial Laser Scanning',
    'Tree Biomass',
    'Allometric Equation',
    'TGO',
    'T-VER',
    'Climate Tech',
    'Sustainable Innovation',
  ],
  authors: [{ name: 'TreeQ Carbon Platform Team' }],
  creator: 'TreeQ Carbon Platform Team',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'https://treeqcarbon.vercel.app'),
  icons: {
    // 1254x1254 at 1.28 MB used to be the favicon, the header mark and the
    // touch icon alike — a megabyte and a quarter downloaded to draw 32 pixels.
    // og:image below still wants the large one; nothing else does.
    icon: '/logo-128.png',
    shortcut: '/logo-128.png',
    apple: '/apple-icon.png',
  },
  openGraph: {
    title: 'TreeQ Carbon Platform — Tree Biomass Carbon Assessment',
    description: 'ประเมินคาร์บอนจากต้นไม้ด้วย pipeline ที่แสดง provenance และข้อจำกัด',
    url: '/',
    siteName: 'TreeQ Carbon Platform',
    locale: 'th_TH',
    type: 'website',
    images: [
      {
        url: '/logo.png',
        width: 1024,
        height: 1024,
        alt: 'TreeQ Carbon Platform — ประเมินคาร์บอนจากต้นไม้พร้อม provenance',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TreeQ Carbon Platform',
    description: 'ประเมินคาร์บอนจากต้นไม้ด้วย pipeline ที่แสดง provenance และข้อจำกัด',
    images: ['/logo.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FAFAF8' },
    { media: '(prefers-color-scheme: dark)', color: '#0F3324' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="th"
      className={cn(
        notoSerifThai.variable,
        ibmPlexSansThai.variable,
        jetBrainsMono.variable,
        GeistSans.variable,
        'font-sans',
      )}
      suppressHydrationWarning
    >
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
