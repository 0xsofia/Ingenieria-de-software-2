import { Link, isRouteErrorResponse, useRouteError } from 'react-router-dom'

function ErrorPage() {
  const error = useRouteError()

  if (isRouteErrorResponse(error)) {
    return (
      <main className="dashboard-shell profile-shell">
        <section className="dashboard-frame profile-frame">
          <header className="dashboard-header profile-header">
            <h1>{error.status} {error.statusText || 'Error'}</h1>
          </header>
          <div>
            <p>No se encontró la página solicitada.</p>
            <p>
              Volvé a <Link to="/">Inicio</Link> o revisá que la dirección esté bien escrita.
            </p>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Ocurrió un error inesperado</h1>
        </header>
        <div>
          <p>{error?.message || 'Algo salió mal al cargar la página.'}</p>
          <p>
            Volvé a <Link to="/">Inicio</Link> o intentá nuevamente.
          </p>
        </div>
      </section>
    </main>
  )
}

export default ErrorPage
