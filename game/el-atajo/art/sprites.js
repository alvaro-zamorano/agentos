/**
 * EL ATAJO — SPRITES v1 (browser)
 * Canvas 180×320. S=2 (1px lógico = 2×2 px reales).
 */
(function() {
'use strict';
const P = window.P;

function px(ctx, rects, ox, oy, S, facing, spriteW) {
  const W = (spriteW || 14) * S;
  for (const [x, y, w, h, c] of rects) {
    ctx.fillStyle = c;
    const rx = facing === 'left' ? ox + W - (x + w) * S : ox + x * S;
    ctx.fillRect(rx, oy + y * S, w * S, h * S);
  }
}

function drawReme(ctx, x, y, frame, facing) {
  frame = frame || 0; facing = facing || 'right';
  const SKIN=P.PAJA_VIEJA, HAIR=P.TIERRA_SECA, SHIRT=P.AZUL_MANDIL, PANTS=P.OLIVO_OSCURO, BOOT=P.TIERRA_SECA, SH=P.NEGRO_SASTRE;
  const idle=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,SHIRT],[3,4,2,3,SH],[11,4,2,3,SH],[3,9,3,4,PANTS],[10,9,3,4,PANTS],[3,13,3,2,BOOT],[10,13,3,2,BOOT]];
  const walk1=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,SHIRT],[3,4,2,3,SH],[11,4,2,3,SH],[3,9,3,5,PANTS],[10,9,3,3,PANTS],[3,14,3,2,BOOT],[10,12,3,2,BOOT]];
  const walk2=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,SHIRT],[3,4,2,3,SH],[11,4,2,3,SH],[3,9,3,3,PANTS],[10,9,3,5,PANTS],[3,12,3,2,BOOT],[10,14,3,2,BOOT]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 16);
}

function drawTurbo(ctx, x, y, frame, facing) {
  frame=frame||0; facing=facing||'right';
  const FUR=P.CASTANO_TURBO, DARK=P.TIERRA_SECA, EYE=P.NEGRO_SASTRE, NOSE=P.SOMBRA_PROFUNDA;
  const idle=[[0,4,3,2,FUR],[3,3,2,2,FUR],[5,2,3,2,FUR],[8,2,4,3,FUR],[12,1,3,3,FUR],[14,1,1,2,DARK],[14,2,1,1,NOSE],[13,2,1,1,EYE],[0,6,2,1,FUR],[3,6,1,1,FUR],[10,6,1,1,FUR],[0,5,1,1,DARK]];
  const walk1=[[0,4,3,2,FUR],[3,3,2,2,FUR],[5,2,3,2,FUR],[8,2,4,3,FUR],[12,1,3,3,FUR],[14,1,1,2,DARK],[14,2,1,1,NOSE],[13,2,1,1,EYE],[1,6,2,1,FUR],[4,6,1,1,FUR],[9,6,1,1,FUR],[1,5,1,1,DARK]];
  const walk2=[[0,4,3,2,FUR],[3,3,2,2,FUR],[5,2,3,2,FUR],[8,2,4,3,FUR],[12,1,3,3,FUR],[14,1,1,2,DARK],[14,2,1,1,NOSE],[13,2,1,1,EYE],[0,5,2,1,FUR],[3,5,1,1,FUR],[10,5,1,1,FUR],[0,4,1,1,DARK]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 16);
}

function drawPura(ctx, x, y, frame, facing) {
  frame=frame||0; facing=facing||'right';
  const SUIT=P.NEGRO_SASTRE, SKIN=P.PAJA_VIEJA, HAIR=P.PIEDRA_OSCURA, LACRE=P.LACRE_ESCARLATA, BLOUSE=P.PIEDRA_CALIZA;
  const base=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,SUIT],[3,4,1,4,SUIT],[10,4,1,4,SUIT],[6,5,2,1,BLOUSE],[7,5,1,1,LACRE]];
  const idle=[...base,[4,9,2,4,SUIT],[8,9,2,4,SUIT],[4,13,2,2,SUIT],[8,13,2,2,SUIT]];
  const walk1=[...base,[4,9,2,5,SUIT],[8,9,2,3,SUIT],[4,14,2,2,SUIT],[8,12,2,2,SUIT]];
  const walk2=[...base,[4,9,2,3,SUIT],[8,9,2,5,SUIT],[4,12,2,2,SUIT],[8,14,2,2,SUIT]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 14);
}

