import { Suspense } from "react";
import LoginClient from "./LoginClient";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto flex min-h-[80vh] w-full max-w-4xl items-center justify-center">
          <section className="glass w-full max-w-lg rounded-3xl p-6 shadow-panel md:p-8">
            <p className="text-sm text-muted">Loading sign-in...</p>
          </section>
        </div>
      }
    >
      <LoginClient />
    </Suspense>
  );
}
