import { createBrowserRouter } from 'react-router-dom'

import App from '../App.jsx'
import InicioPage from '../pages/InicioPage.jsx'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
  },
  {
    path: '/inicio',
    element: <InicioPage />,
  },
])

export default router
