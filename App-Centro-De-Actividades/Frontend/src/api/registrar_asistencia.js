import { http } from './http.js';

export const registrarAsistencia = async (token) => {
    try {
        const response = await http.post('/api/asistencia/registrar', { token });
        return response.data;
    } catch (error) {
        throw error.response?.data || error.message;
    }
};

export const validarQR = async (token) => {
    try {
        const response = await http.get(`/api/asistencia/qr/${token}`);
        return response.data;
    } catch (error) {
        throw error.response?.data || error.message;
    }
};