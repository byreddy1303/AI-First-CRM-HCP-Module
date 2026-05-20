import ChatPanel from "../components/ChatPanel";
import InteractionForm from "../components/InteractionForm";

export default function LogInteractionPage() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI-First CRM HCP Module</p>
          <h1>HCP Interaction Workspace</h1>
        </div>
      </header>
      <section className="workspace-grid">
        <InteractionForm />
        <ChatPanel />
      </section>
    </main>
  );
}

