import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import ListadoClasesPage from '../pages/ListadoClasesPage.jsx'
import LoginPage from '../pages/LoginPage.jsx'
import PagoRetornoPage from '../pages/PagoRetornoPage.jsx'
import PerfilPage from '../pages/PerfilPage.jsx'
import RegistrarsePage from '../pages/RegistrarsePage.jsx'
import ActividadesPage from '../pages/ActividadesPage.jsx'
import ActividadPage from '../pages/ActividadPage.jsx'
import CrearClasePage from '../pages/CrearClasePage.jsx'
import ErrorPage from '../pages/ErrorPage.jsx'
import ListadoUsuariosPage from '../pages/ListadoUsuariosPage.jsx'
import ModificarClasePage from '../pages/ModificarClasePage.jsx'
import ModificarUsuarioPage from '../pages/ModificarUsuarioPage.jsx'
import RegistrarEmpleadoPage from '../pages/RegistrarEmpleadoPage.jsx'
import EscanearQRPage from '../pages/EscanearQRPage.jsx'
import GenerarQRPage from '../pages/GenerarQRPage.jsx'


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
        path: '/clases/crear',
        element: <CrearClasePage />,
      },
      {
        path: '/clases/:claseId/modificar',
        element: <ModificarClasePage />,
      },
      {
        path: '/clases/:claseId/qr',
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
        path: '/actividades',
        element: <ActividadesPage />,
      },
      {
        path: '/actividad/:actividadName',
        element: <ActividadPage />,
      },
    ],
  },
  {
    path: '*',
    element: <ErrorPage />,
  },
])

export default router
