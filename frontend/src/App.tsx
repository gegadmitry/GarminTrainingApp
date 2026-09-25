import { useEffect, useState } from "react"

type Sport = "run" | "cycling" | "pool_swim" | "unknown"
type Activity = {
  id: number
  garmin_activity_id: string
  sport: Sport
  start_time_utc: string
  duration_seconds: number
  distance_meters: number | null
  data_quality_status: string
}
type ActivityDetail = Activity & {
  calories: number | null
  average_heart_rate: number | null
  max_heart_rate: number | null
  elevation_gain_meters: number | null
  validation_messages: string
  provenance_source: string | null
  parser_version: string | null
  raw_file_path: string | null
  raw_file_hash: string | null
}

const apiOrigin = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
const sportLabels: Record<Sport, string> = {
  run: "Run",
  cycling: "Cycling",
  pool_swim: "Pool swim",
  unknown: "Unknown",
}

function formatDuration(seconds: number) {
  const minutes = Math.round(seconds / 60)
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, "0")}m`
}

function formatDistance(meters: number | null) {
  return meters === null ? "Unavailable" : `${(meters / 1000).toFixed(2)} km`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
}

function App() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [selected, setSelected] = useState<ActivityDetail | null>(null)
  const [sport, setSport] = useState("")
  const [start, setStart] = useState("")
  const [end, setEnd] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    const params = new URLSearchParams()
    if (sport) params.set("sport", sport)
    if (start) params.set("start", `${start}T00:00:00Z`)
    if (end) params.set("end", `${end}T23:59:59Z`)
    setLoading(true)
    setError(null)
    fetch(`${apiOrigin}/activities?${params}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("The local API could not load activities.")
        return response.json() as Promise<Activity[]>
      })
      .then(setActivities)
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") setError(requestError.message)
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [sport, start, end])

  async function openDetail(activity: Activity) {
    setError(null)
    try {
      const response = await fetch(`${apiOrigin}/activities/${activity.id}`)
      if (!response.ok) throw new Error("Activity details are unavailable.")
      setSelected(await response.json() as ActivityDetail)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Activity details are unavailable.")
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">FN</span><span>Field Notes</span></div>
        <span className="local-badge"><i /> Local archive</span>
      </header>
      <section className="hero">
        <p className="eyebrow">Training archive / 01</p>
        <h1>Activities</h1>
        <p className="lede">A clear view of the work you have put in, with the raw record always close by.</p>
      </section>
      <section className="workspace" aria-label="Activity browser">
        <aside className="filters">
          <div className="section-label">Refine archive</div>
          <label>Sport<select value={sport} onChange={(event) => setSport(event.target.value)}><option value="">All sports</option>{Object.entries(sportLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>From<input type="date" value={start} onChange={(event) => setStart(event.target.value)} /></label>
          <label>To<input type="date" value={end} onChange={(event) => setEnd(event.target.value)} /></label>
          <button className="clear-button" onClick={() => { setSport(""); setStart(""); setEnd("") }}>Clear filters</button>
          <div className="filter-note"><span className="dot" /> Showing local Garmin records only</div>
        </aside>
        <section className="results">
          <div className="results-heading"><div><div className="section-label">Recent movement</div><h2>{loading ? "Loading archive" : `${activities.length} activities`}</h2></div><span className="range-label">Last year</span></div>
          {error && <div className="state error-state"><strong>Could not connect</strong><span>{error}</span></div>}
          {loading && <div className="state"><span className="spinner" /> Fetching local activities...</div>}
          {!loading && !error && activities.length === 0 && <div className="state empty-state"><strong>No activities found</strong><span>Try widening the date range or removing a sport filter.</span></div>}
          {!loading && !error && activities.length > 0 && <div className="activity-list">{activities.map((activity) => <button className="activity-row" key={activity.id} onClick={() => openDetail(activity)}><span className={`sport-icon ${activity.sport}`}>{activity.sport === "cycling" ? "↗" : activity.sport === "pool_swim" ? "≈" : activity.sport === "run" ? "◒" : "•"}</span><span className="activity-main"><strong>{sportLabels[activity.sport]}</strong><small>{formatDate(activity.start_time_utc)}</small></span><span className="activity-stat"><small>Distance</small><strong>{formatDistance(activity.distance_meters)}</strong></span><span className="activity-stat"><small>Duration</small><strong>{formatDuration(activity.duration_seconds)}</strong></span><span className={`quality ${activity.data_quality_status}`}>{activity.data_quality_status}</span><span className="row-arrow">→</span></button>)}</div>}
        </section>
      </section>
      {selected && <div className="drawer-backdrop" onClick={() => setSelected(null)}><aside className="detail-drawer" onClick={(event) => event.stopPropagation()}><button className="close-button" aria-label="Close activity details" onClick={() => setSelected(null)}>×</button><p className="eyebrow">Activity detail</p><h2>{sportLabels[selected.sport]}</h2><p className="detail-date">{formatDate(selected.start_time_utc)}</p><div className="detail-metrics"><div><small>Distance</small><strong>{formatDistance(selected.distance_meters)}</strong></div><div><small>Duration</small><strong>{formatDuration(selected.duration_seconds)}</strong></div><div><small>Calories</small><strong>{selected.calories === null ? "Unavailable" : `${Math.round(selected.calories)} kcal`}</strong></div><div><small>Avg heart rate</small><strong>{selected.average_heart_rate === null ? "Unavailable" : `${selected.average_heart_rate} bpm`}</strong></div></div><div className="detail-section"><div className="section-label">Data quality</div><p><span className={`quality ${selected.data_quality_status}`}>{selected.data_quality_status}</span></p><p className="muted">{selected.validation_messages || "No validation messages recorded."}</p></div><div className="detail-section"><div className="section-label">Raw provenance</div><dl><dt>Source</dt><dd>{selected.provenance_source ?? "Unavailable"}</dd><dt>Parser</dt><dd>{selected.parser_version ?? "Unavailable"}</dd><dt>File</dt><dd>{selected.raw_file_path ?? "Unavailable"}</dd><dt>Hash</dt><dd>{selected.raw_file_hash ?? "Unavailable"}</dd></dl></div></aside></div>}
    </main>
  )
}

export default App