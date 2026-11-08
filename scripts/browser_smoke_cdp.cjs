/* Browser smoke regression using only Node's built-in WebSocket and local Chrome.
 * Point BE_SMOKE_URL at an isolated Streamlit server/database; no user data is changed.
 */
const {stageForPage, singlePageStages} = require('./full_be_navigation.cjs');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');

const root = path.resolve(__dirname, '..');
const folder = path.join(root, '.cache', 'browser-cdp-smoke');
const target = process.env.BE_SMOKE_URL || 'http://127.0.0.1:18511';
const chromePath = process.env.BE_CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
fs.mkdirSync(folder, {recursive: true});
// A separate profile prevents stale debugging ports and existing Chrome sessions
// from silently stealing a new smoke-test invocation.
const profile = fs.mkdtempSync(path.join(folder,'chrome-session-'));

const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const until = async (fn, attempts=80, delay=250) => {
  for (let i=0; i<attempts; i++) {
    const value = await Promise.resolve().then(fn).catch(() => null);
    if (value) return value;
    await sleep(delay);
  }
  throw Error('Timed out waiting for Chrome or Streamlit');
};

class DevTools {
  constructor(ws) {
    this.ws=ws; this.id=0; this.waiters=new Map();
    ws.addEventListener('message', event => {
      const message=JSON.parse(event.data);
      const waiter=this.waiters.get(message.id);
      if (!waiter) return;
      this.waiters.delete(message.id);
      if(message.error) waiter.reject(Error(JSON.stringify(message.error)));
      else waiter.resolve(message.result);
    });
  }
  send(method, params={}) {
    const id=++this.id;
    return new Promise((resolve,reject) => {
      this.waiters.set(id,{resolve,reject});
      this.ws.send(JSON.stringify({id,method,params}));
    });
  }
  async evaluate(expression) {
    const response=await this.send('Runtime.evaluate', {expression,returnByValue:true,awaitPromise:true});
    if(response.exceptionDetails) throw Error(JSON.stringify(response.exceptionDetails));
    return response.result.value;
  }
  async screenshot(filename) {
    const capture=await this.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    fs.writeFileSync(path.join(folder,filename),Buffer.from(capture.data,'base64'));
  }
}

