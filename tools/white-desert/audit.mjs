import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
import pixelmatch from 'pixelmatch';
import {PNG} from 'pngjs';
const dir='audit-output';await fs.mkdir(dir,{recursive:true});
const pages=[['original','https://white-desert.com/'],['clone','https://white-desert-fidelity-study-v2.vercel.app/']];
const sizes=[['desktop',1440,900],['tablet',834,1112],['mobile',390,844]],stops=[0,.1,.25,.5,.75,1];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const result=[];
for(const [device,width,height] of sizes){
 const ctx=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,reducedMotion:'reduce',isMobile:device==='mobile'});
 for(const [site,url] of pages){
  const tab=await ctx.newPage(),network=[],errors=[];
  tab.on('response',r=>{if(['media','image','font','stylesheet'].includes(r.request().resourceType()))network.push({type:r.request().resourceType(),url:r.url(),status:r.status()})});
  tab.on('pageerror',e=>errors.push(String(e)));
  const stem=device+'-'+site;
  try{
   const res=await tab.goto(url,{waitUntil:'domcontentloaded',timeout:55000});await sleep(4500);
   const nodes=await tab.evaluate(()=>{const names=['h1','h2','nav','header','section','video','canvas'];return Object.fromEntries(names.map(name=>[name,[...document.querySelectorAll(name)].slice(0,24).map(el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return {text:(el.textContent||'').trim().slice(0,120),font:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,letterSpacing:s.letterSpacing,opacity:s.opacity,position:s.position,width:Math.round(r.width),height:Math.round(r.height),x:Math.round(r.x),y:Math.round(r.y)}})]))});
   await fs.writeFile(path.join(dir,stem+'-source.json'),JSON.stringify({url,httpStatus:res?.status(),title:await tab.title(),network,errors,nodes},null,2));
   for(let i=0;i<stops.length;i++){await tab.evaluate(p=>window.scrollTo(0,Math.round((document.documentElement.scrollHeight-innerHeight)*p)),stops[i]);await sleep(1500);await tab.screenshot({path:path.join(dir,stem+'-'+i+'.png'),fullPage:false,timeout:30000})}
   console.log('CAPTURE',stem,'HTTP',res?.status(),'assets',network.length);
  }catch(e){console.error('ERROR',stem,e.message);result.push({device,site,error:e.message});await fs.writeFile(path.join(dir,stem+'-error.txt'),String(e))}
  await tab.close();
 }
 await ctx.close();
 for(let i=0;i<stops.length;i++)try{
  const a=PNG.sync.read(await fs.readFile(path.join(dir,device+'-original-'+i+'.png')));
  const b=PNG.sync.read(await fs.readFile(path.join(dir,device+'-clone-'+i+'.png')));
  if(a.width!==b.width||a.height!==b.height)throw new Error('Screenshot dimensions differed');
  const diff=new PNG({width:a.width,height:a.height});
  const bad=pixelmatch(a.data,b.data,diff.data,a.width,a.height,{threshold:.14,includeAA:true});
  await fs.writeFile(path.join(dir,device+'-diff-'+i+'.png'),PNG.sync.write(diff));
  result.push({device,scrollPercent:Math.round(stops[i]*100),differencePercent:Number((100*bad/(a.width*a.height)).toFixed(2))});
 }catch(e){result.push({device,scrollPercent:Math.round(stops[i]*100),error:String(e)})}
}
await browser.close();
const text=['# White Desert measured visual comparison','','Source: https://white-desert.com/','Clone: https://white-desert-fidelity-study-v2.vercel.app/','','Note: The same scroll percentages can represent different content because page heights differ. These scores are diagnostics, not a fidelity certification.','','| Device | Scroll | Difference |','|---|---:|---:|'];
for(const r of result)text.push('| '+r.device+' | '+(r.scrollPercent??'?')+'% | '+(r.differencePercent??r.error??'error')+' |');
await fs.writeFile(path.join(dir,'REPORT.md'),text.join('\n'));await fs.writeFile(path.join(dir,'summary.json'),JSON.stringify(result,null,2));console.log(text.join('\n'));
