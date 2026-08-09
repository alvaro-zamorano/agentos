/**
 * EL ATAJO — Motor v2
 * Canvas 180×320 · Mobile-first · Textos 100% del JSON
 */
(function () {
'use strict';

// ── DATA ──────────────────────────────────────────────────────────────────────
let SCRIPT, GRAPH;

// ── ESTADO GLOBAL ─────────────────────────────────────────────────────────────
const G = {
  mode: 'onboarding',   // onboarding | cutscene | dialog | scene | end
  scene: null,
  flags: {},
  inventory: [],
  look_counts: {},
  selected_item: null,
  input_mode: 'walk',   // walk | look | use
  player: { x: 90, y: 270 },
  player_target: null,
  player_facing: 'right',
  player_frame: 0,
  _pframe_t: 0,
  cutscene: null,       // {id, idx, beats}
  dialog: null,         // {id, node}
  obj_visible: false,
  t: 0,
};

// ── ITEM META (sin texto — solo para UI icon colors) ──────────────────────────
const ITEM_COLORS = {
  item_fumigador:        '#7a7d8a',
  item_tarro_vacio:      '#4a6fa5',
  item_cuaderno_antiguo: '#5c4a32',
  item_cera_virgen:      '#e8c97e',
  item_tijeras:          '#7a7d8a',
  item_hilo_esparto:     '#c4a265',
  item_papel_estraza:    '#e8d9b0',
  item_libro_deudas:     '#8b6a3e',
  item_nombre_escrito:   '#e8d9b0',
  item_lagrima:          '#4a6fa5',
};
const ITEM_ABBR = {
  item_fumigador:        'FUM',
  item_tarro_vacio:      'TAR',
  item_cuaderno_antiguo: 'CUA',
  item_cera_virgen:      'CER',
  item_tijeras:          'TIJ',
  item_hilo_esparto:     'HIL',
  item_papel_estraza:    'PAP',
  item_libro_deudas:     'LIB',
  item_nombre_escrito:   'NOM',
  item_lagrima:          'LÁG',
};

// ── ESCENAS (declarativo, sin texto de guion) ────────────────────────────────
const SCENES = {
  canada: {
    artFn: 'escena1',
    scriptKey: 'canada',
    walkbox: { x1: 44, y1: 148, x2: 136, y2: 315 },
    hotspots: [
      { id: 'camino_bloqueado', x: 52,  y: 148, w: 76, h: 48 },
      { id: 'señal_lacrada',    x: 50,  y: 158, w: 48, h: 28 },
      { id: 'maleta_pura',      x: 98,  y: 176, w: 34, h: 34 },
      { id: 'bicicleta',        x: 44,  y: 194, w: 34, h: 50 },
      { id: 'turbo',            x: 62,  y: 208, w: 54, h: 50 },
      { id: 'mojon',            x: 10,  y: 176, w: 32, h: 44 },
      { id: 'anima',            x: 140, y: 158, w: 28, h: 40 },
      { id: 'piedra_seca',      x: 62,  y: 258, w: 26, h: 26 },
    ],
    characters: [
      { id: 'turbo', x: 68, y: 240, fn: 'drawTurbo', facing: 'right' },
    ],
    exits: [],
    playerStart: { x: 90, y: 280 },
  },
  venta: {
    artFn: 'escena2',
    scriptKey: 'venta',
    walkbox: { x1: 10, y1: 200, x2: 170, y2: 315 },
    hotspots: [
      { id: 'tia_velas',      x: 60,  y: 194, w: 52, h: 80 },
      { id: 'pratico',        x: 10,  y: 194, w: 44, h: 80 },
      { id: 'melquiades',     x: 118, y: 194, w: 44, h: 80 },
      { id: 'mapa_cañadas',   x: 76,  y: 108, w: 44, h: 48 },
      { id: 'velas_exvoto',   x: 140, y: 148, w: 38, h: 44 },
      { id: 'barrica_miel',   x: 138, y: 215, w: 32, h: 32 },
      { id: 'puerta_trasera', x: 58,  y: 158, w: 54, h: 44 },
      { id: 'telefono_pared', x: 10,  y: 138, w: 34, h: 34 },
      { id: 'gato',           x: 98,  y: 274, w: 34, h: 34 },
    ],
    characters: [
      { id: 'tia_velas',  x: 66, y: 210, fn: 'drawTiaVelas',  facing: 'right' },
      { id: 'pratico',    x: 16, y: 210, fn: 'drawPractico',  facing: 'right' },
      { id: 'melquiades', x: 124, y: 210, fn: 'drawMelquiades', facing: 'left' },
    ],
    exits: [
      { id: 'to_bancales', x: 0,   y: 214, w: 14, h: 68, targetScene: 'bancales',
        condFlag: 'flag_portillo_conocido' },
      { id: 'to_telar',    x: 58,  y: 165, w: 54, h: 14, targetScene: 'telar',
        condFlag: 'flag_sala_telar_abierta' },
      { id: 'to_sotano',   x: 166, y: 214, w: 14, h: 68, targetScene: 'sotano',
        condFlag: 'flag_sotano_acceso' },
    ],
    playerStart: { x: 90, y: 270 },
  },
  bancales: {
    artFn: 'escena3',
    scriptKey: 'bancales',
    walkbox: { x1: 28, y1: 248, x2: 152, y2: 315 },
    hotspots: [
      { id: 'colmena',       x: 64,  y: 158, w: 48, h: 56 },
      { id: 'abeja_reina',   x: 60,  y: 148, w: 26, h: 24 },
      { id: 'fumigador',     x: 14,  y: 234, w: 38, h: 38 },
      { id: 'cesto_esparto', x: 96,  y: 216, w: 38, h: 38 },
      { id: 'pozo_seco',     x: 126, y: 156, w: 34, h: 46 },
      { id: 'olivo_partido', x: 2,   y: 136, w: 48, h: 70 },
      { id: 'tarro_vacio',   x: 126, y: 248, w: 28, h: 32 },
      { id: 'muro_piedra',   x: 0,   y: 138, w: 180, h: 26 },
    ],
    characters: [],
    exits: [
      { id: 'to_venta', x: 0, y: 248, w: 30, h: 67, targetScene: 'venta' },
    ],
    playerStart: { x: 90, y: 280 },
  },
  telar: {
    artFn: 'escena4',
    scriptKey: 'telar',
    walkbox: { x1: 0, y1: 250, x2: 180, y2: 315 },
    hotspots: [
      { id: 'telar',           x: 16,  y: 84,  w: 98, h: 138 },
      { id: 'madeja_esparto',  x: 116, y: 216, w: 48, h: 38 },
      { id: 'tijeras_oxidadas',x: 102, y: 176, w: 44, h: 38 },
      { id: 'espejo_roto',     x: 136, y: 78,  w: 38, h: 58 },
      { id: 'rueca',           x: 0,   y: 192, w: 38, h: 62 },
      { id: 'ventana_tapiada', x: 6,   y: 14,  w: 58, h: 72 },
      { id: 'caja_lacre',      x: 102, y: 158, w: 70, h: 58 },
      { id: 'cuaderno_antiguo',x: 26,  y: 92,  w: 40, h: 28 },
    ],
    characters: [],
    exits: [
      { id: 'to_venta', x: 0, y: 250, w: 30, h: 65, targetScene: 'venta' },
    ],
    playerStart: { x: 90, y: 280 },
  },
  sotano: {
    artFn: 'escena5',
    scriptKey: 'sotano',
    walkbox: { x1: 0, y1: 260, x2: 180, y2: 315 },
    hotspots: [
      { id: 'archivador',          x: 0,   y: 56,  w: 65, h: 110 },
      { id: 'campanilla_caja',     x: 64,  y: 68,  w: 50, h: 54 },
      { id: 'libro_deudas',        x: 0,   y: 146, w: 64, h: 22 },
      { id: 'vela_sebo',           x: 66,  y: 98,  w: 26, h: 40 },
      { id: 'pura_escritorio',     x: 106, y: 146, w: 74, h: 84 },
      { id: 'retrato_quincallero', x: 94,  y: 66,  w: 50, h: 62 },
      { id: 'caja_embargos',       x: 42,  y: 212, w: 60, h: 52 },
      { id: 'suelo_sal',           x: 52,  y: 282, w: 76, h: 26 },
    ],
    characters: [
      { id: 'pura', x: 124, y: 200, fn: 'drawPura', facing: 'left' },
    ],
    exits: [
      { id: 'to_venta', x: 0, y: 260, w: 30, h: 55, targetScene: 'venta' },
    ],
    playerStart: { x: 90, y: 280 },
  },
};

// ── CANVAS & DOM ──────────────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
canvas.width = 180; canvas.height = 320;
canvas.style.imageRendering = 'pixelated';

const elText = document.getElementById('text-overlay');
const elDialog = document.getElementById('dialog-overlay');
const elInv = document.getElementById('inventory');
const elObj = document.getElementById('obj-panel');
const elToolbar = document.getElementById('toolbar');
const btnLook = document.getElementById('btn-look');
const btnUse = document.getElementById('btn-use');
const btnObj = document.getElementById('btn-obj');
const elOnboard = document.getElementById('onboard');

function fitCanvas() {
  const tw = window.innerWidth;
  const th = window.innerHeight - 56; // subtract toolbar height
  const s = Math.min(tw / 180, th / 320);
  const cw = Math.floor(180 * s), ch = Math.floor(320 * s);
  canvas.style.width = cw + 'px';
  canvas.style.height = ch + 'px';
  const left = Math.floor((tw - cw) / 2);
  const top = Math.floor((th - ch) / 2);
  canvas.style.position = 'absolute';
  canvas.style.left = left + 'px';
  canvas.style.top = top + 'px';
  document.getElementById('game').style.height = (window.innerHeight - 56) + 'px';
}
window.addEventListener('resize', fitCanvas);
fitCanvas();

// ── TEXT HELPERS ──────────────────────────────────────────────────────────────
function getLookText(sceneKey, hotspotId) {
  const key = sceneKey + '/' + hotspotId;
  const n = G.look_counts[key] || 0;
  const looks = SCRIPT.scenes[sceneKey]?.hotspots[hotspotId]?.looks;
  if (!looks || !looks.length) return null;
  G.look_counts[key] = (n + 1) % looks.length;
  return looks[n];
}

function getInteractText(sceneKey, hotspotId, idx) {
  idx = idx || 0;
  const beats = SCRIPT.scenes[sceneKey]?.hotspots[hotspotId]?.interact;
  if (!beats || !beats.length) return null;
  const b = beats[idx % beats.length];
  return { speaker: b[0], line: b[1] };
}

function getComboText(a, b) {
  return SCRIPT.combos[a + '|' + b] || SCRIPT.combos[b + '|' + a] || null;
}

function itemLabel(id) {
  const label = GRAPH.nodes?.find(n => n.id === id)?.label;
  return label || id;
}

// ── SHOW/HIDE DOM OVERLAYS ───────────────────────────────────────────────────
function showText(speaker, line) {
  if (!line) return;
  elText.style.display = 'block';
  elText.innerHTML = `<span class="speaker">${speaker}</span><span class="line">${line}</span>`;
}

function hideText() {
  elText.style.display = 'none';
}

function showDialog(dialogId, startNode) {
  G.mode = 'dialog';
  G.dialog = { id: dialogId, node: startNode || SCRIPT.dialogs[dialogId]?.start };
  renderDialog();
}

function renderDialog() {
  if (!G.dialog) return;
  const dlg = SCRIPT.dialogs[G.dialog.id];
  if (!dlg) return;
  const node = dlg.nodes[G.dialog.node];
  if (!node) { closeDialog(); return; }

  // Trigger dialog flag callbacks
  const cbKey = G.dialog.id + '/' + G.dialog.node;
  if (DIALOG_FLAGS[cbKey]) DIALOG_FLAGS[cbKey]();

  let html = `<div class="d-speaker">${node.speaker}</div><div class="d-line">${node.line}</div><div class="d-opts">`;
  if (node.options && node.options.length > 0) {
    node.options.forEach((opt, i) => {
      html += `<button class="d-opt" data-idx="${i}">${opt.text}</button>`;
    });
  } else {
    html += `<button class="d-opt" data-idx="-1">Continuar</button>`;
  }
  html += '</div>';
  elDialog.innerHTML = html;
  elDialog.style.display = 'block';

  elDialog.querySelectorAll('.d-opt').forEach(btn => {
    btn.addEventListener('click', e => {
      const idx = parseInt(e.currentTarget.dataset.idx);
      if (idx < 0) { closeDialog(); return; }
      const next = node.options[idx]?.next;
      if (!next || next === '') { closeDialog(); return; }
      G.dialog.node = next;
      renderDialog();
    }, { once: false });
  });
}

function closeDialog() {
  elDialog.style.display = 'none';
  G.dialog = null;
  G.mode = 'scene';
}

const DIALOG_FLAGS = {
  'dialog_pratico/pr_bancales':  () => { G.flags.flag_portillo_conocido = true; },
  'dialog_pratico/pr_bancales2': () => { G.flags.flag_portillo_conocido = true; },
  'dialog_pratico/pr_bancales3': () => { G.flags.flag_portillo_conocido = true; },
  'dialog_pratico/pr_registro':  () => { G.flags.flag_sotano_acceso = true; },
  'dialog_pratico/pr_registro2': () => { G.flags.flag_sotano_acceso = true; },
  'dialog_pratico/pr_registro3': () => { G.flags.flag_sotano_acceso = true; },
  'dialog_pura/dp_lagrima':      () => { G.flags.flag_pura_confrontada = true; },
};

// ── CUTSCENE SYSTEM ───────────────────────────────────────────────────────────
function startCutscene(id) {
  const cs = SCRIPT.cutscenes[id];
  if (!cs) { console.warn('Unknown cutscene:', id); onCutsceneEnd(id); return; }
  G.mode = 'cutscene';
  G.cutscene = { id, idx: 0, beats: cs.beats };
  renderCutscene();
}

function renderCutscene() {
  if (!G.cutscene) return;
  const beat = G.cutscene.beats[G.cutscene.idx];
  if (!beat) { advanceCutscene(); return; }
  showText(beat.speaker, beat.line);
}

function advanceCutscene() {
  if (G.mode !== 'cutscene' || !G.cutscene) return;
  G.cutscene.idx++;
  if (G.cutscene.idx >= G.cutscene.beats.length) {
    const id = G.cutscene.id;
    G.cutscene = null;
    hideText();
    onCutsceneEnd(id);
  } else {
    renderCutscene();
  }
}

function onCutsceneEnd(id) {
  if (id === 'cs_apertura')        startCutscene('cs_embargo');
  else if (id === 'cs_embargo')    gotoScene('canada');
  else if (id === 'cs_llegada_venta') gotoScene('venta');
  else if (id === 'cs_pili_checkpoint') { G.mode = 'scene'; }
  else if (id === 'cs_exvoto_completo') startCutscene('cs_pura_huye');
  else if (id === 'cs_pura_huye')  startCutscene('cs_resurreccion');
  else if (id === 'cs_resurreccion') { G.mode = 'end'; hideText(); renderEnd(); }
  else G.mode = 'scene';
}

function renderEnd() {
  elOnboard.style.display = 'flex';
  elOnboard.innerHTML = '<div class="ob-title">FIN</div><div class="ob-sub">Capítulo 1 completado.</div>';
}

// ── SCENE NAVIGATION ──────────────────────────────────────────────────────────
function gotoScene(id) {
  if (!SCENES[id]) { console.error('Unknown scene:', id); return; }
  G.scene = id;
  G.mode = 'scene';
  G.input_mode = 'walk';
  G.selected_item = null;
  G.obj_visible = false;
  hideText();
  closeDialogIfOpen();
  const start = SCENES[id].playerStart;
  G.player.x = start.x; G.player.y = start.y;
  G.player_target = null;
  updateToolbar();
  updateInventoryDOM();
}

function closeDialogIfOpen() {
  if (G.dialog) { elDialog.style.display = 'none'; G.dialog = null; }
}

// ── PUZZLE / INTERACTION LOGIC ────────────────────────────────────────────────
function hasItems(...ids) { return ids.every(id => G.inventory.includes(id)); }
function addItem(id) { if (!G.inventory.includes(id)) G.inventory.push(id); updateInventoryDOM(); }
function removeItem(id) { G.inventory = G.inventory.filter(i => i !== id); updateInventoryDOM(); }
function hasAll4() { return hasItems('item_cera_virgen','item_hilo_esparto','item_nombre_escrito','item_lagrima'); }

function handleInteraction(sceneId, hotspotId) {
  const item = G.selected_item;
  const sk = SCENES[sceneId]?.scriptKey;
  hideText();

  // ── VENTA ────────────────────────────────────────────────────────────────
  if (sceneId === 'venta' && hotspotId === 'tia_velas') {
    if (hasAll4()) {
      // Final puzzle: entregar los 4 ingredientes
      removeItem('item_cera_virgen'); removeItem('item_hilo_esparto');
      removeItem('item_nombre_escrito'); removeItem('item_lagrima');
      startCutscene('cs_exvoto_completo');
      return;
    }
    if (item === 'item_cera_virgen') {
      // puzzle_cera_entrega
      G.flags.flag_sala_telar_abierta = true;
      const txt = getComboText('cera_virgen', 'tia_velas') || getInteractText(sk, 'tia_velas', 0)?.line;
      showText('REME', txt);
      startCutscene('cs_pili_checkpoint');
      deselectItem();
      return;
    }
    // Default: open dialog
    showDialog('dialog_tiavelas');
    return;
  }

  if (sceneId === 'venta' && hotspotId === 'pratico') {
    showDialog('dialog_pratico');
    return;
  }

  if (sceneId === 'venta' && hotspotId === 'melquiades') {
    const beats = SCRIPT.scenes.venta?.hotspots?.melquiades?.interact;
    if (beats) { showText(beats[0][0], beats[0][1]); }
    return;
  }

  if (sceneId === 'venta' && hotspotId === 'puerta_trasera') {
    if (G.flags.flag_sala_telar_abierta) {
      gotoScene('telar'); return;
    }
    const t = getInteractText(sk, 'puerta_trasera', 0);
    if (t) showText(t.speaker, t.line);
    return;
  }

  // ── CANADA ───────────────────────────────────────────────────────────────
  if (sceneId === 'canada' && hotspotId === 'camino_bloqueado') {
    if (!G.flags.flag_venta_activa) {
      G.flags.flag_venta_activa = true;
      const t = getInteractText(sk, 'camino_bloqueado', 0);
      if (t) showText(t.speaker, t.line);
      setTimeout(() => { startCutscene('cs_llegada_venta'); }, 800);
      return;
    }
    const t = getInteractText(sk, 'camino_bloqueado', 0);
    if (t) showText(t.speaker, t.line);
    return;
  }

  // ── BANCALES ─────────────────────────────────────────────────────────────
  if (sceneId === 'bancales') {
    if (hotspotId === 'fumigador' && !G.inventory.includes('item_fumigador')) {
      addItem('item_fumigador');
      const t = getInteractText(sk, 'fumigador', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
    if (hotspotId === 'tarro_vacio' && !G.inventory.includes('item_tarro_vacio')) {
      addItem('item_tarro_vacio');
      const t = getInteractText(sk, 'tarro_vacio', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
    if (hotspotId === 'olivo_partido' && !G.inventory.includes('item_cuaderno_antiguo')) {
      addItem('item_cuaderno_antiguo');
      const t = getInteractText(sk, 'olivo_partido', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
    if (hotspotId === 'colmena') {
      if (item === 'item_fumigador' && !G.flags.flag_bees_calmed) {
        G.flags.flag_bees_calmed = true;
        removeItem('item_fumigador');
        const txt = getComboText('fumigador', 'colmena');
        showText('REME', txt || getInteractText(sk,'colmena',0)?.line);
        deselectItem();
        return;
      }
      if (item === 'item_tarro_vacio' && G.flags.flag_bees_calmed && !G.inventory.includes('item_cera_virgen')) {
        removeItem('item_tarro_vacio');
        addItem('item_cera_virgen');
        const t = getInteractText(sk, 'colmena', 0);
        if (t) showText(t.speaker, t.line);
        deselectItem();
        return;
      }
      if (!G.flags.flag_bees_calmed) {
        const t = getInteractText(sk, 'colmena', 0);
        if (t) showText(t.speaker, t.line);
        return;
      }
    }
  }

  // ── TELAR ─────────────────────────────────────────────────────────────────
  if (sceneId === 'telar') {
    if (hotspotId === 'caja_lacre') {
      if (item === 'item_cuaderno_antiguo' && G.flags.flag_sala_telar_abierta) {
        if (!G.inventory.includes('item_tijeras')) {
          addItem('item_tijeras');
          const t = getInteractText(sk, 'tijeras_oxidadas', 0);
          if (t) showText(t.speaker, t.line);
        } else {
          const t = getInteractText(sk, 'caja_lacre', 0);
          if (t) showText(t.speaker, t.line);
        }
        deselectItem();
        return;
      }
      const t = getInteractText(sk, 'caja_lacre', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
    if (hotspotId === 'tijeras_oxidadas') {
      if (G.inventory.includes('item_tijeras')) {
        const t = getInteractText(sk, 'tijeras_oxidadas', 0);
        if (t) showText(t.speaker, t.line);
      } else {
        const t = getInteractText(sk, 'tijeras_oxidadas', 0);
        if (t) showText(t.speaker, t.line);
      }
      return;
    }
    if (hotspotId === 'madeja_esparto') {
      if (item === 'item_tijeras') {
        removeItem('item_tijeras');
        addItem('item_hilo_esparto');
        const txt = getComboText('madeja_esparto', 'tijeras_oxidadas');
        showText('REME', txt || getInteractText(sk,'madeja_esparto',0)?.line);
        deselectItem();
        return;
      }
      const t = getInteractText(sk, 'madeja_esparto', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
  }

  // ── SÓTANO ────────────────────────────────────────────────────────────────
  if (sceneId === 'sotano') {
    if (hotspotId === 'archivador') {
      if (!G.inventory.includes('item_libro_deudas')) {
        addItem('item_papel_estraza');
        addItem('item_libro_deudas');
        const t = getInteractText(sk, 'archivador', 0);
        if (t) showText(t.speaker, t.line);
        return;
      }
    }
    if (hotspotId === 'libro_deudas') {
      if (item === 'item_papel_estraza' && !G.inventory.includes('item_nombre_escrito')) {
        removeItem('item_papel_estraza');
        addItem('item_nombre_escrito');
        const txt = getComboText('papel_estraza', 'libro_deudas');
        showText('REME', txt || getInteractText(sk,'libro_deudas',0)?.line);
        deselectItem();
        return;
      }
      const t = getInteractText(sk, 'libro_deudas', 0);
      if (t) showText(t.speaker, t.line);
      return;
    }
    if (hotspotId === 'pura_escritorio') {
      if (item === 'item_tarro_vacio' && G.flags.flag_pura_confrontada) {
        removeItem('item_tarro_vacio');
        addItem('item_lagrima');
        const t = SCRIPT.dialogs.dialog_pura?.nodes?.dp_lagrima;
        showText('DOÑA PURA', t?.line || '...');
        deselectItem();
        return;
      }
      if (item === 'item_libro_deudas') {
        G.flags.flag_pura_confrontada = true;
        showDialog('dialog_pura', 'dp_libro');
        deselectItem();
        return;
      }
      if (item === 'item_cuaderno_antiguo') {
        showDialog('dialog_pura', 'dp_cuaderno');
        deselectItem();
        return;
      }
      // Default: talk to pura
      showDialog('dialog_pura');
      return;
    }
  }

  // ── COMBO FALLBACK ────────────────────────────────────────────────────────
  if (item) {
    const itemBase = item.replace('item_', '');
    const txt = getComboText(itemBase, hotspotId);
    if (txt) { showText('REME', txt); deselectItem(); return; }
  }

  // ── DEFAULT TEXT ──────────────────────────────────────────────────────────
  const t = getInteractText(sk, hotspotId, 0);
  if (t) showText(t.speaker, t.line);
}

function deselectItem() {
  G.selected_item = null;
  G.input_mode = 'walk';
  updateToolbar();
  updateInventoryDOM();
}

// ── INPUT HANDLING ────────────────────────────────────────────────────────────
function canvasCoords(cx, cy) {
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return { x: 0, y: 0 };
  return {
    x: Math.round((cx - rect.left) * 180 / rect.width),
    y: Math.round((cy - rect.top)  * 320 / rect.height),
  };
}

function handleCanvasTap(clientX, clientY) {
  if (G.mode === 'onboarding') { startGame(); return; }
  if (G.mode === 'end') return;
  if (G.mode === 'cutscene') { advanceCutscene(); return; }
  if (G.mode === 'dialog') return;

  const { x, y } = canvasCoords(clientX, clientY);

  // Dismiss text if visible
  if (elText.style.display !== 'none') {
    hideText();
    return;
  }

  if (G.mode !== 'scene') return;
  const sceneDef = SCENES[G.scene];
  if (!sceneDef) return;

  // Check exits
  for (const exit of sceneDef.exits) {
    if (x >= exit.x && x <= exit.x + exit.w && y >= exit.y && y <= exit.y + exit.h) {
      if (!exit.condFlag || G.flags[exit.condFlag]) {
        gotoScene(exit.targetScene);
        return;
      }
    }
  }

  // Check hotspots
  let hit = null;
  for (const hs of sceneDef.hotspots) {
    if (x >= hs.x && x <= hs.x + hs.w && y >= hs.y && y <= hs.y + hs.h) {
      hit = hs;
      break;
    }
  }

  if (hit) {
    if (G.input_mode === 'look') {
      const sk = sceneDef.scriptKey;
      const line = getLookText(sk, hit.id);
      if (line) showText('REME', line);
      return;
    }
    // walk or use mode
    handleInteraction(G.scene, hit.id);
    return;
  }

  // Walkbox tap → move player
  const wb = sceneDef.walkbox;
  if (x >= wb.x1 && x <= wb.x2 && y >= wb.y1 && y <= wb.y2) {
    G.player_target = { x, y };
    G.player_facing = x > G.player.x ? 'right' : 'left';
  }
}

canvas.addEventListener('click', e => handleCanvasTap(e.clientX, e.clientY));
canvas.addEventListener('touchstart', e => {
  e.preventDefault();
  handleCanvasTap(e.changedTouches[0].clientX, e.changedTouches[0].clientY);
}, { passive: false });

// ── TOOLBAR BUTTONS ───────────────────────────────────────────────────────────
function updateToolbar() {
  btnLook.classList.toggle('active', G.input_mode === 'look');
  btnUse.classList.toggle('active', G.input_mode === 'use' || G.selected_item !== null);
}

btnLook.addEventListener('click', () => {
  if (G.mode !== 'scene') return;
  G.input_mode = G.input_mode === 'look' ? 'walk' : 'look';
  G.selected_item = null;
  updateToolbar(); updateInventoryDOM();
});

btnUse.addEventListener('click', () => {
  if (G.mode !== 'scene') return;
  G.input_mode = G.input_mode === 'use' ? 'walk' : 'use';
  updateToolbar(); updateInventoryDOM();
});

btnObj.addEventListener('click', () => {
  if (G.mode !== 'scene') return;
  G.obj_visible = !G.obj_visible;
  if (G.obj_visible) {
    const goal = Object.values(SCRIPT.goals || {})[0];
    elObj.textContent = goal ? goal.description : '—';
    elObj.style.display = 'block';
  } else {
    elObj.style.display = 'none';
  }
});

// ── INVENTORY DOM ─────────────────────────────────────────────────────────────
function updateInventoryDOM() {
  if (G.mode !== 'scene') { elInv.style.display = 'none'; return; }
  if (G.input_mode !== 'use' && !G.selected_item) { elInv.style.display = 'none'; return; }
  if (!G.inventory.length) { elInv.style.display = 'none'; return; }

  elInv.style.display = 'flex';
  elInv.innerHTML = '';
  G.inventory.forEach(id => {
    const btn = document.createElement('button');
    btn.className = 'inv-item' + (G.selected_item === id ? ' inv-sel' : '');
    btn.style.backgroundColor = ITEM_COLORS[id] || '#555';
    btn.textContent = ITEM_ABBR[id] || id.slice(5, 8).toUpperCase();
    btn.title = itemLabel(id);
    btn.addEventListener('click', () => {
      G.selected_item = (G.selected_item === id) ? null : id;
      G.input_mode = G.selected_item ? 'use' : 'walk';
      updateToolbar(); updateInventoryDOM();
    });
    elInv.appendChild(btn);
  });
}

// ── GAME LOOP / UPDATE ────────────────────────────────────────────────────────
function update(t) {
  // Player movement
  if (G.mode === 'scene' && G.player_target) {
    const dx = G.player_target.x - G.player.x;
    const dy = G.player_target.y - G.player.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 3) {
      G.player.x = G.player_target.x;
      G.player.y = G.player_target.y;
      G.player_target = null;
      G.player_frame = 0;
    } else {
      const speed = 1.5;
      G.player.x += (dx / dist) * speed;
      G.player.y += (dy / dist) * speed;
      G.player_facing = dx > 0 ? 'right' : 'left';
      G._pframe_t++;
      if (G._pframe_t % 12 === 0) G.player_frame = (G.player_frame + 1) % 3;
    }
  } else {
    G.player_frame = 0;
  }
}

// ── RENDERING ─────────────────────────────────────────────────────────────────
function render(t) {
  ctx.clearRect(0, 0, 180, 320);

  if (G.mode === 'onboarding') { renderOnboarding(t); return; }
  if (G.mode === 'end') return;

  // Scene background
  if (G.scene && SCENES[G.scene]) {
    const artFn = window.Art?.[SCENES[G.scene].artFn];
    if (artFn) artFn(ctx, t);
  }

  if (G.mode === 'cutscene' || G.mode === 'scene' || G.mode === 'dialog') {
    renderCharacters(t);
    renderPlayer(t);
    renderHotspotHints(t);
    renderExitHints(t);
    renderModeIndicator(t);
  }
}

function renderOnboarding(t) {
  const f = Math.floor(t / 800) % 2;
  ctx.fillStyle = '#1a1225';
  ctx.fillRect(0, 0, 180, 320);
  ctx.fillStyle = '#2b3a6b';
  ctx.fillRect(0, 0, 180, 100);
  // Stars
  ctx.fillStyle = '#e8d9b0';
  [[20,15],[50,8],[80,22],[120,10],[150,18],[170,30],[30,40],[100,35]].forEach(([sx,sy]) => {
    ctx.fillRect(sx, sy, f===0?2:1, f===0?2:1);
  });
  // Sun low
  ctx.fillStyle = '#e8864a';
  ctx.fillRect(70, 80, 40, 20);
  ctx.fillStyle = '#f2c46d';
  ctx.fillRect(76, 83, 28, 14);
  // Road
  ctx.fillStyle = '#8b6a3e';
  ctx.fillRect(40, 100, 100, 220);
  ctx.fillStyle = '#5c4a32';
  for (let i = 0; i < 7; i++) ctx.fillRect(85, 120 + i * 28, 10, 4);
}

function renderCharacters(t) {
  if (!G.scene) return;
  const sceneDef = SCENES[G.scene];
  if (!sceneDef.characters) return;
  const fr = Math.floor(t / 400) % 3;
  sceneDef.characters.forEach(ch => {
    const fn = window.Sprites?.[ch.fn];
    if (fn) fn(ctx, ch.x, ch.y, 0, ch.facing || 'right');
  });
}

function renderPlayer(t) {
  if (G.mode !== 'scene') return;
  window.Sprites?.drawReme(ctx, G.player.x - 16, G.player.y - 30, G.player_frame, G.player_facing);
}

function renderHotspotHints(t) {
  if (G.input_mode !== 'look') return;
  const sceneDef = SCENES[G.scene];
  if (!sceneDef) return;
  ctx.fillStyle = 'rgba(232,217,176,0.4)';
  sceneDef.hotspots.forEach(hs => {
    ctx.fillRect(hs.x, hs.y, hs.w, hs.h);
  });
}

function renderExitHints(t) {
  const sceneDef = SCENES[G.scene];
  if (!sceneDef) return;
  sceneDef.exits.forEach(exit => {
    const ok = !exit.condFlag || G.flags[exit.condFlag];
    ctx.fillStyle = ok ? 'rgba(107,140,69,0.5)' : 'rgba(255,255,255,0.1)';
    ctx.fillRect(exit.x, exit.y, exit.w, exit.h);
    if (ok) {
      ctx.fillStyle = '#e8d9b0';
      ctx.fillRect(exit.x + exit.w/2 - 2, exit.y + exit.h/2 - 2, 4, 4);
    }
  });
}

function renderModeIndicator(t) {
  if (G.input_mode === 'look') {
    ctx.fillStyle = 'rgba(43,58,107,0.7)';
    ctx.fillRect(0, 0, 180, 12);
    ctx.fillStyle = '#e8d9b0';
    ctx.font = '8px monospace';
    ctx.fillText('MIRAR', 2, 9);
  } else if (G.selected_item) {
    ctx.fillStyle = 'rgba(196,32,42,0.7)';
    ctx.fillRect(0, 0, 180, 12);
    ctx.fillStyle = '#e8d9b0';
    ctx.font = '8px monospace';
    ctx.fillText('USAR: ' + (ITEM_ABBR[G.selected_item] || '?'), 2, 9);
  }
}

// ── START GAME ────────────────────────────────────────────────────────────────
function startGame() {
  elOnboard.style.display = 'none';
  startCutscene('cs_apertura');
}

// ── INIT ──────────────────────────────────────────────────────────────────────
function init() {
  SCRIPT = window.__SCRIPT;
  GRAPH  = window.__GRAPH;
  if (!SCRIPT || !GRAPH) { console.error('Data not loaded'); return; }

  elOnboard.style.display = 'flex';
  elText.style.display = 'none';
  elDialog.style.display = 'none';
  elInv.style.display = 'none';
  elObj.style.display = 'none';
  elToolbar.style.display = 'flex';

  let prev = 0;
  function loop(ts) {
    G.t = ts;
    const dt = ts - prev; prev = ts;
    update(dt);
    render(ts);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

// ── HOOKS (window.__*) ────────────────────────────────────────────────────────
window.__STATE = G;

window.__tapWorld = function(x, y) {
  // Tap at canvas coords (0..180, 0..320) → simulate as center of screen
  const rect = canvas.getBoundingClientRect();
  const clientX = rect.left + (x / 180) * rect.width;
  const clientY = rect.top  + (y / 320) * rect.height;
  handleCanvasTap(clientX, clientY);
};

window.__lookWorld = function(x, y) {
  G.input_mode = 'look';
  updateToolbar();
  window.__tapWorld(x, y);
};

window.__advance = function() {
  if (G.mode === 'onboarding') { startGame(); return; }
  if (G.mode === 'cutscene') { advanceCutscene(); return; }
  if (G.mode === 'dialog') {
    // click first option
    const btn = elDialog.querySelector('.d-opt');
    if (btn) btn.click();
    return;
  }
  if (elText.style.display !== 'none') { hideText(); return; }
};

window.__gotoScene = function(id) {
  if (G.mode === 'onboarding') {
    elOnboard.style.display = 'none';
  }
  // Make conditions permissive for testing
  G.flags.flag_venta_activa = true;
  G.flags.flag_portillo_conocido = true;
  G.flags.flag_sala_telar_abierta = true;
  G.flags.flag_sotano_acceso = true;
  gotoScene(id);
};

window.__setFlag = function(flag, val) { G.flags[flag] = val !== false; };
window.__addItem = function(id) { addItem(id); };

// Wait for DOM + data (fetch is async; poll until both are ready)
function _waitAndInit() {
  if (window.__SCRIPT && window.__GRAPH) {
    init();
  } else {
    setTimeout(_waitAndInit, 50);
  }
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _waitAndInit);
} else {
  _waitAndInit();
}

})();
