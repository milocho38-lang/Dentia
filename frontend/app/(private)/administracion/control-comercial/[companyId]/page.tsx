"use client";
import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { CommercialAccountPage } from "@/components/platform/CommercialControlPage";
export default function Page({params}:{params:Promise<{companyId:string}>}){const {companyId}=use(params);return <PermissionGate permission="platform.commercial.manage"><CommercialAccountPage companyId={companyId}/></PermissionGate>}
