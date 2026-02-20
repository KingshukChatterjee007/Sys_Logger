export const getApiUrl = () => {
<<<<<<< HEAD
    // Return empty string to use relative paths (e.g. /api/units)
    // This allows Next.js rewrites to handle the proxying to the actual backend
    return ''
=======
    // If running in browser and HTTPS, use relative path (proxy) to avoid Mixed Content (HTTPS -> HTTP)
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
        return ''
    }

    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL
    }

    // Default to the public IP for local development or HTTP
    return 'http://203.193.145.59:5010'
>>>>>>> 94571205259c2bf6c077a807c402a192098f910c
}

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const baseUrl = getApiUrl()
    const { headers, ...otherOptions } = options

    return fetch(`${baseUrl}${endpoint}`, {
        mode: 'cors',
        ...otherOptions,
        headers: {
            'Content-Type': 'application/json',
            ...(headers || {}),
        },
    })
}
