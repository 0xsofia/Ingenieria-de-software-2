import { useState } from 'react';
import { registrarAsistencia, validarQR } from '../api/registrar_asistencia.js';
import './RegistrarAsistenciaPage.css';

const RegistrarAsistenciaPage = () => {
    const [token, setToken] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [qrInfo, setQrInfo] = useState(null);

    const handleValidate = async () => {
        if (!token.trim()) {
            setError('Ingrese un token QR');
            return;
        }

        setLoading(true);
        setError('');
        setQrInfo(null);

        try {
            const data = await validarQR(token.trim());
            setQrInfo(data);
            if (!data.valido) {
                setError('Token QR no válido');
            } else {
                setMessage('Token QR válido. Puede registrar asistencia.');
            }
        } catch (err) {
            setError(err.error || 'Error al validar token');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async () => {
        if (!token.trim()) {
            setError('Ingrese un token QR');
            return;
        }

        setLoading(true);
        setError('');
        setMessage('');

        try {
            const data = await registrarAsistencia(token.trim());
            setMessage(data.message);
            setQrInfo(null);
            setToken('');
        } catch (err) {
            setError(err.error || 'Error al registrar asistencia');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="registrar-asistencia-container">
            <h1>Registrar Asistencia</h1>
            <div className="form-group">
                <label htmlFor="token">Token QR:</label>
                <input
                    type="text"
                    id="token"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Ingrese el token del QR"
                    disabled={loading}
                />
            </div>
            <div className="buttons">
                <button onClick={handleValidate} disabled={loading}>
                    {loading ? 'Validando...' : 'Validar QR'}
                </button>
                <button onClick={handleRegister} disabled={loading || !qrInfo?.valido}>
                    {loading ? 'Registrando...' : 'Registrar Asistencia'}
                </button>
            </div>
            {qrInfo && qrInfo.valido && (
                <div className="qr-info">
                    <h3>Información del QR:</h3>
                    <p><strong>Socio:</strong> {qrInfo.socio}</p>
                    <p><strong>Clase:</strong> {qrInfo.clase}</p>
                    <p><strong>Fecha:</strong> {qrInfo.fecha_clase}</p>
                    <p><strong>Hora:</strong> {qrInfo.hora_inicio}</p>
                </div>
            )}
            {message && <div className="success-message">{message}</div>}
            {error && <div className="error-message">{error}</div>}
        </div>
    );
};

export default RegistrarAsistenciaPage;