import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dentia",
  description: "Plataforma de gestion odontologica",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
