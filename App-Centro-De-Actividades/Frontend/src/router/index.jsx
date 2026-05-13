import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import LoginPage from '../pages/LoginPage.jsx'
import RegistrarsePage from '../pages/RegistrarsePage.jsx'
import PerfilPage from '../pages/PerfilPage.jsx'
import MisPagosPage from '../pages/MisPagosPage.jsx'
import PagosClientesPage from '../pages/PagosClientesPage.jsx'


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
    path: '/verperfil',
    element: <PerfilPage />,
  },
  {
    path: '/mispagos',
    element: <MisPagosPage />,
  },
  {
    path: '/pagosclientes',
    element: <PagosClientesPage />,
  }
])

export default router
