import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { default as Chart } from 'react-apexcharts';
import { Loader2, DollarSign, Users, Calendar, TrendingUp, AlertCircle, Award } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { getMetricas } from '../api/metricas'; 

const MetricasPage = () => {
    const { session } = useAuth();
    const [metricasData, setMetricasData] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [errorMsg, setErrorMsg] = useState('');
    
    // Selectores del Administrador
    const [anio, setAnio] = useState(new Date().getFullYear().toString());
    const [mes, setMes] = useState('todos');

    useEffect(() => {
        const cargarMetricas = async () => {
            setCargando(true);
            try {
                const response = await getMetricas(anio, mes); 
                if (response && response.status === "success" && response.data) {
                    setMetricasData(response.data);
                } else if (response && !response.status) {
                    setMetricasData(response);
                }
            } catch (err) {
                setErrorMsg(err.response?.data?.message || "No se pudieron calcular las métricas.");
            } finally {
                setCargando(false);
            }
        };

        if (session?.role === 'administrador') {
            cargarMetricas();
        }
    }, [session, anio, mes]);

    if (session?.role !== 'administrador') {
        return <Navigate to="/inicio" replace />;
    }

    if (cargando) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="animate-spin text-indigo-600 mb-3" size={44} />
                <p className="text-gray-500 font-semibold text-sm">Consultando base de datos...</p>
            </div>
        );
    }

    if (errorMsg) {
        return (
            <div className="max-w-md mx-auto mt-12 p-6 bg-red-50 rounded-2xl border border-red-100 text-center shadow-md">
                <AlertCircle className="mx-auto text-red-500 mb-2" size={40} />
                <h3 className="font-bold text-red-800 text-lg">Error de carga</h3>
                <p className="text-red-700 text-sm mt-1">{errorMsg}</p>
            </div>
        );
    }

    const { 
        asistencias = [], 
        horarios_solicitados = [], 
        ingresos = { total: 0, por_proveedor: [], evolucion: [] }, 
        ocupacion_clases = [] 
    } = metricasData || {};

    // Configuración del Gráfico Dinámico de Ingresos
    const chartPrincipal = {
        series: [{ 
            name: 'Ingresos ($)', 
            data: (ingresos.evolucion || []).map(e => e.monto_pagado) 
        }],
        options: {
            chart: { type: 'bar', toolbar: { show: false } },
            colors: ['#10b981'], 
            plotOptions: { 
                bar: { borderRadius: 5, columnWidth: '65%', dataLabels: { position: 'top' } } 
            },
            dataLabels: {
                enabled: true,
                formatter: (val) => val > 0 ? `$${Math.round(val).toLocaleString('es-AR')}` : '', 
                offsetY: -22,
                style: { fontSize: '9px', colors: ['#374151'], fontWeight: '700' }
            },
            xaxis: { 
                categories: (ingresos.evolucion || []).map(e => e.fecha_label), 
                labels: { style: { colors: '#6b7280', fontSize: '10px', fontWeight: 600 } } 
            },
            yaxis: { labels: { formatter: (val) => `$${Math.round(val).toLocaleString('es-AR')}` } },
            noData: { text: 'Sin ingresos registrados en este rango', style: { color: '#6b7280', fontSize: '14px' } }
        }
    };

    // Configuración del Gráfico de Ocupación por Disciplina
    const chartOcupacion = {
        series: [{ name: '% Ocupación Promedio', data: ocupacion_clases.map(o => o.porcentaje_ocupacion) }],
        options: {
            chart: { type: 'bar', toolbar: { show: false } },
            colors: ['#4f46e5'], 
            plotOptions: { bar: { borderRadius: 6, columnWidth: '40%', dataLabels: { position: 'top' } } },
            dataLabels: {
                enabled: true,
                formatter: (val) => `${val}%`, 
                offsetY: -20,
                style: { fontSize: '11px', colors: ['#374151'], fontWeight: 'bold' }
            },
            xaxis: { 
                categories: ocupacion_clases.map(o => o.clase_label), 
                labels: { style: { fontSize: '11px', colors: '#4b5563', fontWeight: 600 } } 
            },
            yaxis: { max: 100, labels: { formatter: (val) => `${Math.round(val)}%` } },
            noData: { text: 'No hay clases registradas en este periodo', style: { color: '#6b7280', fontSize: '14px' } }
        }
    };

    return (
       <div className="p-6 max-w-7xl mx-auto font-sans bg-gray-50 min-h-screen">
            
            <header className="mb-8 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-gray-800 tracking-tight">Métricas</h1>
                     <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Se mostrará las métricas del período seleccionado</p>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl border border-gray-200 shadow-sm">
                        <label className="text-xs font-black text-gray-400 uppercase">Año:</label>
                        <select 
                            value={anio} 
                            onChange={(e) => setAnio(e.target.value)}
                            className="bg-transparent text-sm font-black text-gray-800 outline-none cursor-pointer"
                        >
                            <option value="2026">2026</option>
                            <option value="2025">2025</option>
                            <option value="2024">2024</option>
                        </select>
                    </div>

                    <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl border border-gray-200 shadow-sm">
                        <label className="text-xs font-black text-gray-400 uppercase">Período:</label>
                        <select 
                            value={mes} 
                            onChange={(e) => setMes(e.target.value)}
                            className="bg-transparent text-sm font-black text-gray-800 outline-none cursor-pointer"
                        >
                            <option value="todos">Año Completo</option>
                            <option value="1">Enero</option>
                            <option value="2">Febrero</option>
                            <option value="3">Marzo</option>
                            <option value="4">Abril</option>
                            <option value="5">Mayo</option>
                            <option value="6">Junio</option>
                            <option value="7">Julio</option>
                            <option value="8">Agosto</option>
                            <option value="9">Septiembre</option>
                            <option value="10">Octubre</option>
                            <option value="11">Noviembre</option>
                            <option value="12">Diciembre</option>
                        </select>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Ingresos Totales</p>
                        <h3 className="text-3xl font-black text-gray-900 mt-1">
                            ${ingresos.total.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                        </h3>
                    </div>
                    <div className="p-4 bg-green-50 text-green-600 rounded-2xl">
                        <DollarSign size={28} />
                    </div>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Asistencias</p>
                        <h3 className="text-3xl font-black text-gray-900 mt-1">
                            {asistencias.reduce((acc, curr) => acc + curr.total_asistencias, 0)} accesos
                        </h3>
                    </div>
                    <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl">
                        <Users size={28} />
                    </div>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Ocupación General</p>
                        <h3 className="text-3xl font-black text-gray-900 mt-1">
                            {ocupacion_clases.length > 0 
                                ? `${roundAvg(ocupacion_clases.reduce((acc, curr) => acc + curr.porcentaje_ocupacion, 0) / ocupacion_clases.length)}%`
                                : '0%'}
                        </h3>
                    </div>
                    <div className="p-4 bg-emerald-50 text-emerald-600 rounded-2xl">
                        <TrendingUp size={28} />
                    </div>
                </div>
            </div>

            {/* Cuadrícula de Gráficos */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Evolución Temporal de Ventas */}
                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl lg:col-span-2">
                    <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <TrendingUp size={18} className="text-emerald-500" /> Historial de Ingresos
                    </h3>
                    <Chart options={chartPrincipal.options} series={chartPrincipal.series} type="bar" height={300} />
                </div>

                {/* Lista de Espera */}
                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl">
                    <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Award size={18} className="text-amber-500" />Horarios más solicitados(personas en lista de espera)
                    </h3>
                    <div className="flex flex-col h-[300px] justify-center">
                        {horarios_solicitados.length === 0 ? (
                            <p className="text-center text-sm text-gray-400 font-medium">No hay registros de socios en lista de espera para este periodo.</p>
                        ) : (
                            <div className="space-y-4 overflow-y-auto pr-1">
                                {horarios_solicitados.map((item, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-2xl border border-gray-100">
                                        <div className="flex items-center gap-3">
                                            <span className={`w-6 h-6 flex items-center justify-center text-xs font-black rounded-full ${
                                                index === 0 ? 'bg-amber-100 text-amber-700' : 'bg-gray-200 text-gray-600'
                                            }`}>
                                                {index + 1}
                                            </span>
                                            <span className="text-xs font-bold text-gray-700 uppercase">{item.label}</span>
                                        </div>
                                        <span className="text-xs font-black bg-amber-50 text-amber-600 px-2.5 py-1 rounded-xl">
                                            {item.cantidad} en espera
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-xl lg:col-span-3">
                    <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Calendar size={18} className="text-indigo-500" /> Ocupación por actividad
                    </h3>
                    <Chart options={chartOcupacion.options} series={chartOcupacion.series} type="bar" height={320} />
                </div>

            </div>
        </div>
    );
};

const roundAvg = (val) => Math.round(val * 10) / 10;

export default MetricasPage;