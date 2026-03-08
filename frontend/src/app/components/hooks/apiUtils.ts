export const getApiUrl = () => {
    // Return empty string to use relative paths (e.g. /api/units)
    // This allows Next.js rewrites to handle the proxying to the actual backend
    return ''
}

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const baseUrl = getApiUrl()
    const { headers, ...otherOptions } = options
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    return fetch(`${baseUrl}${endpoint}`, {
        mode: 'cors',
        ...otherOptions,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...(headers || {}),
        },
    })
}
