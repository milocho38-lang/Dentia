import { notFound } from "next/navigation";
import { ToothPlayground } from "@/components/odontogram/Tooth/ToothPlayground";

export default function OdontogramPlaygroundPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return <ToothPlayground />;
}
