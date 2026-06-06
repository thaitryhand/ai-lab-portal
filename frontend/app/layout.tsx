import type { Metadata } from "next";

import { JsonLd } from "@/components/seo/json-ld";
import { webSiteSchema, organizationSchema } from "@/lib/seo/json-ld";
import { ReducedMotionProvider } from "@/components/reduced-motion-provider";
import { SessionProvider } from "@/components/session-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";

import "./globals.css";

const siteName = "AI Lab Portal";
const siteDescription = "Editorial AI engineering — exploring agent workflows, MCP integrations, and production AI patterns.";
const siteUrl = "https://ai-lab-portal.dev";

export const metadata: Metadata = {
  title: {
    default: siteName,
    template: `%s | ${siteName}`,
  },
  description: siteDescription,
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/apple-icon.svg", type: "image/svg+xml", sizes: "180x180" }],
  },
  openGraph: {
    siteName,
    type: "website",
    locale: "en_US",
    url: siteUrl,
  },
  twitter: {
    card: "summary_large_image",
    title: siteName,
    description: siteDescription,
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <SessionProvider>
            <ReducedMotionProvider>{children}</ReducedMotionProvider>
            <Toaster position="bottom-right" richColors />
          </SessionProvider>
        </ThemeProvider>
        <JsonLd data={webSiteSchema()} />
        <JsonLd data={organizationSchema()} />
      </body>
    </html>
  );
}
