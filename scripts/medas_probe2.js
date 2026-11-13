const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('response', async r => { const u=r.url(); if(/zkau|clm10|medas/.test(u) && !/\.(png|css|woff2?)/.test(u)) console.log('RESP', r.status(), u.slice(0,110)); });
  p.on('requestfailed', r => console.log('FAIL', r.url().slice(0,110), r.failure()?.errorText));
  await p.goto('https://biruni.tuik.gov.tr/medas/?kn=84&locale=tr', { waitUntil:'domcontentloaded', timeout:120000 });
  for (let i=0;i<6;i++){ await p.waitForTimeout(10000);
    const t=(await p.innerText('body')).trim();
    console.log(`--- t=${(i+1)*10}s len=${t.length} ---`, t.slice(0,300).replace(/\n+/g,' | '));
    if(t.length>200) break;
  }
  await p.screenshot({ path:'/tmp/medas2.png', fullPage:true });
  await b.close();
})().catch(e=>{console.error('ERR',e.message);process.exit(1)});
