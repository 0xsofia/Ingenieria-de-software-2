import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import LoginPage from '../pages/LoginPage.jsx'
import PagoRetornoPage from '../pages/PagoRetornoPage.jsx'
import PerfilPage from '../pages/PerfilPage.jsx'


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
    element: <AuthenticatedLayout />,
    children: [
      {
        path: '/inicio',
        element: <InicioPage />,
      },
      {
        path: '/pago/retorno',
        element: <PagoRetornoPage />,
      },
    ],
  },
  {
    path: '/verperfil',
    element: <PerfilPage />,
  }
])

export default router
