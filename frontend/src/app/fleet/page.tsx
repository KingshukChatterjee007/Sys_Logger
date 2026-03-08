'use client';

import DashboardView from '../DashboardView'
import { useAuth } from '../components/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function FleetPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login')
    }
  }, [user, isLoading, router])

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center font-black uppercase tracking-widest text-xs text-zinc-400">
        Authenticating...
      </div>
    )
  }

  return <DashboardView />
}