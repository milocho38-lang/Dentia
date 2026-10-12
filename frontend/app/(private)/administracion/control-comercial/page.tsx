import { PermissionGate } from "@/components/auth/PermissionGate";
import { CommercialControlPage } from "@/components/platform/CommercialControlPage";
export default function Page(){return <PermissionGate permission="platform.commercial.view"><CommercialControlPage/></PermissionGate>}
