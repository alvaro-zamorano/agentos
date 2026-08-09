/* ESCENA 3 — Bancales de la Colmena (browser) */
(function(){
'use strict';
const P=window.P;
function drawEscena3(ctx,t){
  const W=180,H=320,f=Math.floor(t/500)%4,sway=Math.sin(t/800);
  const sky=ctx.createLinearGradient(0,0,0,125);
  sky.addColorStop(0,P.CIELO_TORMENTA); sky.addColorStop(0.4,P.LAVANDA_TARDE);
  sky.addColorStop(0.7,P.PONIENTE_ROSA); sky.addColorStop(1,P.PONIENTE_NARANJA);
  ctx.fillStyle=sky; ctx.fillRect(0,0,W,125);
  ctx.fillStyle=P.PONIENTE_NARANJA; ctx.fillRect(138,88,24,12);
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(142,90,16,8);
  ctx.fillStyle=P.OLIVO_OSCURO;
  [0,28,58,92,128,156].forEach(ox=>{ctx.fillRect(ox,96,20,32); ctx.fillRect(ox+4,80,12,20);});
  ctx.fillStyle=P.PIEDRA_OSCURA;
  ctx.fillRect(0,142,W,8); ctx.fillRect(0,192,W,8); ctx.fillRect(0,242,W,8);
  ctx.fillStyle=P.PIEDRA_CALIZA;
  for(let bx=0;bx<W;bx+=22){ctx.fillRect(bx,142,18,5); ctx.fillRect(bx+4,192,16,4); ctx.fillRect(bx+2,242,16,4);}
  ctx.fillStyle=P.SECANO_VERDE; ctx.fillRect(0,150,W,14);
  ctx.fillStyle=P.HIERBA_POLVO; ctx.fillRect(0,162,W,30); ctx.fillRect(0,200,W,12);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(0,212,W,30);
  ctx.fillStyle=P.OLIVO_OSCURO;
  [[8,152],[42,154],[78,150],[118,153],[152,155]].forEach(([zx,zy])=>{ctx.fillRect(zx,zy,16,9); ctx.fillRect(zx+2,zy-5,12,7);});
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(28,250,124,70);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(36,250,108,14);
  ctx.fillStyle=P.OLIVO_OSCURO; ctx.fillRect(26,250,4,70); ctx.fillRect(150,250,4,70);
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(55,270,7,3); ctx.fillRect(90,290,9,4); ctx.fillRect(120,305,6,3);
  // Colmena vieja (centro-izquierda bancal 2)
  ctx.fillStyle=P.CASTANO_TURBO; ctx.fillRect(65,162,40,32);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(67,164,36,28);
  ctx.fillStyle=P.MIEL_AMBAR; for(let r=0;r<4;r++) ctx.fillRect(69,166+r*6,32,4);
  ctx.fillStyle=P.SOMBRA_PROFUNDA; ctx.fillRect(78,190,14,4);
  // Fumigador (suelo izquierda)
  ctx.fillStyle=P.GRIS_JUBILADO; ctx.fillRect(20,240,24,16);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(22,242,20,12); ctx.fillRect(30,236,8,6);
  // Tarro vacío (suelo derecha)
  ctx.fillStyle=P.AZUL_HORA; ctx.globalAlpha=0.7; ctx.fillRect(130,252,18,20); ctx.globalAlpha=1;
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(132,252,14,4);
  // Olivo partido (izquierda)
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(6,148,20,95);
  ctx.fillStyle=P.OLIVO_OSCURO; ctx.fillRect(0,100,28,55); ctx.fillRect(8,88,20,18);
  ctx.fillStyle=P.SECANO_VERDE; ctx.fillRect(3,95,22,48);
  ctx.fillStyle=P.SOMBRA_PROFUNDA; ctx.fillRect(10,165,8,18); // oquedad
  // Hojas
  ctx.fillStyle=P.SECANO_VERDE;
  const leafOff=Math.round(sway*2);
  [[18,142],[52,144],[98,142],[144,143]].forEach(([lx,ly],i)=>{
    ctx.fillRect(lx+leafOff*(i%2===0?1:-1),ly,4,2); ctx.fillRect(lx+2+leafOff,ly-3,2,3);
  });
  ctx.fillStyle=P.HIERBA_POLVO;
  [[30,164],[68,162],[110,165]].forEach(([lx,ly],i)=>{ctx.fillRect(lx+leafOff*(i%2===0?-1:1),ly,5,2);});
  // Humo
  ctx.fillStyle=P.HUMO_AZUL;
  const smokeY=132-f*4;
  ctx.globalAlpha=0.38-f*0.07; ctx.fillRect(158,smokeY,8,6); ctx.fillRect(156,smokeY-7,10,6); ctx.fillRect(154,smokeY-14,12,6);
  ctx.globalAlpha=0.18-f*0.03; ctx.fillRect(152,smokeY-22,14,8);
  ctx.globalAlpha=1;
}
window.Art=window.Art||{}; window.Art.escena3=drawEscena3;
})();
