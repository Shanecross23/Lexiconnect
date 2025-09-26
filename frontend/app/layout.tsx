import "./globals.css";
import { Inter } from "next/font/google";
import { Metadata } from "next";
import { Providers } from "./providers";
import { Toaster } from "react-hot-toast";
import Navigation from "./components/Navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lexiconnect",
  description:
    "IGT-first, graph-native tool for endangered/minority language documentation and research",
  keywords: [
    "linguistics",
    "language documentation",
    "IGT",
    "endangered languages",
  ],
  authors: [{ name: "Lexiconnect Team" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50`}>
        <Providers>
          <div className="min-h-full">
            <Navigation />
            <main>{children}</main>
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#363636",
                color: "#fff",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
