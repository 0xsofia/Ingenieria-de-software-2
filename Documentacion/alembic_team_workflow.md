# Reglas y guardrails mínimos para usar Alembic en equipo

Este documento define un workflow mínimo para trabajar con **Flask + SQLAlchemy + PostgreSQL + Alembic** cuando varias personas del equipo modelan entidades y migraciones en paralelo.

El objetivo es que los cambios de schema sean compartibles, revisables y aplicables sin romper la base de datos local, de desarrollo o de CI.

---

## Principios básicos

### 1. Todo cambio de modelo que afecte la base debe tener migración

Si modificás modelos SQLAlchemy y eso cambia el schema, el PR debe incluir también una migración de Alembic.

Ejemplos de cambios que requieren migración:

- Crear una tabla.
- Agregar, borrar o renombrar columnas.
- Cambiar tipos de datos.
- Agregar índices.
- Agregar constraints.
- Agregar relaciones / foreign keys.
- Cambiar valores `nullable`.
- Crear enums o modificar enums de PostgreSQL.

---

### 2. Una migración por cambio lógico, no necesariamente por entidad

No es obligatorio crear una migración por cada entidad si el cambio pertenece a una misma unidad lógica.

Bien:

```bash
create users table
create products table
add orders and order_items tables
add indexes to users
```

Evitar:

```bash
add user email column
add user name column
add user password column
```

Una migración debería representar un cambio entendible, revisable y reversible.

---

### 3. No editar migraciones ya mergeadas a `dev` o `main`

Una vez que una migración fue mergeada a una rama compartida, no debería editarse.

Si necesitás corregir algo, creá una migración nueva.

Excepción: se puede editar una migración si todavía está únicamente en tu rama local y nadie más la consumió.

---

### 4. Alembic no mergea automáticamente migraciones al hacer Git merge

Cuando dos ramas crean migraciones distintas desde el mismo punto, Alembic puede terminar con múltiples `heads`.

Eso es normal.

Hay que resolverlo con:

```bash
alembic merge heads -m "merge migration heads"
```

---

### 5. Siempre revisar el autogenerate

No confiar ciegamente en:

```bash
alembic revision --autogenerate
```

Alembic puede detectar muchos cambios automáticamente, pero no siempre interpreta correctamente:

- Renombres de columnas.
- Renombres de tablas.
- Cambios de tipo complejos.
- Enums de PostgreSQL.
- Constraints complejas.
- Migraciones con datos existentes.
- Cambios a `nullable=False` en tablas que ya tienen filas.

Toda migración generada debe ser revisada antes de commitearse.

---

## Comandos base

### Ver estado actual de migraciones

```bash
alembic current
```

Muestra en qué revisión está parada tu base local.

---

### Ver la o las últimas revisiones disponibles

```bash
alembic heads
```

Debe haber una sola `head` en condiciones normales.

Si hay más de una, hay ramas de migración paralelas y probablemente haya que hacer un merge de migraciones.

---

### Ver historial de migraciones

```bash
alembic history
```

Muestra el historial completo.

También podés usar:

```bash
alembic history --verbose
```

---

### Aplicar migraciones pendientes

```bash
alembic upgrade head
```

Lleva tu base local hasta la última migración disponible.

---

### Revertir una migración

```bash
alembic downgrade -1
```

Revierte una migración.

Usar con cuidado. No usar en ambientes compartidos sin coordinación.

---

## Workflow: crear una migración nueva

Usar este flujo cuando agregás o modificás modelos SQLAlchemy.

### 1. Actualizar tu rama base

```bash
git checkout dev
git pull origin dev
alembic upgrade head
```

Descripción:

- Te parás en la rama base actualizada.
- Bajás los últimos cambios.
- Aplicás las migraciones pendientes en tu DB local.

---

### 2. Crear tu rama de trabajo

```bash
git checkout -b feature/nombre-del-cambio
```

Ejemplo:

```bash
git checkout -b feature/users-model
```

---

### 3. Modificar los modelos SQLAlchemy

Ejemplo:

```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
```

---

### 4. Crear la migración

```bash
alembic revision --autogenerate -m "create users table"
```

Descripción:

- Alembic compara los modelos SQLAlchemy contra la DB actual.
- Genera un archivo nuevo dentro de `alembic/versions/`.

