export function resolveCatalogClinicalTargets(priceProvenance, tooth) {
  const graphicalTargets = priceProvenance?.graphical_targets;
  const teeth = graphicalTargets && typeof graphicalTargets === "object" && !Array.isArray(graphicalTargets)
    && Array.isArray(graphicalTargets.teeth)
    ? graphicalTargets.teeth.filter((value) => typeof value === "string")
    : [];
  const required = typeof priceProvenance?.required_dentition === "string"
    ? priceProvenance.required_dentition
    : null;
  const inferred = tooth && /^[5-8][1-5]$/.test(tooth) ? "PRIMARY" : "PERMANENT";
  return {
    fixedTeeth: teeth,
    zone: teeth.length ? "ANTERIOR" : null,
    dentition: required ?? inferred,
    requiredDentition: required,
  };
}
