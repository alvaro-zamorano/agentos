#!/usr/bin/env python3
"""
El Atajo — Playwright flow test
Recorre el Capítulo 1 completo usando hooks de test,
captura pantallazos 390×844 de cada escena.
Requisito: python3 -m playwright install chromium
"""

import os
import sys
import time
import threading
import http.server
import socket
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

# ── Rutas ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent        # el-atajo/
SHOTS_DIR = REPO_ROOT / "docs" / "40-tech" / "shots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Servidor HTTP local ────────────────────────────────────────────────────────
def find_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def start_server(directory: Path, port: int) -> threading.Thread:
    os.chdir(directory)
    server = http.server.HTTPServer(("127.0.0.1", port), SilentHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return t


# ── Helpers de espera ──────────────────────────────────────────────────────────
def wait_mode(page: Page, expected: str, timeout: float = 8.0):
    """Espera hasta que window.__STATE.mode == expected."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            mode = page.evaluate("window.__STATE && window.__STATE.mode")
            if mode == expected:
                return
        except Exception:
            pass
        time.sleep(0.1)
    mode = page.evaluate("window.__STATE && window.__STATE.mode")
    raise TimeoutError(f"Esperando mode='{expected}', got mode='{mode}' tras {timeout}s")


def wait_scene(page: Page, scene_id: str, timeout: float = 6.0):
    """Espera hasta que __STATE.scene == scene_id y mode == 'scene'."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = page.evaluate(
                "window.__STATE ? {mode: window.__STATE.mode, scene: window.__STATE.scene} : null"
            )
            if state and state.get("mode") == "scene" and state.get("scene") == scene_id:
                return
        except Exception:
            pass
        time.sleep(0.1)
    state = page.evaluate(
        "window.__STATE ? {mode: window.__STATE.mode, scene: window.__STATE.scene} : null"
    )
    raise TimeoutError(f"Esperando scene='{scene_id}', got {state} tras {timeout}s")


def advance_all_cutscenes(page: Page, max_steps: int = 30):
    """Avanza todos los beats de cutscene hasta salir del mode cutscene."""
    for _ in range(max_steps):
        try:
            mode = page.evaluate("window.__STATE && window.__STATE.mode")
        except Exception:
            break
        if mode != "cutscene":
            break
        page.evaluate("window.__advance()")
        time.sleep(0.15)


def advance_all_text(page: Page, max_steps: int = 5):
    """Descarta overlays de texto si están visibles."""
    for _ in range(max_steps):
        try:
            mode = page.evaluate("window.__STATE && window.__STATE.mode")
            if mode != "scene":
                break
            visible = page.evaluate(
                "document.getElementById('text-overlay').style.display !== 'none'"
            )
            if not visible:
                break
            page.evaluate("window.__advance()")
            time.sleep(0.1)
        except Exception:
            break


def capture(page: Page, name: str):
    path = str(SHOTS_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  📸 {name}.png")
    return path


# ── Test principal ─────────────────────────────────────────────────────────────
def run_flow(page: Page):
    errors = []

    def on_console(msg):
        if msg.type in ("error",) and "404" not in msg.text:
            errors.append(msg.text)

    page.on("console", on_console)

    # 1. Onboarding → iniciar juego
    print("[ 1/7 ] Onboarding")
    wait_mode(page, "onboarding")
    capture(page, "00-onboarding")
    page.evaluate("window.__advance()")          # dispara startGame() → cs_apertura
    time.sleep(0.3)

    # 2. Cutscene inicial (cs_apertura + cs_embargo)
    print("[ 2/7 ] Cutscenes iniciales")
    wait_mode(page, "cutscene")
    advance_all_cutscenes(page, max_steps=40)   # apertura + embargo
    # Después de cs_embargo → gotoScene('canada')
    wait_scene(page, "canada")
    capture(page, "01-canada")

    # 3. Cañada → interactuar con camino_bloqueado → cs_llegada_venta → venta
    print("[ 3/7 ] Cañada → Venta")
    page.evaluate("window.__tapWorld(90, 170)")  # camino_bloqueado
    time.sleep(0.3)
    advance_all_text(page)
    time.sleep(0.5)
    advance_all_cutscenes(page, max_steps=20)   # cs_llegada_venta
    wait_scene(page, "venta")
    capture(page, "02-venta")

    # 4. Usar __gotoScene para saltar directo a bancales (abre todos los flags)
    print("[ 4/7 ] Bancales")
    page.evaluate("window.__gotoScene('bancales')")
    wait_scene(page, "bancales")
    capture(page, "03-bancales")

    # 5. Telar
    print("[ 5/7 ] Telar")
    page.evaluate("window.__gotoScene('telar')")
    wait_scene(page, "telar")
    capture(page, "04-telar")

    # 6. Sótano
    print("[ 6/7 ] Sótano")
    page.evaluate("window.__gotoScene('sotano')")
    wait_scene(page, "sotano")
    capture(page, "05-sotano")

    # 7. Flujo completo: coleccionar los 4 items y entregar a Tía Velas
    print("[ 7/7 ] Flujo completo → fin")
    # Setear flags necesarios y añadir los 4 items de exvoto
    page.evaluate("""
        window.__setFlag('flag_bees_calmed', true);
        window.__setFlag('flag_pura_confrontada', true);
        window.__addItem('item_cera_virgen');
        window.__addItem('item_hilo_esparto');
        window.__addItem('item_nombre_escrito');
        window.__addItem('item_lagrima');
    """)
    page.evaluate("window.__gotoScene('venta')")
    wait_scene(page, "venta")

    # Simular tap en tia_velas (hotspot en venta: x=60,y=194 w=52 h=80 → centro ~86,234)
    page.evaluate("window.__tapWorld(86, 234)")
    time.sleep(0.4)
    advance_all_cutscenes(page, max_steps=60)   # cs_exvoto_completo + cs_pura_huye + cs_resurreccion
    time.sleep(0.5)

    # Verificar que llegamos al final
    mode = page.evaluate("window.__STATE && window.__STATE.mode")
    print(f"  Modo final: {mode}")

    capture(page, "06-fin")

    # Verificar errores de consola
    if errors:
        print(f"  ⚠️  Errores de consola: {errors}")
        return False
    return True


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    port = find_free_port()
    print(f"Servidor en http://127.0.0.1:{port}")
    start_server(REPO_ROOT, port)
    time.sleep(0.3)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        page = ctx.new_page()

        url = f"http://127.0.0.1:{port}/index.html"
        print(f"Abriendo {url}")
        page.goto(url, wait_until="networkidle", timeout=15000)

        # Esperar a que el motor esté listo (datos cargados + init() completado)
        page.wait_for_function("window.__SCRIPT && window.__GRAPH", timeout=10000)
        page.wait_for_function(
            "window.__STATE && window.__STATE.mode === 'onboarding'", timeout=10000
        )
        time.sleep(0.3)

        ok = run_flow(page)

        # Verificar pantallazos
        shots = list(SHOTS_DIR.glob("*.png"))
        print(f"\nPantallazos generados: {len(shots)}")
        for s in sorted(shots):
            print(f"  {s.name}")

        browser.close()

    if not ok:
        print("\n❌ Test fallido por errores de consola", file=sys.stderr)
        sys.exit(1)

    if len(shots) < 5:
        print(f"\n❌ Solo {len(shots)} pantallazos (mínimo 5)", file=sys.stderr)
        sys.exit(1)

    print("\n✅ flow.py completado correctamente")
    sys.exit(0)


if __name__ == "__main__":
    main()