---

### 5. Revisar el archivo generado

Abrir el archivo generado en:

```bash
alembic/versions/
```

Validar especialmente:

- Que el `upgrade()` haga lo esperado.
- Que el `downgrade()` revierta correctamente.
- Que no haya drops accidentales.
- Que no se pierdan datos.
- Que las constraints tengan sentido.
- Que los índices estén bien definidos.

---

### 6. Aplicar la migración localmente

```bash
alembic upgrade head
```

---

### 7. Probar la app

Ejemplos:

```bash
pytest
```

O levantar la app localmente:

```bash
flask run
```

Si no usás el comando `flask`:

```bash
python -m flask run
```

---

### 8. Committear modelo + migración

```bash
git status
git add -A
git commit -m "Add users model and migration"
```

El commit debe incluir, como mínimo:

- Cambios en modelos SQLAlchemy.
- Archivo de migración en `alembic/versions/`.

---

## Workflow: qué hacer cuando te traés código de `dev`

Usar este flujo cuando estás trabajando en tu rama y querés incorporar cambios nuevos de `dev`.

### 1. Guardar o commitear tus cambios locales

Si tus cambios están listos:

```bash
git add -A
git commit -m "WIP: current model changes"
```

Si no querés commitear todavía:

```bash
git stash
```

---

### 2. Traer los últimos cambios

Opción recomendada con rebase:

```bash
git fetch origin
git rebase origin/dev
```

Alternativa con merge:

```bash
git fetch origin
git merge origin/dev
```

---

### 3. Si usaste stash, recuperar tus cambios

```bash
git stash pop
```

Resolver conflictos si los hubiera.

---

### 4. Aplicar migraciones nuevas de `dev`

```bash
alembic upgrade head
```

---

### 5. Revisar si quedaron múltiples heads

```bash
alembic heads
```

Si aparece una sola head, no hace falta hacer nada más.

Si aparecen dos o más heads, hay migraciones paralelas y hay que mergearlas.

---

## Workflow: mergear migraciones paralelas

Esto pasa cuando tu rama y otra rama crearon migraciones distintas desde el mismo `down_revision`.

### 1. Detectar múltiples heads

```bash
alembic heads
```

Ejemplo de salida conceptual:

```bash
abc123 (head)
def456 (head)
```

---

### 2. Crear migración de merge

```bash
alembic merge heads -m "merge migration heads"
```

Esto crea una nueva migración con más de un `down_revision`.

Ejemplo:

```python
revision = "ghi789"
down_revision = ("abc123", "def456")
```

Esta migración normalmente no tiene operaciones dentro de `upgrade()` ni `downgrade()`. Su función es reconciliar el grafo de migraciones.

---

### 3. Aplicar el resultado

```bash
alembic upgrade head
```

---

### 4. Verificar que quedó una sola head

```bash
alembic heads
```

Debe quedar una sola.

---

### 5. Committear el merge de migraciones

```bash
git add -A
git commit -m "Merge Alembic migration heads"
```

---

## Workflow: qué hacer antes de pushear tu rama

Antes de subir tu rama, correr estos pasos.

### 1. Verificar estado de Git

```bash
git status
```

No debería haber cambios importantes sin commitear.

---

### 2. Actualizar con `dev`

```bash
git fetch origin
git rebase origin/dev
```

Si hay conflictos, resolverlos y continuar:

```bash
git rebase --continue
```

Si necesitás abortar el rebase:

```bash
git rebase --abort
```

---

### 3. Aplicar migraciones

```bash
alembic upgrade head
```

---

### 4. Validar que haya una sola head

```bash
alembic heads
```

Debe mostrar una única head.

Si muestra más de una:

```bash
alembic merge heads -m "merge migration heads"
alembic upgrade head
git add -A
git commit -m "Merge Alembic migration heads"
```

---

### 5. Correr tests

```bash
pytest
```

Si no tienen tests todavía, al menos levantar la app y validar los flujos principales.

---

### 6. Pushear la rama

```bash
git push origin feature/nombre-del-cambio
```

Si hiciste rebase y la rama ya existía en remoto:

```bash
git push --force-with-lease
```

No usar `--force` salvo que haya una razón clara.

---

## Workflow: qué hacer después de mergear un PR a `dev`

