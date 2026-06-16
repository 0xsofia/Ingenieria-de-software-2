import React, { useState, useEffect } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { Clock, AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react';
import { generarQR } from '../api/asistencias';
import { useAuth } from '../hooks/useAuth';

const GenerarQR = () => {
    const { idReserva } = useParams(); 
    const { session } = useAuth();
    
    const [payloadQR, setPayloadQR] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        const cargarCodigoQR = async () => {
            if (!idReserva) {
                setErrorMsg("Código de reserva no especificado en la barra de direcciones.");
                setCargando(false);
                return;
            }

            try {
                // Invocamos a tu API de Flask pasando el ID de la reserva
                const data = await generarQR(idReserva);
                console.log("Respuesta completa del Backend:", data);

                // Verificamos que el backend responda con la estructura esperada
                if (data && data.qr_payload) {
                    setPayloadQR(data.qr_payload);
                } else {
                    setErrorMsg("El servidor no retornó un código de acceso válido.");
                }
            } catch (err) {

                const mensajeError = err.response?.data?.message || err.response?.data?.error || "Error al conectar con el módulo de accesos.";
                setErrorMsg(mensajeError);
            } finally {
                setCargando(false);
            }
        };

        cargarCodigoQR();
    }, [idReserva]);

    if (session?.role !== 'socio') {
        return <Navigate to="/inicio" replace />;
    }

    // 1. Pantalla de Carga
    if (cargando) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh]">
                <Loader2 className="animate-spin text-indigo-600 mb-2" size={40} />
                <p className="text-gray-500 font-medium text-sm">Generando tu pase de acceso...</p>
            </div>
        );
    }

    // 2. Pantalla de Error Personalizada (Evita los códigos rotos en pantalla)
    if (errorMsg) {
        return (
            <div className="max-w-md mx-auto p-6 mt-10">
                <div className="text-center p-8 bg-red-50 rounded-3xl border border-red-100 shadow-xl">
                    <AlertTriangle className="mx-auto text-red-500 mb-3" size={48} />
                    <h3 className="text-lg font-bold text-red-800 mb-2">No se pudo generar el acceso</h3>
                    <p className="text-red-700 text-sm whitespace-pre-line leading-relaxed mb-6">
                        {errorMsg}
                    </p>
                    <button 
                        onClick={() => window.location.reload()}
                        className="bg-gray-800 hover:bg-gray-900 text-white font-semibold py-2.5 px-6 rounded-xl text-sm transition-all"
                    >
                        Volver a intentar
                    </button>
                </div>
            </div>
        );
    }

    // 3. Renderizado Exitoso (Cuando los datos ya están en el estado)
    return (
        <div className="max-w-md mx-auto p-6 mt-10">
            <header className="mb-8 text-center">
                <h1 className="text-3xl font-extrabold text-gray-900">Hola, {payloadQR?.nombre || "Socio"}</h1>
                <p className="text-gray-500 mt-2 text-sm leading-relaxed px-2">
                    Presentá el siguiente código QR en la entrada para registrar tu ingreso.
                </p>
            </header>

            <div className="text-center p-8 bg-white rounded-3xl border border-gray-100 shadow-xl">
                <div className="animate-scale-up">
                    <h2 className="text-lg font-bold text-green-600 flex items-center justify-center gap-1.5 mb-2">
                        <CheckCircle2 size={18}/> Pase Autorizado
                    </h2>
                    
                    {payloadQR?.clase && (
                        <div className="mt-2 mb-4 p-3 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                            <p className="text-gray-800 font-bold text-base mb-1">
                                {payloadQR.clase}
                            </p>
                            <div className="flex items-center justify-center gap-3 text-xs text-gray-500 font-medium">
                                <span>📅 {payloadQR.dia || "Hoy"}</span>
                                <span className="flex items-center gap-1">
                                    <Clock size={12} /> {payloadQR.horario ? `${payloadQR.horario} hs` : "Horario reservado"}
                                </span>
                            </div>
                        </div>
                    )}

                    <div className="my-6 flex justify-center">
                        <div className="p-4 bg-white border border-gray-200 rounded-2xl shadow-md">
                            <QRCodeSVG 
                                value={JSON.stringify({
                                    dni: String(payloadQR.dni).trim(),
                                    id_reserva: Number(payloadQR.id_reserva),
                                    id_clase : Number(payloadQR.id_clase)
                                })}
                                size={220}
                                level="H"
                            />
                        </div>
                    </div>
                    
                    <p className="text-xs text-gray-400 leading-relaxed px-2">
                        Apoyá la pantalla contra el escáner de la recepción.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default GenerarQR;