function drawTiaVelas(ctx, x, y, frame, facing) {
  frame=frame||0; facing=facing||'right';
  const MANDIL=P.CERA_VELAS, SKIN=P.PAJA_VIEJA, HAIR=P.NEGRO_SASTRE, DRESS=P.BARRO_TOSTADO, MIEL=P.MIEL_AMBAR;
  const base=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,DRESS],[3,5,1,3,MANDIL],[10,5,1,3,MANDIL],[5,5,4,4,MANDIL],[6,7,2,2,MIEL]];
  const idle=[...base,[4,9,3,4,DRESS],[7,9,3,4,DRESS],[4,13,3,2,DRESS],[7,13,3,2,DRESS]];
  const walk1=[...base,[4,9,3,5,DRESS],[7,9,3,3,DRESS],[4,14,3,2,DRESS],[7,12,3,2,DRESS]];
  const walk2=[...base,[4,9,3,3,DRESS],[7,9,3,5,DRESS],[4,12,3,2,DRESS],[7,14,3,2,DRESS]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 14);
}

function drawMelquiades(ctx, x, y, frame, facing) {
  frame=frame||0; facing=facing||'right';
  const SUIT=P.TERGAL_MARRON, SKIN=P.PAJA_VIEJA, HAIR=P.GRIS_JUBILADO, WHITE=P.PIEDRA_CALIZA;
  const base=[[5,0,4,4,HAIR],[4,0,1,3,SKIN],[9,0,1,3,SKIN],[4,3,6,1,SKIN],[4,4,6,5,SUIT],[3,4,1,4,SUIT],[10,4,1,4,SUIT],[5,5,4,2,WHITE]];
  const idle=[...base,[4,9,2,4,SUIT],[8,9,2,4,SUIT],[4,13,2,2,SUIT],[8,13,2,2,SUIT]];
  const walk1=[...base,[4,9,2,5,SUIT],[8,9,2,3,SUIT],[4,14,2,2,SUIT],[8,12,2,2,SUIT]];
  const walk2=[...base,[4,9,2,3,SUIT],[8,9,2,5,SUIT],[4,12,2,2,SUIT],[8,14,2,2,SUIT]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 14);
}

function drawPractico(ctx, x, y, frame, facing) {
  frame=frame||0; facing=facing||'right';
  const WORK=P.GRIS_JUBILADO, SKIN=P.PAJA_VIEJA, BERET=P.TIERRA_SECA, SHIRT=P.HIERBA_POLVO;
  const base=[[4,0,6,2,BERET],[4,1,1,2,SKIN],[9,1,1,2,SKIN],[5,2,4,3,SKIN],[4,4,6,5,SHIRT],[3,5,1,3,WORK],[10,5,1,3,WORK]];
  const idle=[...base,[4,9,2,4,WORK],[8,9,2,4,WORK],[4,13,2,2,WORK],[8,13,2,2,WORK]];
  const walk1=[...base,[4,9,2,5,WORK],[8,9,2,3,WORK],[4,14,2,2,WORK],[8,12,2,2,WORK]];
  const walk2=[...base,[4,9,2,3,WORK],[8,9,2,5,WORK],[4,12,2,2,WORK],[8,14,2,2,WORK]];
  px(ctx, [idle,walk1,walk2][frame%3], x, y, 2, facing, 14);
}

window.Sprites = { drawReme, drawTurbo, drawPura, drawTiaVelas, drawMelquiades, drawPractico, px };
})();
