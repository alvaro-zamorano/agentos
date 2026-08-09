/* ESCENA 2 — Venta de Tía Velas (browser) */
(function(){
'use strict';
const P = window.P;
function drawEscena2(ctx, t) {
  const W=180,H=320,f=Math.floor(t/300)%3,flicker=0.85+0.15*Math.sin(t/180);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(0,0,W,H);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(0,0,W,10); ctx.fillRect(0,H-10,W,10);
  ctx.fillStyle=P.CIELO_TORMENTA; ctx.fillRect(112,28,54,68);
  ctx.fillStyle=P.AZUL_HORA; ctx.fillRect(115,31,48,62);
  ctx.fillStyle=P.LAVANDA_TARDE; ctx.fillRect(115,31,48,22);
  ctx.fillStyle=P.TIERRA_SECA;
  ctx.fillRect(112,28,3,68); ctx.fillRect(163,28,3,68); ctx.fillRect(112,28,54,3); ctx.fillRect(112,93,54,3);
  ctx.fillStyle=P.PAJA_VIEJA; ctx.fillRect(136,28,3,68);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(10,178,44,142);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(13,181,38,136);
  ctx.fillStyle=P.MIEL_AMBAR; ctx.fillRect(40,248,5,5);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(0,108,132,6); ctx.fillRect(0,158,82,5);
  [28,58,88].forEach((cx,i)=>{
    ctx.fillStyle=P.CASTANO_TURBO; ctx.fillRect(cx,118,22,30);
    ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(cx+2,120,18,26);
    ctx.fillStyle=P.MIEL_AMBAR;
    for(let r=0;r<4;r++) ctx.fillRect(cx+4,122+r*5,14,3);
    ctx.fillStyle=P.SOMBRA_PROFUNDA; ctx.fillRect(cx+7,144,8,3);
    if(f===i%3){ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(cx+10,110-f*3,3,2); ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(cx+11,110-f*3,1,1);}
  });
  [10,28,46,64].forEach(tx=>{
    ctx.fillStyle=P.MIEL_AMBAR; ctx.fillRect(tx,90,14,18);
    ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(tx+2,90,10,5);
    ctx.fillStyle=P.CERA_VELAS; ctx.fillRect(tx+4,88,6,3);
  });
  ctx.fillStyle=P.TERGAL_MARRON; ctx.fillRect(0,218,W,12);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(0,230,W,90);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(0,236,W,6);
  ctx.fillStyle=P.CERA_VELAS; ctx.fillRect(140,208,5,12);
  ctx.fillStyle=P.MIEL_AMBAR; ctx.fillRect(152,210,12,10);
  [[148,158],[162,153],[172,166]].forEach(([cx,cy],i)=>{
    ctx.fillStyle=P.CERA_VELAS; ctx.fillRect(cx,cy,5,18);
    ctx.fillStyle=P.PONIENTE_NARANJA; ctx.globalAlpha=flicker*(0.8+0.2*(i%2));
    ctx.fillRect(cx+1,cy-5,3,6);
    ctx.fillStyle=P.SOL_BAJO; ctx.globalAlpha=flicker; ctx.fillRect(cx+1,cy-4,3,3);
    ctx.globalAlpha=1;
    ctx.fillStyle=P.MIEL_AMBAR; ctx.globalAlpha=0.10*flicker; ctx.fillRect(cx-7,cy-10,19,24);
    ctx.globalAlpha=1;
  });
  const bx=46+f*14, by=112-f*4;
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(bx,by,5,2);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(bx+1,by,3,1);
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.globalAlpha=0.6;
  ctx.fillRect(bx-1,by-2,2,1); ctx.fillRect(bx+4,by-2,2,1);
  ctx.globalAlpha=1;
  // Indicadores de salida
  // Portillo izquierda (aparece si flag)
  ctx.fillStyle=P.SECANO_VERDE; ctx.globalAlpha=0.5;
  ctx.fillRect(0,215,12,70);
  ctx.globalAlpha=1;
  // Puerta trasera
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(60,160,50,42);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(63,163,44,36);
  ctx.fillStyle=P.MIEL_AMBAR; ctx.fillRect(98,178,5,5);
  // Sótano (higuera, derecha)
  ctx.fillStyle=P.SECANO_VERDE; ctx.globalAlpha=0.5;
  ctx.fillRect(168,215,12,70);
  ctx.globalAlpha=1;
}
window.Art=window.Art||{}; window.Art.escena2=drawEscena2;
})();
