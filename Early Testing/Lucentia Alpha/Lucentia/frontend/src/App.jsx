import React from "react";
import { useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import { getLinkToken, exchangePublicToken, fetchDiningInsight } from "./api";

function ConnectButton({ onSuccess }) {
  const [linkToken, setLinkToken] = useState(null);

  useEffect(() => {
    (async () => {
      const { link_token } = await getLinkToken();
      setLinkToken(link_token);
    })();
  }, []);

  const config = {
    token: linkToken,
    onSuccess: async (public_token) => {
      await exchangePublicToken(public_token);
      onSuccess();
    },
  };

  const { open, ready } = usePlaidLink(config);

  return (
    <button disabled={!ready} onClick={() => open()}>
      Connect bank
    </button>
  );
}

export default function App() {
  const [insight, setInsight] = useState(null);

  const refresh = async () => {
    const data = await fetchDiningInsight();
    setInsight(data);
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Lucentia</h1>
      <ConnectButton onSuccess={refresh} />
      <button onClick={refresh} style={{ marginLeft: 12 }}>Refresh insight</button>
      <div style={{ marginTop: 24 }}>
        {insight?.pct_change == null ? (
          <p>No baseline yet. Connect and refresh.</p>
        ) : (
          <p>
            You’re spending {Math.abs(insight.pct_change).toFixed(0)}%
            {insight.pct_change >= 0 ? " more " : " less "}
            on dining this week than your average.
          </p>
        )}
      </div>
    </div>
  );
}
