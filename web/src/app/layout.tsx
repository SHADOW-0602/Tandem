import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tandem Operations Center",
  description:
    "Real-time voice operations across Field Workers, Healthcare, Dispatch, and Customer Support.",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className="min-h-screen bg-[#0e0e13] text-[#fffaea] antialiased selection:bg-[#62f6b5] selection:text-black">
        {children}
      </body>
    </html>
  );
}
