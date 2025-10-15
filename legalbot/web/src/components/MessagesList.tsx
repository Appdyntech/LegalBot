// web/src/components/MessagesList.tsx
import React from "react";

type Source = {
  source: string;
  snippet: string;
  metadata?: any;
};

export default function MessagesList({ answer, sources }: { answer?: string; sources?: Source[] }) {
  return (
    <div>
      {answer && (
        <div className="message">
          <div style={{ fontWeight: 600 }}>Answer</div>
          <div style={{ marginTop: 8 }}>{answer}</div>
        </div>
      )}
      {sources && sources.length > 0 && (
        <div>
          <h4>Sources</h4>
          {sources.map((s, idx) => (
            <div key={idx} className="message" style={{ background: "#fffefb" }}>
              <div className="small">{s.source}</div>
              <div style={{ marginTop: 6 }}>{s.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
