export function managedAppointments(agenda) {
  return (
    agenda.appointments_created +
    agenda.appointments_confirmed_by_actor +
    agenda.appointments_rescheduled_by_actor +
    agenda.appointments_completed_by_actor +
    agenda.appointments_cancelled_by_actor
  );
}

export function hasUsageActivity(report) {
  if (!report) return false;
  return [
    report.general.active_days,
    managedAppointments(report.agenda),
    report.patients.patients_created_by_actor,
    report.patients.unique_patients_with_actor_activity,
    report.clinical.clinical_records_opened,
    report.clinical.clinical_evolutions_created,
    report.clinical.clinical_evolutions_signed,
    report.clinical.addenda_created,
    report.treatments.treatments_created,
    report.treatments.treatment_procedures_registered,
    report.consents.consents_created,
    report.consents.consents_shared,
    report.consents.consents_accepted,
    report.orthodontics.orthodontic_cases_created,
    report.orthodontics.orthodontic_evolutions_created,
    report.orthodontics.orthodontic_evolutions_signed,
    report.orthodontics.orthodontic_records_finalized,
    report.administrative_activity.payments_registered,
    report.administrative_activity.payments_reversed,
  ].some((value) => value > 0);
}

export function hasOrthodonticActivity(metrics) {
  return Object.values(metrics).some((value) => value > 0);
}

export function isPeriodComplete(periodMode, startDate, endDate) {
  if (periodMode === "last_7_days" || periodMode === "last_30_days") return true;
  if (periodMode === "pilot_to_date") return Boolean(startDate);
  return Boolean(startDate && endDate && startDate <= endDate);
}
