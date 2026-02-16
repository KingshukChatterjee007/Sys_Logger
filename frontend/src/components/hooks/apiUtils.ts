export const getApiUrl = () => {
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL
    }
    // Default to localhost:5000 for dev
    return 'http://localhost:5000'
}

export const apiFetch = async (endpoint: string) => {
    const baseUrl = getApiUrl()
    const response = await fetch(`${baseUrl}${endpoint}`, {
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    return response
}
