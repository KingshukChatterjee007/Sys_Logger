'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'

interface User {
    user_id: number
    username: string
    role: 'admin' | 'org'
    org_id: number | null
    org_slug: string | null
    org_name: string | null
    tier?: string
}

interface AuthContextType {
    user: User | null
    token: string | null
    loading: boolean
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>
    logout: () => void
    isAdmin: boolean
    isOrg: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [token, setToken] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const router = useRouter()
    const pathname = usePathname()

    // On mount, check for stored token
    useEffect(() => {
        const storedToken = localStorage.getItem('syslogger_token')
        const storedUser = localStorage.getItem('syslogger_user')
        if (storedToken && storedUser) {
            setToken(storedToken)
            try {
                setUser(JSON.parse(storedUser))
            } catch {
                localStorage.removeItem('syslogger_token')
                localStorage.removeItem('syslogger_user')
            }
        }
        setLoading(false)
    }, [])

    // Redirect logic
    useEffect(() => {
        if (loading) return
        const publicPaths = ['/login', '/reset-password', '/']
        const isPublic = publicPaths.some(p => pathname === p || pathname.startsWith('/reset-password'))

        if (!user && !isPublic) {
            router.push('/login')
        }
    }, [user, loading, pathname, router])

    const login = async (username: string, password: string) => {
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            })
            const data = await res.json()
            if (!res.ok) {
                return { success: false, error: data.error || 'Login failed' }
            }
            setToken(data.token)
            setUser(data.user)
            localStorage.setItem('syslogger_token', data.token)
            localStorage.setItem('syslogger_user', JSON.stringify(data.user))

            // Redirect based on role
            if (data.user.role === 'admin') {
                router.push('/admin')
            } else if (data.user.org_slug) {
                router.push(`/${data.user.org_slug}`)
            }
            return { success: true }
        } catch (err) {
            return { success: false, error: 'Network error' }
        }
    }

    const logout = () => {
        setUser(null)
        setToken(null)
        localStorage.removeItem('syslogger_token')
        localStorage.removeItem('syslogger_user')
        router.push('/login')
    }

    return (
        <AuthContext.Provider value={{
            user,
            token,
            loading,
            login,
            logout,
            isAdmin: user?.role === 'admin',
            isOrg: user?.role === 'org',
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) throw new Error('useAuth must be used within AuthProvider')
    return context
}
