import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from './apiUtils'

export const useOrgs = () => {
    const [orgs, setOrgs] = useState<string[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchOrgs = useCallback(async () => {
        try {
            const response = await apiFetch('/api/orgs')
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            const result: string[] = await response.json()
            setOrgs(result)
            setLoading(false)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchOrgs()
        const interval = setInterval(fetchOrgs, 5000) // Poll for new orgs every 5s
        return () => clearInterval(interval)
    }, [fetchOrgs])

    return {
        orgs,
        loading,
        error,
        refetch: fetchOrgs
    }
}
