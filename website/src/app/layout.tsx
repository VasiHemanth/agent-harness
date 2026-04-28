import type { Metadata } from "next";
import "./globals.css";
import { FAQ_ITEMS } from "@/components/FAQ";

const SITE_URL = "https://tokentelemetry.com";
const TITLE = "TokenTelemetry — See exactly what your coding agents cost, think, and do";
const DESCRIPTION =
  "Local, read-only observability for Claude Code, Codex, Gemini, Cursor, Copilot, and 4 more coding agents. Tokens, traces, cost — one command, no signup, 100% on your machine.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  applicationName: "TokenTelemetry",
  keywords: [
    "AI agent observability",
    "Claude Code dashboard",
    "Codex token tracking",
    "Gemini CLI cost",
    "local AI observability",
    "coding agent monitoring",
    "LLM token cost tracker",
    "Cursor logs",
    "open source agent telemetry",
  ],
  authors: [{ name: "Hemanth Vasi", url: "https://www.linkedin.com/in/vasi-hemanth/" }],
  creator: "Hemanth Vasi",
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: "TokenTelemetry",
    type: "website",
    locale: "en_US",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "TokenTelemetry" }],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    creator: "@VasiHemanth",
    images: ["/og.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
  },
  verification: {
    google: process.env.GOOGLE_VERIFICATION,
    other: process.env.BING_VERIFICATION
      ? { "msvalidate.01": process.env.BING_VERIFICATION }
      : undefined,
  },
};

const JSON_LD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "TokenTelemetry",
  url: SITE_URL,
  description: DESCRIPTION,
  applicationCategory: "DeveloperApplication",
  operatingSystem: "macOS, Linux, Windows",
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  license: "https://opensource.org/licenses/MIT",
  author: { "@type": "Person", name: "Hemanth Vasi", url: "https://www.linkedin.com/in/vasi-hemanth/" },
  codeRepository: "https://github.com/VasiHemanth/tokentelemetry",
};

const FAQ_LD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQ_ITEMS.map(({ q, a }) => ({
    "@type": "Question",
    name: q,
    acceptedAnswer: { "@type": "Answer", text: a },
  })),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_LD) }}
        />
      </body>
    </html>
  );
}
