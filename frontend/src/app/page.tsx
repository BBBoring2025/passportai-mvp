import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      {/* Navbar */}
      <nav className="border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">
            Passport<span className="text-blue-600">AI</span>
          </span>
          <Link
            href="/login"
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-block mb-6 px-3 py-1 text-xs font-medium rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
          EU Digital Product Passport — Ready
        </div>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-tight max-w-3xl mx-auto">
          Compliance automation for textile supply chains
        </h1>
        <p className="mt-6 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
          PassportAI extracts, validates, and organizes the documents you need
          for Digital Product Passports — so your team can stop chasing
          spreadsheets and start shipping compliant products.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/login"
            className="px-6 py-3 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Get Started
          </Link>
          <a
            href="#how-it-works"
            className="px-6 py-3 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
          >
            See How It Works
          </a>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: "Minutes", label: "Not weeks — from upload to passport" },
            { value: "40+", label: "Data fields extracted per product" },
            { value: "3", label: "User roles supported" },
            { value: "24/7", label: "Automated compliance checks" },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl font-bold text-blue-600">
                {stat.value}
              </div>
              <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center">
          Everything you need for DPP compliance
        </h2>
        <p className="mt-4 text-center text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          From document intake to regulatory submission — one platform for
          buyers, suppliers, and compliance teams.
        </p>
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          {[
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12-3-3m0 0-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                </svg>
              ),
              title: "Smart Document Upload",
              description:
                "Drag-and-drop invoices, test reports, certificates, and BOMs. We accept PDF, JPG, and PNG.",
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
              ),
              title: "AI-Powered Extraction",
              description:
                "Automatically extract key data fields — material composition, certifications, supplier identity, and more.",
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              ),
              title: "Compliance Validation",
              description:
                "Real-time checks against EU DPP requirements. See exactly what's missing before submission.",
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
                </svg>
              ),
              title: "Buyer–Supplier Collaboration",
              description:
                "Buyers track supplier readiness. Suppliers manage their cases. Everyone sees live status.",
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" />
                </svg>
              ),
              title: "Readiness Dashboard",
              description:
                "At-a-glance metrics for every supplier — overall score, document coverage, and open issues.",
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
                </svg>
              ),
              title: "Admin Review Queue",
              description:
                "Admins review extracted data, approve or reject submissions, and keep the pipeline moving.",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                {feature.icon}
              </div>
              <h3 className="mt-4 font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="border-y border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900"
      >
        <div className="max-w-6xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-center">How it works</h2>
          <p className="mt-4 text-center text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
            Three roles, one streamlined workflow.
          </p>
          <div className="mt-16 grid md:grid-cols-3 gap-12">
            {[
              {
                step: "1",
                role: "Supplier",
                description:
                  "Upload commercial invoices, test reports, OEKO-TEX certificates, and safety data sheets. PassportAI extracts the data automatically.",
              },
              {
                step: "2",
                role: "Admin",
                description:
                  "Review extracted fields, resolve flagged issues, and approve or reject each case through the review queue.",
              },
              {
                step: "3",
                role: "Buyer",
                description:
                  "Monitor supplier readiness scores on your dashboard. Track compliance progress across your entire supply chain.",
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-10 h-10 mx-auto rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                  {item.step}
                </div>
                <h3 className="mt-4 font-semibold text-lg">{item.role}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Video */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl font-bold">See it in action</h2>
        <p className="mt-4 text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          Watch a 2-minute walkthrough of the full buyer–supplier–admin workflow.
        </p>
        <a
          href="https://youtu.be/u14T2_ferbs"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-8 inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
          Watch Demo Video
        </a>
      </section>

      {/* Try the Demo */}
      <section className="border-y border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-center">Try the demo</h2>
          <p className="mt-4 text-center text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
            Sign in with any of the accounts below to explore each role.
            All accounts use the same password.
          </p>
          <div className="mt-12 grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            {[
              {
                role: "Buyer",
                email: "buyer@nordic.com",
                color: "blue",
              },
              {
                role: "Supplier",
                email: "info@yildiz.com",
                color: "green",
              },
              {
                role: "Admin",
                email: "admin@nordic.com",
                color: "purple",
              },
            ].map((account) => (
              <div
                key={account.role}
                className="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 text-center"
              >
                <div className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {account.role}
                </div>
                <div className="mt-2 font-mono text-sm font-medium">
                  {account.email}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 text-center">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Password for all accounts:{" "}
            </span>
            <code className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-sm font-mono font-medium">
              demo1234
            </code>
          </div>
          <div className="mt-8 text-center">
            <Link
              href="/login"
              className="px-6 py-3 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Sign In to Try It
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl font-bold">
          Ready to simplify DPP compliance?
        </h2>
        <p className="mt-4 text-gray-600 dark:text-gray-400 max-w-lg mx-auto">
          Sign in to start uploading documents, tracking compliance, and
          collaborating with your supply chain partners.
        </p>
        <Link
          href="/login"
          className="mt-8 inline-block px-8 py-3 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          Sign In to Your Account
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500 dark:text-gray-500">
          <span>
            &copy; {new Date().getFullYear()} PassportAI. All rights reserved.
          </span>
          <span>DPP Operations Module for Textile Supply Chains</span>
        </div>
      </footer>
    </div>
  );
}
