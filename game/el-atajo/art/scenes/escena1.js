/* ESCENA 1 — La Cañada Cerrada (browser) */
(function(){
'use strict';
const P = window.P;
function drawEscena1(ctx, t) {
  const W=180, H=320, f=Math.floor(t/400)%4;
  const sky=ctx.createLinearGradient(0,0,0,140);
  sky.addColorStop(0,P.CIELO_TORMENTA); sky.addColorStop(0.6,P.AZUL_HORA); sky.addColorStop(1,P.LAVANDA_TARDE);
  ctx.fillStyle=sky; ctx.fillRect(0,0,W,140);
  ctx.fillStyle=P.PONIENTE_NARANJA; ctx.fillRect(128,108,20,10);
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(132,110,12,6);
  ctx.fillStyle=P.PIEDRA_OSCURA;
  ctx.fillRect(0,60,52,260); ctx.fillRect(0,80,28,240);
  ctx.fillRect(140,55,40,265); ctx.fillRect(158,75,22,245);
  ctx.fillStyle=P.TIERRA_SECA;
  for(let i=0;i<8;i++){ctx.fillRect(6+i*4,92+i*16,7,3); ctx.fillRect(152+(i%3)*5,88+i*18,5,3);}
  ctx.fillStyle=P.OLIVO_OSCURO; ctx.fillRect(14,118,22,14); ctx.fillRect(146,112,20,12);
  ctx.fillStyle=P.SECANO_VERDE; ctx.fillRect(17,116,15,9); ctx.fillRect(149,110,14,8);
  ctx.fillStyle=P.HIERBA_POLVO; ctx.fillRect(20,128,6,4); ctx.fillRect(152,122,5,3);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(44,138,92,182);
  ctx.fillStyle=P.TIERRA_SECA;
  for(let i=0;i<7;i++) ctx.fillRect(52+i*11,175+i*18,9,3);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(42,138,4,182); ctx.fillRect(134,138,4,182);
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(65,195,8,4); ctx.fillRect(100,238,10,4); ctx.fillRect(72,278,6,3);
  // Cinta de precinto
  ctx.fillStyle=P.LACRE_ESCARLATA||'#c4202a';
  ctx.fillRect(44,148,92,4);
  ctx.fillRect(88,138,4,16);
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(84,134,12,8);
  // Pájaros
  ctx.fillStyle=P.PIEDRA_OSCURA;
  [[28,38],[58,28],[88,44]].forEach(([bx,by],i)=>{
    const ox=(f+i)%2===0?0:2, oy=(f+i)%3===0?0:-1;
    ctx.fillRect(bx+ox,by+oy,2,1); ctx.fillRect(bx+ox+2,by+oy-1,2,1); ctx.fillRect(bx+ox+4,by+oy,2,1);
  });
  // Polvo
  ctx.fillStyle=P.HUMO_AZUL; ctx.globalAlpha=0.22+0.1*Math.sin(t/600);
  ctx.fillRect(52,286+f*2,76,6); ctx.fillRect(62,296+f*2,56,4);
  ctx.globalAlpha=1;
}
window.Art = window.Art||{}; window.Art.escena1 = drawEscena1;
})();
