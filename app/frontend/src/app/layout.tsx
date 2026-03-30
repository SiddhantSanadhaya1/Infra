import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsureCo Insurance Portal",
  description: "Policy management and claims processing system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {/* Header */}
        <header className="bg-brand-navy text-white shadow-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
                <div className="bg-brand-red rounded px-2 py-1">
                  <span className="text-white font-black text-xl tracking-tight">InsureCo</span>
                </div>
                <div className="hidden sm:block">
                  <p className="text-white font-semibold text-sm leading-tight">Insurance Portal</p>
                  <p className="text-gray-400 text-xs leading-tight">Policy &amp; Claims Management</p>
                </div>
              </Link>

              {/* Navigation */}
              <nav className="flex items-center gap-1">
                <Link
                  href="/"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/policies"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                >
                  Policies
                </Link>
                <Link
                  href="/claims"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                >
                  Claims
                </Link>
                <Link
                  href="/quotes"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                >
                  Quotes
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="min-h-screen bg-gray-50">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-brand-navy text-gray-400 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="bg-brand-red rounded px-1.5 py-0.5">
                  <span className="text-white font-black text-sm">InsureCo</span>
                </div>
                <span className="text-sm">American International Group, Inc.</span>
              </div>
              <div className="flex gap-6 text-sm">
                <span>Privacy Policy</span>
                <span>Terms of Service</span>
                <span>Contact Support</span>
              </div>
              <p className="text-xs text-gray-500">
                &copy; {new Date().getFullYear()} InsureCo. Demo Application. All rights reserved.
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
