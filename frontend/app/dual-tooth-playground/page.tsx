import { notFound } from "next/navigation";
import { DualClinicalToothPlayground } from "@/components/odontogram/classic";

export default function DualToothPlaygroundPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return <DualClinicalToothPlayground />;
}
