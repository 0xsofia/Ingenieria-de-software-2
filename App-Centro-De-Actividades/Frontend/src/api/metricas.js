import { http } from './http';
import { endpoints } from '../services/api';

export async function getMetricas(anio = new Date().getFullYear(), mes = 'todos') {
  const { data } = await http.get(`/api/metricas?anio=${anio}&mes=${mes}`);  
  return data; 
}