import { BrandMark } from "@/components/brand/BrandMark";
import { Spinner } from "@/components/shared/Spinner";

export function AuthLoadingScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-dentia-background px-6">
      <div className="flex flex-col items-center text-center">
        <BrandMark />
        <Spinner className="mt-8 h-7 w-7 text-dentia-primary" />
        <p className="mt-4 text-sm font-medium text-slate-500">
          Verificando tu sesión…
        </p>
      </div>
    </main>
  );
}
