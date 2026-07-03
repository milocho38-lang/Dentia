import { TreatmentDetailPage } from "@/components/treatments/TreatmentPages";

export default async function Page({
  params,
}: {
  params: Promise<{ treatmentId: string }>;
}) {
  const { treatmentId } = await params;
  return <TreatmentDetailPage treatmentId={treatmentId} />;
}
