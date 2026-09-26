import type {
  PeriodontalExam,
  PeriodontalExamSnapshot,
  PeriodontalExamVersion,
} from "@/types/periodontogram";

const hasHistoricalClinicalSnapshot = (
  snapshot: PeriodontalExamVersion["snapshot"],
): snapshot is PeriodontalExamSnapshot =>
  snapshot !== null &&
  Array.isArray(snapshot.teeth) &&
  typeof snapshot.coverage === "object" &&
  snapshot.coverage !== null &&
  typeof snapshot.indices === "object" &&
  snapshot.indices !== null;

export const sortedPeriodontalVersions = (exam: PeriodontalExam) =>
  [...exam.versions].sort((left, right) => right.version_number - left.version_number);

export const findReplacingVersion = (
  exam: PeriodontalExam,
  version: PeriodontalExamVersion,
) => exam.versions.find((candidate) => candidate.supersedes_version_id === version.id) ?? null;

export const historicalPeriodontalExam = (
  exam: PeriodontalExam,
  versionId: string,
): PeriodontalExam | null => {
  if (versionId === exam.current_version.id) return exam;

  const version = exam.versions.find((candidate) => candidate.id === versionId);
  if (!version || !hasHistoricalClinicalSnapshot(version.snapshot)) return null;

  return {
    ...exam,
    status: version.status,
    finalized_at: version.finalized_at,
    row_version: version.row_version,
    current_version: version,
    teeth: version.snapshot.teeth,
    coverage: version.snapshot.coverage,
    indices: version.snapshot.indices,
  };
};
