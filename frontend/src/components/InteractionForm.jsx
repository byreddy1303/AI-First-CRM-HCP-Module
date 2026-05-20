import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { createInteraction } from "../redux/interactionsSlice";

const initialForm = {
  hcp_name: "",
  interaction_type: "meeting",
  date: new Date().toISOString().slice(0, 10),
  time: "",
  attendees: "",
  topics: "",
  materials_shared: "",
  samples_distributed: "",
  sentiment: "neutral",
  outcome: "",
  follow_up_actions: "",
};

export default function InteractionForm() {
  const dispatch = useDispatch();
  const { loading, current, error } = useSelector((state) => state.interactions);
  const { hcpList } = useSelector((state) => state.hcp);
  const [form, setForm] = useState(initialForm);

  // Reset form after a successful save (current.id changes to a new value)
  useEffect(() => {
    if (current?.id) {
      setForm({ ...initialForm, date: new Date().toISOString().slice(0, 10) });
    }
  }, [current?.id]);

  const updateField = (field, value) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = (event) => {
    event.preventDefault();
    dispatch(createInteraction(toPayload(form)));
  };

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-header">
        <div>
          <p className="eyebrow">Structured Entry</p>
          <h2>Log Interaction</h2>
        </div>
        <button className="icon-button primary" type="submit" disabled={loading} title="Save interaction">
          <Save size={18} />
          <span>{loading ? "Saving…" : "Save"}</span>
        </button>
      </div>

      <div className="form-grid">
        <label>
          HCP Name
          <input
            list="hcp-suggestions"
            value={form.hcp_name}
            onChange={(e) => updateField("hcp_name", e.target.value)}
            placeholder="Dr. Smith"
            required
          />
          <datalist id="hcp-suggestions">
            {hcpList.map((hcp) => (
              <option key={hcp.id} value={hcp.name} />
            ))}
          </datalist>
        </label>
        <label>
          Interaction Type
          <select value={form.interaction_type} onChange={(e) => updateField("interaction_type", e.target.value)}>
            <option value="meeting">Meeting</option>
            <option value="call">Call</option>
            <option value="email">Email</option>
            <option value="conference">Conference</option>
          </select>
        </label>
        <label>
          Date
          <input type="date" value={form.date} onChange={(e) => updateField("date", e.target.value)} />
        </label>
        <label>
          Time
          <input type="time" value={form.time} onChange={(e) => updateField("time", e.target.value)} />
        </label>
      </div>

      <label>
        Attendees <span className="field-hint">(comma-separated)</span>
        <input
          value={form.attendees}
          onChange={(e) => updateField("attendees", e.target.value)}
          placeholder="e.g. Rep A, Rep B"
        />
      </label>
      <label>
        Topics Discussed <span className="field-hint">(comma-separated)</span>
        <textarea
          value={form.topics}
          onChange={(e) => updateField("topics", e.target.value)}
          rows={3}
          placeholder="e.g. Product X efficacy, side effects"
        />
      </label>
      <div className="form-grid">
        <label>
          Materials Shared
          <input
            value={form.materials_shared}
            onChange={(e) => updateField("materials_shared", e.target.value)}
            placeholder="e.g. brochure, study"
          />
        </label>
        <label>
          Samples Distributed
          <input
            value={form.samples_distributed}
            onChange={(e) => updateField("samples_distributed", e.target.value)}
            placeholder="e.g. 2 sample kits"
          />
        </label>
      </div>
      <label>
        Sentiment
        <select value={form.sentiment} onChange={(e) => updateField("sentiment", e.target.value)}>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
      </label>
      <label>
        Outcomes
        <textarea
          value={form.outcome}
          onChange={(e) => updateField("outcome", e.target.value)}
          rows={3}
          placeholder="Key results from this interaction"
        />
      </label>
      <label>
        Follow-up Actions
        <textarea
          value={form.follow_up_actions}
          onChange={(e) => updateField("follow_up_actions", e.target.value)}
          rows={3}
          placeholder="e.g. Send brochure, schedule call next week"
        />
      </label>

      {current && (
        <p className="success-line">
          Saved interaction #{current.id} for {current.hcp_name}
        </p>
      )}
      {error && <p className="error-line">{error}</p>}
    </form>
  );
}

function toPayload(form) {
  return {
    ...form,
    attendees: splitList(form.attendees),
    topics: splitList(form.topics),
    materials_shared: splitList(form.materials_shared),
    samples_distributed: splitList(form.samples_distributed),
    follow_up_actions: splitList(form.follow_up_actions),
    time: form.time || null,
  };
}

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
