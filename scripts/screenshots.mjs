// Screenshots of the Work Search app running against the demo database.
//
//   1. python scripts/demo_seed.py
//   2. start the app with WORKSEARCH_DB=demo/demo.db WORKSEARCH_NO_CATCHUP=1 on port 8765
//   3. node scripts/screenshots.mjs
//
// Needs Playwright with Chromium. PLAYWRIGHT_PATH can point at a node_modules/playwright folder.

import { createRequire } from 'node:module'
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright')
const URL = process.env.APP_URL || 'http://127.0.0.1:8765/'
const OUT = join(ROOT, 'docs', 'img')

const SHOTS = [
  { name: 'today', tab: 'today', theme: 'light' },
  { name: 'matches', tab: 'matches', theme: 'light' },
  // The board has six columns and scrolls sideways inside the app's 1240px page width.
  // For this picture only, the page is allowed to grow so every column shows.
  { name: 'board', tab: 'board', theme: 'light', width: 1840, css: '.wrap { max-width: 1800px; }' },
  { name: 'week', tab: 'week', theme: 'light' },
  { name: 'matches-dark', tab: 'matches', theme: 'dark' },
]

mkdirSync(OUT, { recursive: true })
const browser = await chromium.launch()
for (const s of SHOTS) {
  const page = await browser.newPage({ viewport: { width: s.width || 1280, height: 820 }, deviceScaleFactor: 2, colorScheme: s.theme })
  await page.addInitScript(([tab, theme]) => {
    localStorage.setItem('ws-tab', tab)
    localStorage.setItem('ws-theme', theme)
  }, [s.tab, s.theme])
  await page.goto(URL, { waitUntil: 'networkidle' })
  if (s.css) await page.addStyleTag({ content: s.css })
  // Let the title waves and any fade settle before the picture.
  await page.waitForTimeout(1200)
  await page.screenshot({ path: join(OUT, `${s.name}.jpg`), type: 'jpeg', quality: 82 })
  console.log(`wrote docs/img/${s.name}.jpg`)
  await page.close()
}
await browser.close()
