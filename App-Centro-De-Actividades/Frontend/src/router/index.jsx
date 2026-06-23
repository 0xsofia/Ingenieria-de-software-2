import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import ListadoClasesPage from '../pages/ListadoClasesPage.jsx'
import DetalleClasePage from '../pages/DetalleClasePage.jsx'
import LoginPage from '../pages/LoginPage.jsx'
import RecuperarContrasenaPage from '../pages/RecuperarContrasenaPage.jsx'
import CambiarContrasenaPage from '../pages/CambiarContrasenaPage.jsx'
import PagoRetornoPage from '../pages/PagoRetornoPage.jsx'
import PerfilPage from '../pages/PerfilPage.jsx'
import RegistrarsePage from '../pages/RegistrarsePage.jsx'
import ActividadesPage from '../pages/ActividadesPage.jsx'
import AbonosPage from '../pages/AbonosPage.jsx'
import ActividadPage from '../pages/ActividadPage.jsx'
import RealizarReservaAbonadaPage from '../pages/RealizarReservaAbonadaPage.jsx'
import ActualizarPerfilPage from '../pages/ActualizarPerfilPage.jsx'
import CrearClasePage from '../pages/CrearClasePage.jsx'
import ErrorPage from '../pages/ErrorPage.jsx'
import ListadoUsuariosPage from '../pages/ListadoUsuariosPage.jsx'
import MisPagosPage from '../pages/MisPagosPage.jsx'
import ModificarClasePage from '../pages/ModificarClasePage.jsx'
import ModificarUsuarioPage from '../pages/ModificarUsuarioPage.jsx'
import RegistrarEmpleadoPage from '../pages/RegistrarEmpleadoPage.jsx'
import MisClasesPage from '../pages/MisClasesPage.jsx'
import EscanearQRPage from '../pages/EscanearQRPage.jsx'
import GenerarQRPage from '../pages/GenerarQRPage.jsx'
import CrearProfesorPage from '../pages/CrearProfesorPage.jsx'
import ListadoProfesoresPage from '../pages/ListadoProfesoresPage.jsx'
import ListadoPagosPage from '../pages/ListadoPagosPage.jsx'
import ConfirmarTurnoPage from '../pages/ConfirmarTurnoPage.jsx'
import MetricasPage from '../pages/MetricasPage.jsx'
import RealizarRenovacionAbonoPage from '../pages/RenovarAbonoMensualPage.jsx'


const router = createBrowserRouter([
  {
    path: '/',
    element: <LoginPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/registrarse',
    element: <RegistrarsePage />,
  },
  {
    path: '/recuperar-contrasena',
    element: <RecuperarContrasenaPage />,
  },
  {
    path: '/cambiar-contrasena/:token',
    element: <CambiarContrasenaPage />,
  },
  {
    path: '/confirmar-turno/:token',
    element: <ConfirmarTurnoPage />,
  },
  {
    element: <AuthenticatedLayout />,
    children: [
      {
        path: '/inicio',
        element: <InicioPage />,
      },
      {
        path: '/clases',
        element: <ListadoClasesPage />,
      },
      {
        path: '/clases/:claseId/detalle',
        element: <DetalleClasePage />,
      },
      {
        path: '/clases/crear',
        element: <CrearClasePage />,
      },
      {
        path: '/profesor/crear',
        element: <CrearProfesorPage />,
      },
      {
        path: '/profesores',
        element: <ListadoProfesoresPage />,
      },
      {
        path: '/clases/:claseId/modificar',
        element: <ModificarClasePage />,
      },
      {
        path: '/clases/escanear-qr',
        element: <EscanearQRPage />,
      },
      {
        path: '/reservas/:idReserva/qr',
        element: <GenerarQRPage />,
      },
      {
        path: '/pago/retorno',
        element: <PagoRetornoPage />,
      },
      {
        path: '/usuarios',
        element: <ListadoUsuariosPage />,
      },
      {
        path: '/usuarios/registrar-empleado',
        element: <RegistrarEmpleadoPage />,
      },
      {
        path: '/usuarios/:id/modificar',
        element: <ModificarUsuarioPage />,
      },
      {
        path: '/verperfil',
        element: <PerfilPage />,
      },
      {
        path: '/perfil/actualizar',
        element: <ActualizarPerfilPage />,
      },
      {
        path: '/perfil/cambiar-contrasena',
        element: <CambiarContrasenaPage />,
      },
      {
        path: '/mis-pagos',
        element: <MisPagosPage />,
      },
      {
        path: '/pagos',
        element: <ListadoPagosPage />,
      },
      {
        path: '/mis-clases',
        element: <MisClasesPage />,
      },
      {
        path: '/actividades',
        element: <ActividadesPage />,
      },
      {
        path: '/abonos',
        element: <AbonosPage />,
      },
      {
        path: '/abonos/:actividadName/reservar',
        element: <RealizarReservaAbonadaPage />,
      },
      {
        path: '/actividad/:actividadName',
        element: <ActividadPage />,
      },
      {
        path: '/metricas',
        element: <MetricasPage />,
      },
      {
        path: "/abonos/renovar/:actividadName", 
        element: <RealizarRenovacionAbonoPage />
      }
      
    ],
  },
  {
    path: '*',
    element: <ErrorPage />,
  },
])

export default router
