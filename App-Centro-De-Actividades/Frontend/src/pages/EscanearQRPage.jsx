import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom'; 
import { Html5Qrcode } from "html5-qrcode"; 
import { AlertTriangle, Loader2, CheckCircle2, RefreshCw } from 'lucide-react';
import { escanearQR } from '../api/asistencias'; 
import './EscanearQRPage.css';

const EscanearQR = () => {
    const [resultadoEscaneo, setResultadoEscaneo] = useState(null);
    const [errorLog, setErrorLog] = useState(null);
    const [cargando, setCargando] = useState(false);
    const { idClase } = useParams(); 
    const html5QrCodeRef = useRef(null);
    
    useEffect(() => {
        const timer = setTimeout(() => {
            iniciarCamaraDirecta();
        }, 200);

        return () => {
            clearTimeout(timer);
            apagarCamaraSeguro();
        };
    }, []);

    const apagarCamaraSeguro = async () => {
        if (html5QrCodeRef.current && html5QrCodeRef.current.isScanning) {
            try {
                await html5QrCodeRef.current.stop();
            } catch (err) {
                console.warn("Error al apagar la cámara:", err);
            }
        }
        html5QrCodeRef.current = null;
    };

    const iniciarCamaraDirecta = async () => {
        setResultadoEscaneo(null);
        setErrorLog(null);
        setCargando(false);

        await apagarCamaraSeguro();

        try {
            // Creamos la instancia apuntando al div
            const html5QrCode = new Html5Qrcode("reader-asistencia");
            html5QrCodeRef.current = html5QrCode;

            // Configuración del escáner
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 }
            };

            // { facingMode: "environment" } fuerza la cámara de atrás en celulares, o la webcam default en PC
            await html5QrCode.start(
                { facingMode: "environment" },
                config,
                onScanSuccess,
                onScanFailure
            );

        } catch (err) {
            console.error("Error al encender la cámara con Html5Qrcode:", err);
            setErrorLog("No se pudo acceder a la cámara web. Asegúrate de que no esté siendo usada por otra aplicación (Zoom, Teams, etc.) y que diste los permisos correctamente.");
        }
    };

    const onScanSuccess = async (decodedText) => {
        // Apagamos la cámara inmediatamente para evitar lecturas dobles consecutivas
        await apagarCamaraSeguro();
        setCargando(true);

        try {
            let payload;
            try {
                payload = JSON.parse(decodedText);
            } catch (err) {
                throw new Error("Formato del QR inválido. El código escaneado no pertenece al sistema del gimnasio.");
            }

            if (!payload.dni || !payload.id_reserva) {
                throw new Error("El QR no contiene los datos obligatorios del cliente (DNI o Reserva).");
            }

            // Llamamos a tu servicio asíncrono
            const data = await escanearQR(payload, idClase);
            setResultadoEscaneo(data.message || "Asistencia registrada con éxito.");

        } catch (err) {
                if (err.response && err.response.data) {
                    // Captura el string si el backend lo envía en .message o en .error
                    const mensajeError = err.response.data.message || err.response.data.error;
                    
                    if (mensajeError) {
                        setErrorLog(mensajeError);
                    } else if (typeof err.response.data === 'string' && !err.response.data.includes('<!DOCTYPE html>')) {
                        setErrorLog(err.response.data);
                    } else {
                        setErrorLog(`Error de comunicación (${err.response.status}): Controlá que las rutas coincidan.`);
                    }
            } else {
                setErrorLog(err.message || "No se pudo conectar con el servidor central.");
            }
        } finally {
            setCargando(false);
        }
    };

    const onScanFailure = (error) => {
        // Omisión de ruidos de lectura
    };

    return (
        <div className="max-w-md mx-auto p-6 bg-white rounded-3xl border border-gray-100 shadow-xl mt-8 font-sans">
            <h2 className="text-xl font-extrabold text-gray-800 text-center mb-1">Escanear QR de Asistencia</h2>
            <p className="text-xs text-gray-400 text-center mb-6">Panel para el empleado de recepción</p>

            {!resultadoEscaneo && !errorLog && !cargando && (
                // 👈 Un contenedor con tamaño fijo inicial para que no se rompa el diseño mientras enciende
                <div 
                    id="reader-asistencia" 
                    className="overflow-hidden rounded-2xl bg-gray-50 border-2 border-dashed border-gray-200"
                    style={{ width: '100%', minHeight: '300px' }}
                ></div>
            )}

            {cargando && (
                <div className="flex flex-col items-center justify-center py-12">
                    <RefreshCw className="animate-spin text-indigo-600 mb-3" size={32} />
                    <p className="text-gray-500 font-medium text-sm">Validando registro en la base de datos...</p>
                </div>
            )}

            {/* Escenario 1: Ingreso Autorizado */}
            {resultadoEscaneo && (
                <div className="text-center py-6 bg-green-50 rounded-2xl p-4 border border-green-200">
                    <CheckCircle2 className="mx-auto text-green-600 mb-3" size={48} />
                    <h3 className="text-lg font-bold text-green-800">¡Ingreso Autorizado!</h3>
                    <p className="text-green-700 text-sm mt-2">{resultadoEscaneo}</p>
                    <button 
                        onClick={iniciarCamaraDirecta}
                        className="mt-6 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-xl text-sm transition-all shadow-md shadow-green-100"
                    >
                        Escanear Siguiente
                    </button>
                </div>
            )}

            {/* Escenarios de Fallo */}
            {errorLog && (
                <div className="text-center py-6 bg-red-50 rounded-2xl p-4 border border-red-200">
                    <AlertTriangle className="mx-auto text-red-500 mb-3" size={48} />
                    <h3 className="text-lg font-bold text-red-800">Acceso Denegado</h3>
                    <p className="text-red-700 text-sm mt-2">{errorLog}</p>
                    <button 
                        onClick={iniciarCamaraDirecta}
                        className="mt-6 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-6 rounded-xl text-sm transition-all shadow-md shadow-red-100"
                    >
                        Reintentar Escaneo
                    </button>
                </div>
            )}
        </div>
    );
};

export default EscanearQR;