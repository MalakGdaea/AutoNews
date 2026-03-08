import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const heading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap"
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
  display: "swap"
});

export const metadata = {
  title: "AutoNews Dashboard",
  description: "Monitor posts, configure topics, and manually upload ready videos."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${heading.variable} ${mono.variable}`}>
      <body className="font-[var(--font-heading)] antialiased">
        <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-8">{children}</main>
      </body>
    </html>
  );
}
