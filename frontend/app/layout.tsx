import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Isometric → MTO Generator",
  description:
    "Upload a piping isometric drawing (PNG, JPG, or PDF) and automatically generate a validated Material Take-Off (MTO) using an AI vision pipeline.",
  keywords: ["piping isometric", "MTO", "material take-off", "AI", "piping engineering"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 z-50 bg-navy text-white px-3 py-2 rounded text-sm font-medium"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
