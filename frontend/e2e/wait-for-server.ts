export default async function waitForServer() {
  const base = process.env.E2E_URL || 'http://127.0.0.1:8011';
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    try { if ((await fetch(`${base}/api/health`)).ok) return; } catch { /* Starting */ }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error('Start the isolated E2E server on port 8011 before browser tests');
}
