import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

// Example API utility function
export async function exampleApiCall(): Promise<any> {
    try {
        const response = await axios.get(`${BASE_URL}/`);
        return response.data;
    } catch (error) {
        console.error('Error making API call:', error);
        throw error;
    }
}