(async () => {
  const chrome=spawn(chromePath, [
    '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
    '--disable-background-networking','--remote-allow-origins=*',
    '--remote-debugging-port=0','--user-data-dir='+profile,'about:blank',
  ],{windowsHide:true,stdio:'ignore'});
  let ws,client;
  const proof={target,checks:[],stage:'Chrome startup'};
  try {
    const portInfo=await until(() => {
      const p=path.join(profile,'DevToolsActivePort');
      return fs.existsSync(p) ? fs.readFileSync(p,'utf8').split(/\r?\n/)[0] : null;
    });
    const pages=await until(async () => {
      const response=await fetch('http://127.0.0.1:'+portInfo+'/json/list');
      const items=await response.json();
      return items.find(item=>item.type==='page');
    });
    ws=new WebSocket(pages.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{
      ws.addEventListener('open',resolve,{once:true});
      ws.addEventListener('error',reject,{once:true});
    });
    const c=new DevTools(ws);
    client=c;
    await c.send('Page.enable');
    await c.send('Runtime.enable');
    await c.send('Emulation.setDeviceMetricsOverride', {width:1440,height:950,deviceScaleFactor:1,mobile:false});
    proof.stage='Streamlit home';
    await c.send('Page.navigate',{url:target});
    const body=await until(async()=>{
      const value=await c.evaluate('document.body.innerText');
      return value.includes('Luồng phân tích')?value:null;
    },120,250);
    proof.checks.push('Streamlit home rendered and demo project creation is accessible');
    proof.firstBody=body.slice(0,2200);
    await c.screenshot('home-1440.png');
    await c.send('Emulation.setDeviceMetricsOverride',{width:714,height:950,deviceScaleFactor:1,mobile:false});
    await sleep(500);
    await c.screenshot('home-714.png');
    proof.checks.push('Both 1440px and 714px viewport captures saved after render');
    const workflowSelected=await c.evaluate(`(()=>{const sidebar=document.querySelector('[data-testid="stSidebar"]');const option=Array.from(sidebar?.querySelectorAll('label')||[]).find(x=>x.innerText.trim()==='BE đầy đủ');if(!option)return false;option.click();return true;})()`);
    if(!workflowSelected) throw Error('BE workflow selector missing from DOM');
    await until(async()=> (await c.evaluate('document.body.innerText')).includes('Điền dữ liệu mẫu vào biểu mẫu nghiên cứu'));
    const filled=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.includes('Điền dữ liệu mẫu vào biểu mẫu nghiên cứu'));if(!b)return false;b.click();return true;})()`);
    if(!filled) throw Error('Demo form load button missing');
    await until(async()=> c.evaluate('Array.from(document.querySelectorAll("input")).some(e=>e.value==="DEMO_2X2")'));
    const evidenceSelector = 'textarea[aria-label="Bằng chứng rà soát guideline / PSG và phạm vi sản phẩm"]';
    const settle = async () => {
      await sleep(350);
      await until(async()=>c.evaluate("!document.querySelector('[data-testid=stStatusWidget]')?.offsetHeight"));
    };
    await settle();
    await c.evaluate(`document.querySelector(${JSON.stringify(evidenceSelector)}).focus()`);
    await c.send('Input.insertText',{text:'Synthetic QA scope review for IR 2x2.'});
    await c.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',windowsVirtualKeyCode:9});
    await c.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',windowsVirtualKeyCode:9});
    await settle();
    await c.evaluate(`Array.from(document.querySelectorAll('label')).find(e=>e.innerText.trim()==='Đã rà soát phạm vi và yêu cầu riêng của sản phẩm').click()`);
    await settle();
    const clicked=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Tạo nghiên cứu');if(!b)return false;b.click();return true;})()`);
    if(!clicked) throw Error('Create study button missing from DOM');
    const after=await until(async()=>{
      const value=await c.evaluate('document.body.innerText');
      const main=await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText || ""');
      return value.includes('DEMO_2X2') && main.includes('Tiến độ quy trình nghiên cứu')?value:null;
    },120,250);
    proof.checks.push('Created DEMO_2X2 through the public study form');
    proof.afterCreateBody=after.slice(0,2500);
    await c.screenshot('demo-created-714.png');
    const width=await c.evaluate('({body:document.body.scrollWidth,viewport:innerWidth})');
    if(width.body > width.viewport + 1) throw Error('Horizontal page overflow at 714px: '+JSON.stringify(width));
    proof.checks.push('No document-level horizontal overflow at 714px');
    await c.send('Emulation.setDeviceMetricsOverride',{width:1440,height:950,deviceScaleFactor:1,mobile:false});
    await sleep(300);
    const navigate=async (label, expected) => {
      const stage = stageForPage(label);
      for (const option of singlePageStages.has(stage) ? [stage] : [stage, label]) {
        await until(async()=>c.evaluate(`(()=>{const sidebar=document.querySelector('[data-testid="stSidebar"]');const el=Array.from(sidebar?.querySelectorAll('label')||[]).find(x=>x.innerText.trim()===${JSON.stringify(option)});if(el)el.click();return !!el;})()`));
      }
      await until(async()=>{
        const main=await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText || ""');
        return main.includes(expected);
      },120,250);
      proof.checks.push('Sidebar navigation to '+label);
    };
    proof.stage='Prepare synthetic study';
    await navigate('Ngẫu nhiên hóa và lịch lấy mẫu','Tạo danh sách phân nhóm');
    const allocated=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Tạo danh sách phân nhóm');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!allocated) throw Error('Randomization action unavailable');
    await until(async()=> (await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText||""')).includes('Chuẩn bị Excel phân nhóm và lịch lấy mẫu'));
    await navigate('Nhập dữ liệu nồng độ','Điền dữ liệu mẫu vào bảng nồng độ');
    const stage=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Điền dữ liệu mẫu vào bảng nồng độ');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!stage) throw Error('Synthetic concentration load unavailable');
    await until(async()=> c.evaluate(`Array.from(document.querySelectorAll('button')).some(b=>b.innerText.trim()==='Kiểm tra cấu trúc và QC' && !b.disabled)`));
    const preflight=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Kiểm tra cấu trúc và QC');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!preflight) throw Error('Preflight action unavailable');
    await until(async()=> c.evaluate(`Array.from(document.querySelectorAll('button')).some(b=>b.innerText.trim()==='Nhập và lưu raw bất biến' && !b.disabled)`));
    const imported=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Nhập và lưu raw bất biến');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!imported) throw Error('Raw import unavailable after preflight');
    await until(async()=> (await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText||""')).includes('Đã lưu dữ liệu gốc'));
    proof.checks.push('Randomization, concentration preflight, and immutable raw import succeeded');
    proof.stage='Design navigation';
    await navigate('Thiết kế và cỡ mẫu BE','CV AUC (%)');
    await c.screenshot('design-1440.png');
    proof.stage='QC freeze';
    await navigate('Kiểm soát chất lượng (QC)','Data Freeze và khóa SAP');
    const froze=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Data Freeze và khóa SAP');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!froze) throw Error('Data Freeze action unavailable on synthetic study');
    await until(async()=>{
      const sidebar=await c.evaluate('document.querySelector("[data-testid=stSidebar]")?.innerText || ""');
      return sidebar.includes('Đã khóa');
    },120,250);
    proof.checks.push('Data Freeze triggered in browser');
    proof.stage='NCA calculation';
    await navigate('Phân tích NCA','Phân tích NCA và BE');
    const calculated=await c.evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Phân tích NCA và BE');if(!b || b.disabled)return false;b.click();return true;})()`);
    if(!calculated) throw Error('NCA/BE button unavailable after freeze');
    await until(async()=>{
      const main=await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText || ""');
      return main.includes('Kết quả hiện hành của đầu vào đã xác nhận.') && main.includes('Input r2 · dữ liệu r2');
    },180,250);
    proof.checks.push('NCA/BE analysis created a current revision-2 snapshot');
    await c.screenshot('nca-analyzed-1440.png');
    proof.stage='BE study decision';
    await navigate('Thống kê BE — EMA / FDA','Kết quả BE của nghiên cứu đã lưu');
    const studyDecision=await until(async()=>{
      const main=await c.evaluate('document.querySelector("[data-testid=stMain]")?.innerText || ""');
      return main.includes('Không thể kết luận') && main.includes('DỮ LIỆU GIẢ LẬP PHỤC VỤ HỌC THỬ') ? 'NOT EVALUABLE (demo/QA)' : null;
    },120,250);
    proof.studyDecision=studyDecision;
    proof.checks.push('Study decision remains NOT EVALUABLE for synthetic QA data after analysis');
    await c.screenshot('be-gated-1440.png');
    proof.stage='Report page';
    await navigate('Báo cáo CTD / Xuất dữ liệu','Báo cáo DRAFT');
    proof.checks.push('Reports page visibly labels exports as drafts');
    await c.screenshot('reports-1440.png');
    proof.passed=true;
    proof.stage='Completed';
    fs.writeFileSync(path.join(folder,'proof.json'),JSON.stringify(proof,null,2));
    console.log(JSON.stringify(proof));
  } catch(err) {
    proof.passed=false; proof.error=String(err);
    if(client) {
      try {proof.errorBody=(await client.evaluate('document.body.innerText')).slice(0,800); await client.screenshot('error.png');} catch {}
    }
    fs.writeFileSync(path.join(folder,'proof.json'),JSON.stringify(proof,null,2));
    console.error(JSON.stringify(proof)); process.exitCode=1;
  } finally {
    if(ws) ws.close();
    chrome.kill();
  }
})().catch(err=>{console.error(err);process.exitCode=1});
