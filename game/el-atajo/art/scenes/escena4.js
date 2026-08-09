/* ESCENA 4 — Sala del Telar (browser) */
(function(){
'use strict';
const P=window.P;
function drawEscena4(ctx,t){
  const W=180,H=320,f=Math.floor(t/350)%4,sway=Math.sin(t/600),flicker=0.85+0.15*Math.sin(t/200);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(0,0,W,H);
  ctx.fillStyle=P.TIERRA_SECA; [0,58,118].forEach(vy=>ctx.fillRect(0,vy,W,8));
  ctx.fillStyle=P.CIELO_TORMENTA; ctx.fillRect(8,18,52,62);
  ctx.fillStyle=P.AZUL_HORA; ctx.fillRect(11,21,46,56);
  ctx.fillStyle=P.LAVANDA_TARDE; ctx.fillRect(11,21,46,22);
  ctx.fillStyle=P.TIERRA_SECA;
  ctx.fillRect(8,18,3,62); ctx.fillRect(57,18,3,62); ctx.fillRect(8,18,52,3); ctx.fillRect(8,77,52,3);
  ctx.fillStyle=P.PAJA_VIEJA; ctx.fillRect(32,18,3,62); ctx.fillRect(8,43,52,2);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(108,38,72,5);
  [113,123,133,143,153,163].forEach(lx=>{
    ctx.fillStyle=P.LACRE_ESCARLATA; ctx.fillRect(lx,26,7,13);
    ctx.fillStyle=P.PIEDRA_OSCURA; ctx.fillRect(lx+2,26,3,5);
  });
  ctx.fillStyle=P.TERGAL_MARRON;
  ctx.fillRect(18,88,14,132); ctx.fillRect(98,88,14,132); ctx.fillRect(18,86,94,12); ctx.fillRect(18,218,94,12);
  ctx.fillStyle=P.CERA_VELAS;
  for(let hx=34;hx<98;hx+=4){const dy=Math.round(sway*2); ctx.fillRect(hx,100+dy,2,120-dy);}
  ctx.fillStyle=P.SECANO_VERDE; ctx.fillRect(32,100,68,62);
  ctx.fillStyle=P.HIERBA_POLVO; for(let hy=100;hy<160;hy+=8) ctx.fillRect(32,hy,68,4);
  ctx.fillStyle=P.BARRO_TOSTADO; for(let hy=104;hy<160;hy+=8) ctx.fillRect(32,hy,68,4);
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(32,162,32,6);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(62,162,4,6);
  // Caja con lacre (hotspot)
  ctx.fillStyle=P.TERGAL_MARRON; ctx.fillRect(108,170,60,38);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(110,172,56,34);
  ctx.fillStyle=P.LACRE_ESCARLATA; ctx.fillRect(130,165,20,8); ctx.fillRect(137,160,6,14);
  // Madeja esparto
  ctx.fillStyle=P.PAJA_VIEJA; ctx.fillRect(120,222,36,22);
  ctx.fillStyle=P.HIERBA_POLVO; ctx.fillRect(122,224,32,18);
  ctx.fillStyle=P.TIERRA_SECA;
  for(let r=0;r<3;r++) ctx.fillRect(124,226+r*5,28,2);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(120,192,58,8); ctx.fillRect(120,200,10,50); ctx.fillRect(168,200,10,50);
  ctx.fillStyle=P.CERA_VELAS; ctx.fillRect(142,175,8,18);
  ctx.fillStyle=P.PONIENTE_NARANJA; ctx.globalAlpha=flicker; ctx.fillRect(143,169,6,8);
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(144,171,4,4); ctx.globalAlpha=1;
  ctx.fillStyle=P.MIEL_AMBAR; ctx.globalAlpha=0.14*flicker; ctx.fillRect(122,160,52,40); ctx.globalAlpha=1;
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(0,252,W,68);
  ctx.fillStyle=P.BARRO_TOSTADO; for(let fx=0;fx<W;fx+=32){ctx.fillRect(fx,252,30,10); ctx.fillRect(fx+14,262,30,10);}
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(0,272,W,3);
  ctx.fillStyle=P.CERA_VELAS; ctx.globalAlpha=0.5; ctx.fillRect(30,260,50,2); ctx.fillRect(42,265,30,2); ctx.globalAlpha=1;
  const mx=158-f*5, my=174+Math.round(Math.sin(t/220)*4);
  ctx.fillStyle=P.LAVANDA_TARDE; ctx.fillRect(mx,my,5,2);
  ctx.fillStyle=P.HUMO_AZUL; ctx.fillRect(mx+1,my+2,3,1);
}
window.Art=window.Art||{}; window.Art.escena4=drawEscena4;
})();
