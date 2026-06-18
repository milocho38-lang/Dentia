import type { Metadata } from "next";
import { AuthProvider } from "@/providers/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Dentia",
    template: "%s | Dentia",
  },
  description: "Gestión Odontológica Inteligente",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
