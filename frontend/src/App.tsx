import "./App.css";
import AdminTicketsPanel from "./components/AdminTicketsPanel";
import ChatPanel from "./components/ChatPanel";

function App() {
  return (
    <main className="container">
      <h1>SupportOps AI Agent</h1>

      <ChatPanel />

      <AdminTicketsPanel />
    </main>
  );
}

export default App;