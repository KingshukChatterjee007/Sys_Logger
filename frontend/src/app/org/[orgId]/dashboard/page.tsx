'use client'
import React from 'react'
import { useParams } from 'next/navigation'
import DashboardView from '@/components/DashboardView'

export default function OrgDashboard() {
    const params = useParams()
    const orgId = params.orgId as string

    return <DashboardView orgId={orgId} />
}
