import { notFound } from "next/navigation";
import { RealDualOdontogramPreview } from "@/components/odontogram/classic/RealDualOdontogramPreview";

export default async function PatientDualOdontogramPreviewPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  const { patientId } = await params;
  return <RealDualOdontogramPreview patientId={patientId} />;
}
