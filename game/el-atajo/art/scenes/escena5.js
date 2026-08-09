/* ESCENA 5 — Sótano del Registro (browser) */
(function(){
'use strict';
const P=window.P;
function drawEscena5(ctx,t){
  const W=180,H=320,f=Math.floor(t/400)%4,flicker=0.90+0.10*Math.sin(t/250);
  ctx.fillStyle=P.CIELO_TORMENTA; ctx.fillRect(0,0,W,H);
  ctx.fillStyle=P.PIEDRA_OSCURA; ctx.fillRect(0,0,W,32);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(88,0,4,26);
  ctx.fillStyle=P.SOL_BAJO; ctx.globalAlpha=flicker; ctx.fillRect(83,25,14,12);
  ctx.fillStyle=P.PONIENTE_NARANJA; ctx.fillRect(86,27,8,8); ctx.globalAlpha=1;
  ctx.fillStyle=P.MIEL_AMBAR; ctx.globalAlpha=0.16*flicker; ctx.fillRect(58,22,64,90);
  ctx.globalAlpha=0.08*flicker; ctx.fillRect(40,22,100,140); ctx.globalAlpha=1;
  for(let my=32;my<265;my+=20){
    ctx.fillStyle=P.PIEDRA_OSCURA;
    for(let mx=0;mx<W;mx+=36) ctx.fillRect(mx,my,34,18);
    ctx.fillStyle=P.AZUL_HORA; ctx.fillRect(0,my+18,W,2);
  }
  ctx.fillStyle=P.TERGAL_MARRON;
  ctx.fillRect(0,58,62,5); ctx.fillRect(0,108,62,5); ctx.fillRect(0,158,62,5);
  ctx.fillRect(0,58,5,105); ctx.fillRect(57,58,5,105);
  [[7,65],[22,65],[38,65],[7,115],[22,115]].forEach(([bx,by])=>{
    ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(bx,by,20,40);
    ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(bx+2,by+2,16,36);
    ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(bx+3,by+8,14,2); ctx.fillRect(bx+3,by+14,10,1); ctx.fillRect(bx+3,by+18,12,1);
  });
  ctx.fillStyle=P.TERGAL_MARRON;
  ctx.fillRect(118,58,62,5); ctx.fillRect(118,118,62,5); ctx.fillRect(118,58,5,65); ctx.fillRect(175,58,5,65);
  [122,136,150,164].forEach(lx=>{
    ctx.fillStyle=P.PAJA_VIEJA; ctx.fillRect(lx,65,10,52);
    ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(lx+1,68,8,1); ctx.fillRect(lx+1,76,8,1); ctx.fillRect(lx+1,84,8,1);
    ctx.fillStyle=P.LACRE_ESCARLATA; ctx.fillRect(lx+3,65,4,52);
    ctx.globalAlpha=0.6; ctx.fillRect(lx,88,10,3); ctx.globalAlpha=1;
  });
  ctx.fillStyle=P.TERGAL_MARRON; ctx.fillRect(68,85,48,4);
  [72,82,92,102].forEach(tx=>{
    ctx.fillStyle=P.AZUL_HORA; ctx.globalAlpha=0.6; ctx.fillRect(tx,72,8,14); ctx.globalAlpha=1;
    ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(tx+1,72,6,3);
  });
  // Escritorio Pura (derecha baja)
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(110,175,68,50);
  ctx.fillStyle=P.BARRO_TOSTADO; ctx.fillRect(112,177,64,46);
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.fillRect(115,180,30,2); ctx.fillRect(115,185,20,1); ctx.fillRect(115,189,25,1);
  ctx.fillStyle=P.LACRE_ESCARLATA; ctx.fillRect(150,180,8,6);
  // Campanilla (centro estantería)
  ctx.fillStyle=P.GRIS_JUBILADO; ctx.fillRect(75,68,28,22);
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(77,70,24,18);
  ctx.fillStyle=P.SOL_BAJO; ctx.fillRect(85,72,8,12);
  ctx.fillStyle=P.PIEDRA_OSCURA; ctx.fillRect(0,265,W,55);
  ctx.fillStyle=P.AZUL_HORA; ctx.fillRect(0,265,W,4);
  ctx.fillStyle=P.HUMO_AZUL; ctx.globalAlpha=0.45; ctx.fillRect(0,288,W,10); ctx.globalAlpha=1;
  ctx.fillStyle=P.SOMBRA_PROFUNDA; ctx.fillRect(20,272,30,1); ctx.fillRect(100,280,40,1);
  // Sal umbral
  ctx.fillStyle=P.PIEDRA_CALIZA; ctx.globalAlpha=0.5; ctx.fillRect(55,290,70,5); ctx.globalAlpha=1;
  // Polvo en luz
  ctx.fillStyle=P.SOL_BAJO;
  for(let d=0;d<6;d++){
    const dx=72+(d*8+f*5)%36, dy=38+d*35+(f*7)%20;
    ctx.globalAlpha=0.20-d*0.02; ctx.fillRect(dx,dy,2,2);
  }
  ctx.globalAlpha=1;
  // Cucaracha
  const rx=20+f*20, ry=276;
  ctx.fillStyle=P.TIERRA_SECA; ctx.fillRect(rx,ry,9,4); ctx.fillRect(rx+2,ry-1,5,1);
  ctx.fillStyle=P.PIEDRA_OSCURA; ctx.fillRect(rx+7,ry-3,1,3); ctx.fillRect(rx+8,ry-3,1,3);
  ctx.fillStyle=P.SOMBRA_PROFUNDA;
  if(f%2===0){ctx.fillRect(rx+1,ry+4,1,2); ctx.fillRect(rx+4,ry+4,1,2); ctx.fillRect(rx+7,ry+4,1,2);}
  else{ctx.fillRect(rx,ry+3,1,2); ctx.fillRect(rx+3,ry+3,1,2); ctx.fillRect(rx+6,ry+3,1,2);}
}
window.Art=window.Art||{}; window.Art.escena5=drawEscena5;
})();
