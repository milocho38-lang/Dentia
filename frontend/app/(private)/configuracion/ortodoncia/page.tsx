import { PermissionGate } from "@/components/auth/PermissionGate";
import { OrthodonticsAssignmentPage } from "@/components/orthodontics/OrthodonticsAssignmentPage";
export default function OrthodonticsConfigurationPage() { return <PermissionGate permission="orthodontics.assignment.view"><OrthodonticsAssignmentPage /></PermissionGate>; }
