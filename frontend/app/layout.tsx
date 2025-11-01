import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "./components/Navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lexiconnect - Linguistic Data Visualization",
  description: "Visualize and explore linguistic connections and data",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-stone-50 text-stone-950`}>
        <Navigation />
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  );
}
