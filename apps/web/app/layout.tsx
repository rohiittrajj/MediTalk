import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "MediTalk", description: "A clearer path from patient history to clinician review." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
