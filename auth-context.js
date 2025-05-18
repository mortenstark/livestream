const { chromium } = require('playwright');
const fs = require('fs');

async function createAuthContext() {
  const browser = await chromium.launch({
    headless: false,
    args: [
      '--use-fake-ui-for-media-stream',
      '--autoplay-policy=no-user-gesture-required',
    ]
  });

  const context = await browser.newContext({
    permissions: ['microphone'],
  });

  // ✅ Indlæs cookies fra auth.json
  if (fs.existsSync('auth.json')) {
    const raw = JSON.parse(fs.readFileSync('auth.json', 'utf-8'));

    const cookies = raw.cookies || [];
    if (cookies.length === 0) {
      console.warn('[auth-context] ⚠️ auth.json indeholder ingen cookies');
    } else {
      await context.addCookies(cookies);
    }
  } else {
    console.warn('[auth-context] ⚠️ auth.json ikke fundet – login kræves');
  }

  const page = await context.newPage();
  return { browser, page };
}

module.exports = createAuthContext;
