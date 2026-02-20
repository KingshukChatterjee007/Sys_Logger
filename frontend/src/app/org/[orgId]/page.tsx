import React from 'react'
import DashboardView from '@/components/DashboardView'

interface PageProps {
    params: Promise<{ orgId: string }>
}

export default async function OrgDashboard({ params }: PageProps) {
    const { orgId } = await params
    // URI decode the ID in case it has spaces or special chars
    const decodedOrgId = decodeURIComponent(orgId)

    return <DashboardView orgId={decodedOrgId} />
}
