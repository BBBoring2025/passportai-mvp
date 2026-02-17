"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { AuthData, saveAuth } from "@/lib/auth";

function AcceptInviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="w-full max-w-sm text-center space-y-4">
        <h1 className="text-2xl font-bold">PassportAI</h1>
        <div className="p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-700 dark:text-red-400">
            Gecersiz davet linki. Lutfen alici firmadan yeni bir davet
            isteyin.
          </p>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("Sifreler eslesmiyor.");
      return;
    }
    if (password.length < 6) {
      setError("Sifre en az 6 karakter olmalidir.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<AuthData & { message: string }>(
        "/auth/accept-invite",
        {
          method: "POST",
          body: JSON.stringify({
            token,
            full_name: fullName,
            password,
          }),
        }
      );
      saveAuth(data);
      router.push("/supplier/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hesap olusturulamadi");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
      <h1 className="text-2xl font-bold text-center">PassportAI</h1>
      <p className="text-sm text-gray-500 text-center">
        Daveti Kabul Et — Tedarikci hesabinizi olusturun
      </p>

      {error && (
        <div className="p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      <div>
        <label htmlFor="fullName" className="block text-sm font-medium mb-1">
          Ad Soyad
        </label>
        <input
          id="fullName"
          type="text"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Ahmet Yilmaz"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium mb-1">
          Sifre
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="En az 6 karakter"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label
          htmlFor="passwordConfirm"
          className="block text-sm font-medium mb-1"
        >
          Sifre Tekrar
        </label>
        <input
          id="passwordConfirm"
          type="password"
          required
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 px-4 bg-foreground text-background rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {loading ? "Hesap olusturuluyor..." : "Hesap Olustur"}
      </button>

      <p className="text-xs text-gray-400 text-center">
        Zaten hesabiniz var mi?{" "}
        <a href="/login" className="text-blue-500 hover:underline">
          Giris yapin
        </a>
      </p>
    </form>
  );
}

export default function AcceptInvitePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 font-[family-name:var(--font-geist-sans)]">
      <Suspense
        fallback={
          <p className="text-gray-500 text-center">Yukleniyor...</p>
        }
      >
        <AcceptInviteForm />
      </Suspense>
    </div>
  );
}