Cuando un PR con migraciones fue mergeado a `dev`, el resto del equipo debería hacer:

```bash
git checkout dev
git pull origin dev
alembic upgrade head
```

Si una persona estaba trabajando en otra rama:

```bash
git checkout feature/mi-rama
git fetch origin
git rebase origin/dev
alembic upgrade head
alembic heads
```

Si aparecen múltiples heads:

```bash
alembic merge heads -m "merge migration heads"
alembic upgrade head
git add -A
git commit -m "Merge Alembic migration heads"
```

---

## Guardrails mínimos para PRs

Antes de aprobar o mergear un PR con cambios de base de datos, revisar:

- El PR incluye cambios de modelo y migración.
- La migración no borra tablas o columnas accidentalmente.
- `upgrade()` tiene sentido.
- `downgrade()` tiene sentido o, como mínimo, está conscientemente definido.
- `alembic upgrade head` corre correctamente.
- `alembic heads` muestra una sola head.
- Los tests pasan.
- No se editan migraciones viejas ya mergeadas.
- No se usa `db.create_all()` para ambientes compartidos.

---

## Guardrail recomendado para CI

El pipeline debería validar al menos esto:

```bash
alembic heads
alembic upgrade head
pytest
```

Mejor aún: levantar una PostgreSQL vacía y correr todas las migraciones desde cero.

Ejemplo conceptual:

```bash
createdb test_db
alembic upgrade head
pytest
```

Esto confirma que la DB se puede construir únicamente desde las migraciones.

---

## Casos que requieren revisión manual especial

No confiar en autogenerate para estos casos:

### Renombrar columna

Alembic puede interpretarlo como borrar una columna y crear otra.

Revisar que no haga algo como:

```python
op.drop_column("users", "name")
op.add_column("users", sa.Column("full_name", sa.String()))
```

Eso podría perder datos.

Preferir:

```python
op.alter_column("users", "name", new_column_name="full_name")
```

---

### Agregar columna `nullable=False` en tabla con datos

Esto puede fallar si ya existen filas.

Mal:

```python
op.add_column("users", sa.Column("status", sa.String(), nullable=False))
```

Mejor estrategia:

1. Agregar la columna como nullable o con default.
2. Backfillear datos existentes.
3. Cambiar a `nullable=False`.

Ejemplo:

```python
op.add_column("users", sa.Column("status", sa.String(), nullable=True))
op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
op.alter_column("users", "status", nullable=False)
```

---

### Enums de PostgreSQL

Los enums suelen requerir operaciones específicas.

Revisar cuidadosamente migraciones que creen o modifiquen enums.

---

### Cambios destructivos

Cualquier cambio que haga esto requiere revisión explícita:

```python
op.drop_table(...)
op.drop_column(...)
op.drop_index(...)
```

Puede ser correcto, pero nunca debería pasar desapercibido.

---

## Comandos rápidos de referencia

### Crear migración automática

```bash
alembic revision --autogenerate -m "descripcion del cambio"
```

### Crear migración vacía/manual

```bash
alembic revision -m "descripcion del cambio"
```

### Aplicar todas las migraciones

```bash
alembic upgrade head
```

### Revertir una migración

```bash
alembic downgrade -1
```

### Ver revisión actual de la DB

```bash
alembic current
```

### Ver heads

```bash
alembic heads
```

### Mergear heads

```bash
alembic merge heads -m "merge migration heads"
```

### Ver historial

```bash
alembic history
```

---

## Política mínima sugerida para el equipo

1. Cada PR que modifica modelos debe incluir migración.
2. No se mergean PRs si `alembic upgrade head` falla.
3. No se mergean PRs si `alembic heads` muestra más de una head sin resolver.
4. No se editan migraciones ya mergeadas a `dev`.
5. Las migraciones generadas automáticamente se revisan antes de commitear.
6. Cambios destructivos requieren mención explícita en el PR.
7. La DB local se actualiza con `alembic upgrade head` después de traer cambios de `dev`.
8. Si hay migraciones paralelas, se resuelven con `alembic merge heads`.
9. En ambientes compartidos no se usa `db.create_all()` ni cambios manuales directos de schema.
10. La fuente de verdad del schema son los modelos + migraciones versionadas.
