"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getRole, getToken, getRoleRedirect } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (token && role) {
      router.replace(getRoleRedirect(role));
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-500">Redirecting...</p>
    </div>
  );
}
