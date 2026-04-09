export const getApiUrl = () => {
    // Return empty string to use relative paths (e.g. /api/units)
    // This allows Next.js rewrites to handle the proxying to the actual backend
    return ''
}

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const baseUrl = getApiUrl()
    const { headers, ...otherOptions } = options
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const cacheBuster = `cb=${Date.now()}`
    const separator = endpoint.includes('?') ? '&' : '?'
    
    return fetch(`${baseUrl}${endpoint}${separator}${cacheBuster}`, {
        mode: 'cors',
        cache: 'no-store', // Disable browser caching
        ...otherOptions,
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...(headers || {}),
        },
    })
}
