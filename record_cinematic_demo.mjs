import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';

// HAL Aerospace Mission Control - Cinematic Product Demo Director Script
// Directs an automated, smooth, professional engineering software demonstration (~6 minutes)
// Recorded in 1920x1080 Full HD using Playwright Chromium Video Recording

const RECORDINGS_DIR = path.resolve('./demo_recordings');
if (!fs.existsSync(RECORDINGS_DIR)) {
  fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
}

// Helper: Human-like smooth mouse movement
async function smoothMove(page, targetX, targetY, steps = 40) {
  await page.mouse.move(targetX, targetY, { steps });
}

// Helper: Move to element center and hover — graceful timeout
async function hoverElement(page, selector, hoverTimeMs = 2000, steps = 35, timeout = 8000) {
  try {
    const loc = page.locator(selector).first();
    await loc.waitFor({ state: 'visible', timeout });
    const box = await loc.boundingBox();
    if (box) {
      const targetX = box.x + box.width / 2;
      const targetY = box.y + box.height / 2;
      await page.mouse.move(targetX, targetY, { steps });
      await page.waitForTimeout(hoverTimeMs);
      return { x: targetX, y: targetY };
    }
  } catch (e) {
    console.warn(`[Director Warning] Hover timeout for: ${selector}`);
  }
  return null;
}

// Helper: Move to element, hover to let audience read, then click — never throws
async function clickElement(page, selector, hoverTimeMs = 1500, steps = 35, timeout = 8000) {
  const coords = await hoverElement(page, selector, hoverTimeMs, steps, timeout);
  if (coords) {
    await page.mouse.click(coords.x, coords.y);
    await page.waitForTimeout(1000);
    return true;
  }
  console.warn(`[Director Warning] Could not find or click selector: ${selector}`);
  return false;
}

