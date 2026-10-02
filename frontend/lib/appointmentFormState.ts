export interface AppointmentScheduleFormState {
  appointmentDate: string;
  time: string;
  typeId: string;
  duration: number;
}

export interface AppointmentTypeDefaults {
  id: string;
  suggested_duration_minutes: number;
}

export function initializeAppointmentSchedule(
  current: AppointmentScheduleFormState,
  initialDate: string,
  initialTime: string,
  defaultType?: AppointmentTypeDefaults,
): AppointmentScheduleFormState {
  const hasSelectedType = Boolean(current.typeId);
  return {
    appointmentDate: initialDate,
    time: initialTime,
    typeId: hasSelectedType ? current.typeId : defaultType?.id ?? "",
    duration: hasSelectedType
      ? current.duration
      : defaultType?.suggested_duration_minutes ?? current.duration,
  };
}

export function applyAppointmentType(
  current: AppointmentScheduleFormState,
  appointmentType: AppointmentTypeDefaults,
): AppointmentScheduleFormState {
  return {
    ...current,
    typeId: appointmentType.id,
    duration: appointmentType.suggested_duration_minutes,
  };
}
