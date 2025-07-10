import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Poker App',
    description: 'A Next.js Poker Application',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}