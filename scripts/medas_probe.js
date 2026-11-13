const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const reqs = [];
  p.on('request', r => { const u=r.url(); if(!/\.(png|jpg|gif|css|woff2?|svg)/.test(u)) reqs.push(r.method()+' '+u.slice(0,160)); });
  await p.goto('https://biruni.tuik.gov.tr/medas/?kn=84&locale=tr', { waitUntil:'networkidle', timeout:120000 });
  await p.waitForTimeout(5000);
  console.log('TITLE:', await p.title());
  const txt = (await p.innerText('body')).replace(/\n{2,}/g,'\n').slice(0, 2500);
  console.log('--- BODY ---\n'+txt);
  console.log('--- REQS ---\n'+[...new Set(reqs)].slice(0,25).join('\n'));
  await p.screenshot({ path:'/tmp/medas.png', fullPage:false });
  await b.close();
})().catch(e=>{console.error('ERR',e.message);process.exit(1)});
