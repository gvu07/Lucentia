export async function getLinkToken() {
  const r = await fetch("http://localhost:8000/link/token/create", { method: "POST" });
  return r.json();
}

export async function exchangePublicToken(public_token) {
  const r = await fetch("http://localhost:8000/plaid/exchange_public_token", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ public_token, user_email: "demo@example.com" })
  });
  return r.json();
}

export async function fetchDiningInsight() {
  const r = await fetch("http://localhost:8000/insights/weekly-dining");
  return r.json();
}
