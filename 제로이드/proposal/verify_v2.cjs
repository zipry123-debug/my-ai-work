const {chromium} = require('C:/Users/김우진/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const {pathToFileURL}=require('url');
(async()=>{
  const qa=path.join(__dirname,'qa_v2'); fs.mkdirSync(qa,{recursive:true});
  const executablePath = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(fs.existsSync);
  const browser=await chromium.launch({executablePath,headless:true});
  const result=[];
  for(const width of [1280,760,390]){
    const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    await page.goto(pathToFileURL(path.join(__dirname,'제로이드_무신사뷰티_성수팝업_제안서.html')).href);
    await page.evaluate(()=>document.fonts.ready); await page.waitForTimeout(900);
    await page.screenshot({path:path.join(qa,`page-${width}.png`),fullPage:true});
    for(const section of ['why','popup','risk','next']) await page.locator('#'+section).screenshot({path:path.join(qa,`${section}-${width}.png`)});
    const state=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&e.getBoundingClientRect().width>0).slice(-15).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,45),right:e.getBoundingClientRect().right})),sections:[...document.querySelectorAll('main>section')].map(s=>s.id),brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,branches:document.querySelectorAll('.outcome-branches>div').length,lastLine:getComputedStyle(document.querySelector('.timeline li:last-child'),'::after').content}));
    state.visibleOverflow=await page.evaluate(()=>[...document.querySelectorAll('main *')].filter(e=>e.checkVisibility()&&!e.closest('details:not([open])')&&e.getBoundingClientRect().right>innerWidth+.5).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,50),right:e.getBoundingClientRect().right})).slice(0,12));
    result.push({...state,errors});
    await page.close();
  }
  fs.writeFileSync(path.join(qa,'verification.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
