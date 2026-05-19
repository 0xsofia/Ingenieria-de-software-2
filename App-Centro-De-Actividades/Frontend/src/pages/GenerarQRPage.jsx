import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { Clock, AlertTriangle, Loader2, CheckCircle2, QrCode } from 'lucide-react';
import { generarQR } from '../api/asistencias'; // Tu función http.post

const GenerarQR = () => {
    // 💡 FIX: Capturamos idReserva asegurando que coincida con el nombre en la ruta /reservas/:idReserva/qr
    const { idReserva } = useParams(); 
    
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
                // Invocamos a tu API oficial pasando el ID de la reserva
                const data = await generarQR(idReserva);

                if (data && data.qr_payload) {
                    setPayloadQR(data.qr_payload);
                } else {
                    setErrorMsg("El servidor no retornó un código de acceso válido.");
                }
            } catch (err) {
                // 💡 FIX: Si el backend explota con un 500 (como el del dict), extraemos el error exacto para verlo en pantalla
                const mensajeError = err.response?.data?.message || err.response?.data?.error || "Error al conectar con el módulo de accesos.";
                setErrorMsg(mensajeError);
            } finally {
                setCargando(false);
            }
        };

        cargarCodigoQR();
    }, [idReserva]);

    if (cargando) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh]">
                <Loader2 className="animate-spin text-indigo-600 mb-2" size={40} />
                <p className="text-gray-500 font-medium text-sm">Generando tu pase de acceso...</p>
            </div>
        );
    }

    return (
        <div className="max-w-md mx-auto p-6 mt-10">
            <header className="mb-8 text-center">
                <h1 className="text-3xl font-extrabold text-gray-900">Hola, Socio</h1>
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
                        <p className="text-gray-700 text-sm font-semibold bg-gray-50 py-1.5 px-3 rounded-full inline-block border border-gray-100">
                            Clase: {payloadQR.clase}
                        </p>
                    )}

                    <div className="my-6 flex justify-center">
                        <div className="p-4 bg-white border border-gray-200 rounded-2xl shadow-md">
                            <QRCodeSVG 
                                value={JSON.stringify({
                                    dni: payloadQR?.dni || "",
                                    id_reserva: payloadQR?.id_reserva || idReserva
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