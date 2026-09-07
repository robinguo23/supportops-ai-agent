import { useEffect, useState } from "react";

import { API_BASE_URL } from "../config/api";


type SecuritySummary = {
  window_hours: number;
  allowed: number;
  blocked: number;
  total: number;
  block_rate: number;
  generated_at: string;
};

type WafRule = {
  name: string;
  priority: number;
  action: string;
  statement_type: string;
};

type WafEvent = {
  timestamp: string;
  source_ip: string;
  method: string;
  uri: string;
  action: string;
  rule: string;
  country: string;
};


function formatNumber(value: number) {
  return new Intl.NumberFormat("en-GB").format(value);
}


export default function SecurityDashboard() {
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [rules, setRules] = useState<WafRule[]>([]);
  const [events, setEvents] = useState<WafEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadSecurityData() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const [summaryResponse, rulesResponse, eventsResponse] =
        await Promise.all([
          fetch(`${API_BASE_URL}/security-api/summary`),
          fetch(`${API_BASE_URL}/security-api/rules`),
          fetch(`${API_BASE_URL}/security-api/events?limit=20`),
        ]);

      const responses = [summaryResponse, rulesResponse, eventsResponse];
      const deniedResponse = responses.find(
        (response) => response.status === 403
      );

      if (deniedResponse) {
        throw new Error("ACCESS_DENIED");
      }

      if (responses.some((response) => !response.ok)) {
        throw new Error("UNAVAILABLE");
      }

      const [summaryData, rulesData, eventsData] = await Promise.all([
        summaryResponse.json() as Promise<SecuritySummary>,
        rulesResponse.json() as Promise<{ rules: WafRule[] }>,
        eventsResponse.json() as Promise<{ events: WafEvent[] }>,
      ]);

      setSummary(summaryData);
      setRules(rulesData.rules);
      setEvents(eventsData.events);
    } catch (error) {
      setSummary(null);
      setRules([]);
      setEvents([]);

      setErrorMessage(
        error instanceof Error && error.message === "ACCESS_DENIED"
          ? "Security data is restricted to a trusted administrator IP."
          : "Security data is unavailable until the AWS deployment is configured."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadSecurityData();
  }, []);

  return (
    <section className="security-panel">
      <div className="security-header">
        <div>
          <h2>Application Security</h2>
          <div className="security-subtitle">
            AWS WAF activity during the last 24 hours
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadSecurityData()}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {errorMessage && (
        <div className="security-access-note">{errorMessage}</div>
      )}

      {summary && (
        <>
          <div className="security-cards">
            <div className="security-card">
              <div className="security-card-label">Requests</div>
              <div className="security-card-value">
                {formatNumber(summary.total)}
              </div>
            </div>

            <div className="security-card">
              <div className="security-card-label">Allowed</div>
              <div className="security-card-value">
                {formatNumber(summary.allowed)}
              </div>
            </div>

            <div className="security-card blocked">
              <div className="security-card-label">Blocked</div>
              <div className="security-card-value">
                {formatNumber(summary.blocked)}
              </div>
            </div>

            <div className="security-card">
              <div className="security-card-label">Block rate</div>
              <div className="security-card-value">
                {summary.block_rate.toFixed(2)}%
              </div>
            </div>
          </div>

          <div className="security-timestamp">
            Updated {new Date(summary.generated_at).toLocaleString()}
          </div>
        </>
      )}

      <div className="security-section">
        <div className="security-section-header">
          <h3>Deployed WAF rules</h3>
          <span>{rules.length} rules</span>
        </div>

        <table className="security-table">
          <thead>
            <tr>
              <th>Priority</th>
              <th>Rule</th>
              <th>Type</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.name}>
                <td>
                  <span className="priority-badge">{rule.priority}</span>
                </td>
                <td>{rule.name}</td>
                <td>{rule.statement_type}</td>
                <td>{rule.action}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!isLoading && rules.length === 0 && (
          <div className="empty-state">No rule data available.</div>
        )}
      </div>

      <div className="security-section">
        <div className="security-section-header">
          <h3>Recent blocked requests</h3>
          <span>{events.length} events</span>
        </div>

        <table className="security-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Source</th>
              <th>Country</th>
              <th>Request</th>
              <th>Rule</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, index) => (
              <tr key={`${event.timestamp}-${event.source_ip}-${index}`}>
                <td>{new Date(event.timestamp).toLocaleString()}</td>
                <td>{event.source_ip}</td>
                <td>{event.country}</td>
                <td>
                  {event.method} {event.uri}
                </td>
                <td>{event.rule}</td>
                <td>
                  <span className="action-badge">{event.action}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!isLoading && events.length === 0 && (
          <div className="empty-state">No blocked events available.</div>
        )}
      </div>
    </section>
  );
}
