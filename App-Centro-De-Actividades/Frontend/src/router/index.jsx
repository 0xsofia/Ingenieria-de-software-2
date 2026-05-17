import { createBrowserRouter } from 'react-router-dom'

import AuthenticatedLayout from '../components/AuthenticatedLayout.jsx'
import InicioPage from '../pages/InicioPage.jsx'
import LoginPage from '../pages/LoginPage.jsx' 
import ModificarUsuarioPage from '../pages/ModificarUsuarioPage.jsx'
import RegistrarEmpleadoPage from '../pages/RegistrarEmpleadoPage.jsx'
import CrearClasePage from '../pages/CrearClasePage.jsx'
import ListadoClasesPage from '../pages/ListadoClasesPage.jsx'
import RegistrarsePage from '../pages/RegistrarsePage.jsx'

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
        path: '/registrar-empleado',
        element: <RegistrarEmpleadoPage />,
      },
      {
        path: '/modificar-usuario/:id',
        element: <ModificarUsuarioPage />,
      },
    ],
  },
  {
    path: '/clases',
    element: <ListadoClasesPage />,    
  },
  {
    path:'/crearclase',
    element:<CrearClasePage />,
  },
])

export default router
