import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Among Agents · Stacja dowodzenia",
  description: "Lokalna stacja koordynacji agentów na Halloween Hack 2026.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pl"><body>{children}</body></html>;
}