async function runCinematicDemo() {
  console.log('====================================================================');
  console.log('STARTING HAL AEROSPACE MISSION CONTROL CINEMATIC DEMO RECORDING');
  console.log('Resolution: 1920x1080 Full HD | Target Duration: ~6 Minutes');
  console.log('====================================================================');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: RECORDINGS_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  // Inject Custom Professional Engineering Cursor Dot into DOM
  await page.addInitScript(() => {
    window.addEventListener('DOMContentLoaded', () => {
      const cursor = document.createElement('div');
      cursor.id = 'cinematic-cursor';
      cursor.style.cssText = 'position: fixed; top: 0; left: 0; width: 18px; height: 18px; background: rgba(220, 38, 38, 0.95); border: 2.5px solid #ffffff; border-radius: 50%; pointer-events: none; z-index: 2147483647; box-shadow: 0 0 12px rgba(220, 38, 38, 0.85), 0 0 3px #000000; transform: translate(-50%, -50%); transition: transform 0.08s ease-out, background-color 0.15s, box-shadow 0.15s;';
      document.body.appendChild(cursor);

      window.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
      });

      window.addEventListener('mousedown', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(0.65)';
        cursor.style.background = '#10B981'; // Emerald glow on click
        cursor.style.boxShadow = '0 0 16px rgba(16, 185, 129, 0.9), 0 0 4px #000000';
      });

      window.addEventListener('mouseup', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(1)';
        cursor.style.background = 'rgba(220, 38, 38, 0.95)';
        cursor.style.boxShadow = '0 0 12px rgba(220, 38, 38, 0.85), 0 0 3px #000000';
      });
    });
  });

  try {
    // -------------------------------------------------------------------------
    // 1. OPENING SEQUENCE (~20s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 1: Opening & Workstation Initialization...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(4000); // Allow splash & title to initialize naturally

    // Hover across top workstation header seals and LCA Tejas CAD blueprint
    await smoothMove(page, 300, 40, 40);
    await page.waitForTimeout(2000);
    await smoothMove(page, 960, 250, 50); // Move over LCA Tejas structural wireframe
    await page.waitForTimeout(3000);

    // -------------------------------------------------------------------------
    // 2. LOGIN WORKFLOW (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 2: Secure Credentials & Biometric Authentication...');
    
    // Ensure we select DEMO seeded mode for 100% reliable automated capture
    await clickElement(page, 'button:has-text("[ DEMO // SEEDED ]")', 1500);
    await page.waitForTimeout(1500);

    // Hover over Authorizing Operator dropdown
    await hoverElement(page, 'select', 2000);
    
    // Move to PKI password field and input credentials
    await clickElement(page, 'input[type="password"]', 1000);
    await page.waitForTimeout(1000);

    // Step 2: Click Validate Credentials & Initiate Biometric Matrix
    await clickElement(page, 'button:has-text("VALIDATE CREDENTIALS & INITIATE BIOMETRIC MATRIX")', 2000);
    await page.waitForTimeout(3500); // Step 3: Observe transition to Biometric matrix

    // Step 4: Live Biometric Scanner Challenge & Verification
    console.log('[Director] Scene 2b: Biometric Scanner Reticule & Liveness Challenge...');
    await smoothMove(page, 960, 600, 40); // Move cursor near scanning reticule
    await page.waitForTimeout(3500); // Let audience observe targeting brackets and liveness prompt

    // Hover over quality pills (CENTERED, LIGHTING, EYES)
    await smoothMove(page, 1150, 520, 30);
    await page.waitForTimeout(2500);

    // Click Verify Biometric Matrix
    await clickElement(page, 'button:has-text("VERIFY BIOMETRIC MATRIX & LIVENESS")', 1500);
    await page.waitForTimeout(3500); // Watch 98.4% similarity score & IDENTITY VERIFIED banner appear!

    // Step 5: Clearance Summary Profile
    console.log('[Director] Scene 2c: Operator Clearance Summary & Authorization...');
    await smoothMove(page, 960, 650, 35);
    await page.waitForTimeout(3500); // Allow audience to read clearance level & squadron assignment
    await clickElement(page, 'button:has-text("AUTHORIZE & BOOT MISSION CONTROL")', 2000);

    // -------------------------------------------------------------------------
    // 3. MISSION INITIALIZATION SEQUENCE (~20s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 3: Enterprise Bootstrap Loading Sequence...');
    await page.waitForTimeout(9000); // Allow all 8 bootstrap steps to complete naturally
    await page.waitForTimeout(3500); // Pause on completed initialization before dashboard transition

    // -------------------------------------------------------------------------
    // 4. MISSION OVERVIEW (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 4: Mission Overview Dashboard & CAD Viewports...');
    await page.waitForTimeout(4000); // Allow dashboard telemetry and 3D engine CAD to render

    // Hover over top KPI badges
    await smoothMove(page, 400, 25, 30);
    await page.waitForTimeout(2000);
    await smoothMove(page, 1400, 25, 35);
    await page.waitForTimeout(2000);

    // Move to Center Dock: GE F404 Digital Twin Viewport
    await smoothMove(page, 960, 450, 45);
    await page.waitForTimeout(3000);

    // Cycle through CAD Viewport Modes
    await clickElement(page, 'button:has-text("NORMAL ASSEMBLY")', 1500);
    await page.waitForTimeout(3000);
    await clickElement(page, 'button:has-text("X-RAY SPOOLS")', 1500);
    await page.waitForTimeout(4000); // Show rotating N1/N2 spools
    await clickElement(page, 'button:has-text("THERMAL FIELD")', 1500);
    await page.waitForTimeout(4000); // Show glowing thermal core
    await clickElement(page, 'button:has-text("NORMAL ASSEMBLY")', 1000);
    await page.waitForTimeout(2000);

    // -------------------------------------------------------------------------
    // 5. DIGITAL TWIN SUBSYSTEM INSPECTION (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 5: 3D Digital Twin Subsystem Diagnostics...');
    await clickElement(page, 'button:has-text("3D DIGITAL TWIN"), a:has-text("DIGITAL TWIN"), [data-nav="digital-twin"]', 2000);
    await page.waitForTimeout(3500);

    // Hover over engine schematic and click subsystem stages
    await clickElement(page, 'button:has-text("LPC"), div:has-text("#2 LPC"), button:has-text("Low Press Compressor")', 2000);
    await page.waitForTimeout(3500);
    
    await clickElement(page, 'button:has-text("COMBUSTOR"), div:has-text("#4 COMBUSTOR"), button:has-text("Annular Chamber")', 2000);
    await page.waitForTimeout(4500); // Allow audience to read +38°C thermal creep exceedance warning
    
    await clickElement(page, 'button:has-text("HPT"), div:has-text("#5 HPT"), button:has-text("Single Stage Air-Cooled")', 2000);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 6. LIVE TELEMETRY STREAMING (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 6: 60 FPS Live Telemetry Transducer Charts...');
    await clickElement(page, 'button:has-text("LIVE TELEMETRY"), a:has-text("TELEMETRY"), [data-nav="telemetry"]', 2000);
    await page.waitForTimeout(4000);

    // Move cursor slowly across charts to show live streaming data
    await smoothMove(page, 600, 350, 40);
    await page.waitForTimeout(3500);
    await smoothMove(page, 1300, 350, 40);
    await page.waitForTimeout(3500);
    await smoothMove(page, 600, 750, 40);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 7. THERMODYNAMICS & ENGINE ANALYSIS (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 7: Thermodynamics & Cycle Efficiency...');
    await clickElement(page, 'button:has-text("THERMODYNAMICS"), button:has-text("ENGINE ANALYSIS"), [data-nav="thermodynamics"], [data-nav="analysis"]', 2000);
    await page.waitForTimeout(4000);

    // Hover over Thermodynamic Cycle Efficiency and Compressor Stall Margin
    await smoothMove(page, 500, 300, 35);
    await page.waitForTimeout(3500);
    await smoothMove(page, 1400, 300, 35);
    await page.waitForTimeout(3500);

    // Scroll down to observe enthalpy/entropy degradation curves
    await page.mouse.wheel(0, 400);
    await page.waitForTimeout(4000);
    await page.mouse.wheel(0, -400);
    await page.waitForTimeout(2000);

    // -------------------------------------------------------------------------
    // 8. AI DIAGNOSTICS & RUL PREDICTION (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 8: AI Diagnostics & Weibull Reliability...');
    await clickElement(page, 'button:has-text("AI DIAGNOSTICS"), [data-nav="ai-diagnostics"], button:has-text("DIAGNOSTICS")', 2000);
    await page.waitForTimeout(4000);

    // Hover over Combustor Thermal Creep prediction and 88.4% failure probability
    await smoothMove(page, 700, 380, 40);
    await page.waitForTimeout(4500);
    await smoothMove(page, 1350, 550, 40); // Hover over recommended maintenance actions
    await page.waitForTimeout(4000);

    // -------------------------------------------------------------------------
    // 9. EXPLAINABILITY (XAI) (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 9: XAI Explainability SHAP Waterfall...');
    await clickElement(page, 'button:has-text("EXPLAINABILITY"), button:has-text("XAI"), [data-nav="xai"]', 2000);
    await page.waitForTimeout(4000);

    // Hover over top SHAP contributors (T4 Turbine Inlet Temp, N2 Vibration)
    await smoothMove(page, 800, 450, 40);
    await page.waitForTimeout(4000);
    await smoothMove(page, 800, 650, 35);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 10. PHYSICS MODELS & 0D/1D SOLVER (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 10: Real-time 0D/1D Thermodynamic Physics Solver...');
    await clickElement(page, 'button:has-text("PHYSICS MODELS"), button:has-text("PHYSICS"), [data-nav="physics"]', 2000);
    await page.waitForTimeout(4500);

    // Hover over compressor performance map (Beta vs Surge line)
    await smoothMove(page, 600, 500, 40);
    await page.waitForTimeout(4000);
    await smoothMove(page, 1400, 500, 40); // Observe numerical solver iterations
    await page.waitForTimeout(4000);

    // -------------------------------------------------------------------------
    // 11. ROOT CAUSE ANALYSIS / FAULT TREE (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 11: Causal Fault Propagation Tree...');
    await clickElement(page, 'button:has-text("ROOT CAUSE"), button:has-text("FAULT TREE"), [data-nav="root-cause"]', 2000);
    await page.waitForTimeout(4000);

    // Trace causal fault path: Injector Clogging -> Hot Spot -> Creep -> Fatigue
    await smoothMove(page, 400, 400, 35);
    await page.waitForTimeout(3000);
    await smoothMove(page, 800, 400, 35);
    await page.waitForTimeout(3000);
    await smoothMove(page, 1200, 400, 35);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 12. MAINTENANCE & LOGS (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 12: Work Orders & Horoscope Schedules...');
    await clickElement(page, 'button:has-text("WORK ORDERS"), button:has-text("MAINTENANCE"), [data-nav="maintenance"]', 2000);
    await page.waitForTimeout(4000);

    // Hover over open military work orders
    await smoothMove(page, 700, 450, 40);
    await page.waitForTimeout(4000);
    await smoothMove(page, 1300, 450, 40);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 13. MISSION REPLAY & SURGE SIMULATION (~35s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 13: Mission Replay & Compressor Surge Event...');
    await clickElement(page, 'button:has-text("MISSION REPLAY"), button:has-text("REPLAY"), [data-nav="replay"]', 2000);
    await page.waitForTimeout(3500);

    // Start playback
    await clickElement(page, 'button:has-text("PLAY"), button:has-text("START"), button:has-text("RESUME")', 1500);
    await page.waitForTimeout(4000);

    // Seek / jump timeline to compressor surge event
    await clickElement(page, 'button:has-text("SURGE"), button:has-text("ANOMALY"), div:has-text("Surge Event")', 1500);
    await page.waitForTimeout(6000); // Observe red pulsing surge arrows and synchronized telemetry reaction!

    // -------------------------------------------------------------------------
    // 14. HISTORICAL ANALYSIS (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 14: 500-Sortie Fleet Health Trends...');
    await clickElement(page, 'button:has-text("HISTORICAL"), button:has-text("TRENDS"), [data-nav="historical"]', 2000);
    await page.waitForTimeout(4000);

    await smoothMove(page, 600, 450, 40);
    await page.waitForTimeout(3500);
    await smoothMove(page, 1300, 450, 40);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 15. EVENT TIMELINE (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 15: Chronological Sortie Flight Log...');
    await clickElement(page, 'button:has-text("EVENT TIMELINE"), button:has-text("TIMELINE"), [data-nav="timeline"]', 2000);
    await page.waitForTimeout(3500);

    // Scroll and select critical events
    await smoothMove(page, 800, 350, 35);
    await page.waitForTimeout(3000);
    await page.mouse.wheel(0, 300);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 16. FLEET OPERATIONS (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 16: No. 45 Squadron Flying Daggers Fleet...');
    await clickElement(page, 'button:has-text("FLEET"), [data-nav="fleet"]', 2000);
    await page.waitForTimeout(4000);

    // Move cursor over the fleet matrix grid
    await smoothMove(page, 600, 400, 35);
    await page.waitForTimeout(2000);
    await smoothMove(page, 1100, 400, 35);
    await page.waitForTimeout(2000);

    // Click aircraft cards using correct tail identifiers from mockData
    // Tails: TJ-201, TJ-202, TJ-203, TJ-204 (No. 45 Sqn) | TJ-114..TJ-118 (No. 18 Sqn)
    await clickElement(page, 'div:has-text("TJ-201")', 1500);
    await page.waitForTimeout(3000);
    await clickElement(page, 'div:has-text("TJ-203")', 1500);
    await page.waitForTimeout(3000);
    await clickElement(page, 'div:has-text("TJ-204")', 1500); // Grounded - shows warning
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 17. ALERTS CENTER (~30s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 17: Prioritized Active Alerts Center...');
    await clickElement(page, 'button:has-text("ACTIVE ALERTS"), button:has-text("ALERTS"), [data-nav="alerts"]', 2000);
    await page.waitForTimeout(3500);

    // Hover over alert cards
    await smoothMove(page, 700, 350, 35);
    await page.waitForTimeout(3000);
    await smoothMove(page, 700, 500, 35);
    await page.waitForTimeout(3000);

    // Try filter buttons (graceful — won't abort if not found)
    await clickElement(page, 'button:has-text("CRITICAL")', 1000);
    await page.waitForTimeout(2500);
    await clickElement(page, 'button:has-text("ALL")', 1000);
    await page.waitForTimeout(2000);

    // -------------------------------------------------------------------------
    // 18. SETTINGS & CLEARANCE PROFILE (~25s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 18: HUD Settings & Workstation Configuration...');
    await clickElement(page, 'button:has-text("SETTINGS"), button:has-text("HUD"), [data-nav="settings"]', 2000);
    await page.waitForTimeout(4000);

    await smoothMove(page, 800, 400, 35);
    await page.waitForTimeout(3500);

    // -------------------------------------------------------------------------
    // 19. ENDING (~20s)
    // -------------------------------------------------------------------------
    console.log('[Director] Scene 19: Return to Mission Overview & Final Telemetry...');
    await clickElement(page, 'button:has-text("MISSION OVERVIEW"), button:has-text("OVERVIEW"), [data-nav="overview"]', 2000);
    await page.waitForTimeout(4000);

    // Allow live telemetry to stream smoothly in full glory
    await smoothMove(page, 960, 500, 50);
    await page.waitForTimeout(8000);

    console.log('[Director] Demonstration sequence completed successfully.');
  } catch (err) {
    console.error('[Director Error] Exception during automated demonstration:', err);
  } finally {
    console.log('[Director] Closing browser context and saving high-definition video recording...');
    await context.close();
    await browser.close();
    console.log('[Director] Video saved successfully in ./demo_recordings directory!');
  }
}

runCinematicDemo();
