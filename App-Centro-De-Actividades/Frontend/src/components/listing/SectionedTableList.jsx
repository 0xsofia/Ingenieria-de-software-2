import './SectionedTableList.css'

export default function SectionedTableList({
  sections,
  columns,
  getRowKey,
  emptyMessage,
  renderActions,
}) {
  const totalItems = sections.reduce((count, section) => count + section.items.length, 0)

  if (totalItems === 0) {
    return <div className="sectioned-table-list__empty">{emptyMessage}</div>
  }

  return (
    <div className="sectioned-table-list">
      {sections.map((section) => (
        <section key={section.key} className="sectioned-table-list__section">
          <div className="sectioned-table-list__header">
            <h3>{section.title}</h3>
            <p className="dashboard-copy">{section.items.length} resultado(s)</p>
          </div>

          {section.items.length === 0 ? (
            <div className="sectioned-table-list__section-empty">
              {section.emptyMessage || 'No hay elementos para mostrar en esta sección.'}
            </div>
          ) : (
            <div className="sectioned-table-list__table-wrapper">
              <table className="sectioned-table-list__table">
                <thead>
                  <tr>
                    {columns.map((column) => (
                      <th key={column.key} scope="col">
                        {column.header}
                      </th>
                    ))}
                    {renderActions ? <th scope="col">Acciones</th> : null}
                  </tr>
                </thead>

                <tbody>
                  {section.items.map((item) => (
                    <tr key={getRowKey(item, section.key)}>
                      {columns.map((column) => (
                        <td key={column.key} data-label={column.header}>
                          {column.render ? column.render(item) : item[column.key]}
                        </td>
                      ))}
                      {renderActions ? (
                        <td data-label="Acciones">{renderActions(item, section.key)}</td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ))}
    </div>
  )
}
