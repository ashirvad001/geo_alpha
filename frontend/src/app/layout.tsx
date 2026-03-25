import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { PortfolioProvider } from "@/context/PortfolioContext";
import { RealTimeTickerBanner } from "@/components/shared/RealTimeTickerBanner";
import { Sidebar, Navbar } from "@/components/shared/Navigation";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Geo Alpha | Nifty 50 GPR Intelligence",
  description: "Advanced Geopolitical Risk and Sentiment Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans min-h-full bg-background text-foreground flex flex-col`}>
        <PortfolioProvider>
          <RealTimeTickerBanner />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar />
            <main className="flex-1 flex flex-col min-w-0 bg-[#070707]">
              <Navbar />
              <div className="flex-1 overflow-y-auto p-8 max-md:p-4 custom-scrollbar">
                {children}
              </div>
            </main>
          </div>
        </PortfolioProvider>
      </body>
    </html>
  );
}
