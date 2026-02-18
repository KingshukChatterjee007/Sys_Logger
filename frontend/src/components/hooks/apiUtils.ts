export const getApiUrl = () => {
    // If running in browser and HTTPS, use relative path (proxy) to avoid Mixed Content (HTTPS -> HTTP)
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
        return ''
    }

    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL
    }

    // Default to the public IP for local development or HTTP
    return 'http://203.193.145.59:5010'
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
