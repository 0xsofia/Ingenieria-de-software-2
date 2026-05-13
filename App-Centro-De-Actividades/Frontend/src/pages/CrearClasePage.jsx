import { useMemo, useState } from "react"
import { crearClase } from "../api/clase"

const profesores = [
  { id: 1, nombre: "Carlos" },
  { id: 2, nombre: "Juan" }
]

const actividades = [
  "Voley",
  "Futbol",
  "Tenis"
]

const niveles = [
  "Principiante",
  "Intermedio",
  "Experto"
]


export default function CrearClasePage() {
  const today = new Date()
  .toISOString()
  .split("T")[0]

  const horarios = [
  "08:00",
  "09:00",
  "10:00",
  "11:00",
  "12:00",
  "13:00",
  "14:00",
  "15:00",
  "16:00",
  "17:00",
  "18:00",
  "19:00",
  "20:00"
]
  const [formData, setFormData] = useState({
    profesor_id: "",
    fecha: "",
    horario_inicio: "",
    actividad: "",
    nivel: "",
    cancha: "",
    cupos: 1
  })

  const [mensaje, setMensaje] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const tipoClase = useMemo(() => {

    return Number(formData.cupos) === 1
      ? "Particular"
      : "Grupal"

  }, [formData.cupos])

  function handleChange(e) {

    const { name, value } = e.target

    setFormData({
      ...formData,
      [name]: value
    })
  }

  async function handleSubmit(e) {

    e.preventDefault()

    setMensaje("")
    setError("")
    setLoading(true)

    try {

      const response = await crearClase({
            ...formData,
            profesor_id: Number(formData.profesor_id),
            cupos: Number(formData.cupos)
          })  

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error)
      }

      setMensaje(
        "La clase fue registrada correctamente"
      )

      setFormData({
        profesor_id: "",
        fecha: "",
        horario_inicio: "",
        actividad: "",
        nivel: "",
        cancha: "",
        cupos: 1
      })

    } catch (err) {

      setError(err.message)

    } finally {

      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>

      <h1>Crear Clase</h1>

      <form
        onSubmit={handleSubmit}
        style={styles.form}
      >

        <div style={styles.field}>
          <label>Profesor</label>

          <select
            name="profesor_id"
            value={formData.profesor_id}
            onChange={handleChange}
            required
          >
            <option value="">
              Seleccionar profesor
            </option>

            {profesores.map((profesor) => (
              <option
                key={profesor.id}
                value={profesor.id}
              >
                {profesor.nombre}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.field}>
          <label>Fecha</label>

          <input
            type="date"
            name="fecha"
            value={formData.fecha}
            onChange={handleChange}
            required
            min={today}
          />
        </div>

        <div style={styles.field}>
          <label>Horario Inicio</label>

          <select
            name="horario_inicio"
            value={formData.horario_inicio}
            onChange={handleChange}
            required
            >
            <option value="">
                Seleccionar horario
            </option>

            {horarios.map((horario) => (
                <option
                key={horario}
                value={horario}
                >
                {horario}
                </option>
            ))}
            </select>
        </div>

        <div style={styles.field}>
          <label>Actividad</label>

          <select
            name="actividad"
            value={formData.actividad}
            onChange={handleChange}
            required
          >
            <option value="">
              Seleccionar actividad
            </option>

            {actividades.map((actividad) => (
              <option
                key={actividad}
                value={actividad}
              >
                {actividad}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.field}>
          <label>Nivel</label>

          <select
            name="nivel"
            value={formData.nivel}
            onChange={handleChange}
            required
          >
            <option value="">
              Seleccionar nivel
            </option>

            {niveles.map((nivel) => (
              <option
                key={nivel}
                value={nivel}
              >
                {nivel}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.field}>
        <label>Cancha</label>

        <input
            type="text"
            name="cancha"
            value={formData.cancha}
            onChange={handleChange}
            placeholder="Ingrese la cancha"
            required
        />
        </div>

        <div style={styles.field}>
          <label>Cupos</label>

          <input
            type="number"
            name="cupos"
            min="1"
            value={formData.cupos}
            onChange={handleChange}
            required
          />
        </div>

        <div style={styles.tipoClase}>
          <strong>Tipo de clase:</strong>
          {" "}
          {tipoClase}
        </div>

        <button
          type="submit"
          disabled={loading}
        >
          {
            loading
              ? "Creando..."
              : "Crear clase"
          }
        </button>

      </form>

      {mensaje && (
        <div style={styles.success}>
          {mensaje}
        </div>
      )}

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

    </div>
  )
}

const styles = {

  container: {
    maxWidth: "500px",
    margin: "40px auto",
    padding: "24px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontFamily: "Arial"
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px"
  },

  field: {
    display: "flex",
    flexDirection: "column",
    gap: "6px"
  },

  tipoClase: {
    padding: "12px",
    backgroundColor: "#f4f4f4",
    borderRadius: "6px"
  },

  success: {
    marginTop: "16px",
    color: "green"
  },

  error: {
    marginTop: "16px",
    color: "red"
  }
}