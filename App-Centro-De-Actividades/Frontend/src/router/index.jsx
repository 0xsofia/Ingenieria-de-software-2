import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import LoginPage from '../pages/LoginPage.jsx'
import CrearClasePage from '../pages/CrearClasePage.jsx'
import RegistrarsePage from '../pages/RegistrarsePage.jsx'
import PerfilPage from '../pages/PerfilPage.jsx'
import ActividadesPage from '../pages/ActividadesPage.jsx'
import ActividadPage from '../pages/ActividadPage.jsx'
import ErrorPage from '../pages/ErrorPage.jsx'


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
    ],
  },
  {
    path:'/crearclase',
    element:<CrearClasePage />,
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
  {
    path: '*',
    element: <ErrorPage />,
  },
])

export default router
