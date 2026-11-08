/* Local browser regression. Uses Playwright from NODE_PATH or a normal local installation.
   Starts an isolated Streamlit server and database; never touches the user's project DB. */
const {stageForPage, singlePageStages} = require('./full_be_navigation.cjs');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const {spawn, spawnSync} = require('node:child_process');
const {chromium} = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const folder = path.join(root, '.cache', `browser-state-${Date.now()}`);
  fs.mkdirSync(folder, {recursive:true});
  const port = process.env.BE_TEST_PORT ? Number(process.env.BE_TEST_PORT) : await new Promise((resolve,reject)=>{
    const probe=net.createServer(); probe.on('error',reject);
    probe.listen(0,'127.0.0.1',()=>{const available=probe.address().port; probe.close(()=>resolve(available));});
  });
  const python = process.env.BE_TEST_PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
  const server = spawn(python, ['-m','streamlit','run',path.join(root,'app.py'),'--server.port',String(port),
    '--server.headless','true','--server.fileWatcherType','none'], {
      cwd:root, windowsHide:true, env:{...process.env,
        BE_PROJECT_DATABASE:path.join(folder,'browser.sqlite'),
        PK_ANALYSIS_DATABASE:path.join(folder,'pk-analysis.sqlite')},
      stdio:['ignore','pipe','pipe']
    });
  let logs = '';
  server.stdout.on('data', b=>{logs+=b.toString();});
  server.stderr.on('data', b=>{logs+=b.toString();});
  let browser;
  let testPage;
  const proof = {scenario:'Streamlit browser state regression', checks:[]};
  try {
    let ready=false;
    for (let attempt=0; attempt<100; attempt++) {
      if(server.exitCode!==null) throw Error('Isolated test server exited: '+logs);
      try { if (logs.includes(`http://127.0.0.1:${port}`) && (await fetch(`http://127.0.0.1:${port}/_stcore/health`)).ok) {ready=true; break;} } catch {}
      await new Promise(resolve=>setTimeout(resolve,200));
    }
    if(!ready) throw Error('Isolated test server did not start; refusing to automate another server');
    browser = await chromium.launch({headless:true, channel:process.env.BE_BROWSER_CHANNEL || 'chrome'});
    const context = await browser.newContext({viewport:{width:1600,height:1100}, acceptDownloads:true});
    const page = await context.newPage();
    testPage = page;
    page.setDefaultTimeout(20000);
    await page.goto(`http://127.0.0.1:${port}`);
    const go = async label => {
      const stage = stageForPage(label);
      await page.getByTestId('stSidebar').getByText(stage,{exact:true}).click();
      if (!singlePageStages.has(stage)) {
        await page.getByTestId('stSidebar').getByText(label,{exact:true}).click();
      }
      await page.getByRole('heading',{name:label,exact:true}).waitFor();
      await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
    };
    const saved = () => {
      const code = "import json,sys; from be_app.persistence import ProjectStore; d=ProjectStore(sys.argv[1]); e=next(x for x in d.list_projects() if x['study_id']=='DEMO_2X2'); p=d.load(e['project_id']); r=p.runs[-1] if p.runs else None; print(json.dumps(dict(pending=p.pending_edits, planning=p.planning_inputs, input_revision=p.input_revision, input_fingerprint=p.input_fingerprint, run=r)))";
      const result = spawnSync(python,['-c',code,path.join(folder,'browser.sqlite')],{cwd:root,encoding:'utf8',windowsHide:true,maxBuffer:32*1024*1024});
      if(result.status!==0) throw Error(result.stderr);
      return JSON.parse(result.stdout);
    };
    await page.getByTestId('stSidebar').getByText('BE đầy đủ',{exact:true}).click();
    await page.getByRole('button',{name:'Điền dữ liệu mẫu vào biểu mẫu nghiên cứu',exact:true}).click();
    await page.locator('input[value="DEMO_2X2"]').waitFor();
    const evidence = page.getByRole('textbox',{name:'Bằng chứng rà soát guideline / PSG và phạm vi sản phẩm',exact:true});
    await evidence.fill('Synthetic QA scenario: M13A IR 2x2, scope reviewed for this test.');
    await evidence.press('Tab');
    await page.getByText('Đã rà soát phạm vi và yêu cầu riêng của sản phẩm',{exact:true}).click();
    await page.getByRole('button',{name:'Tạo nghiên cứu',exact:true}).click();
    await page.getByText('DEMO_2X2',{exact:false}).first().waitFor();
    await go('Ngẫu nhiên hóa và lịch lấy mẫu');
    await page.getByRole('button',{name:'Tạo danh sách phân nhóm',exact:true}).click();
    await page.getByRole('button',{name:'Chuẩn bị Excel phân nhóm và lịch lấy mẫu',exact:true}).waitFor();
    await go('Nhập dữ liệu nồng độ');
    await page.getByRole('button',{name:'Điền dữ liệu mẫu vào bảng nồng độ',exact:true}).click();
    await page.getByRole('button',{name:'Kiểm tra cấu trúc và QC',exact:true}).click();
    await page.getByRole('button',{name:'Nhập và lưu raw bất biến',exact:true}).click();
    await page.getByText(/Đã lưu dữ liệu gốc/).first().waitFor();
    await go('Thiết kế và cỡ mẫu BE');
    await page.getByRole('spinbutton',{name:'CV AUC (%)',exact:true}).fill('24.7');
    await page.getByRole('spinbutton',{name:'CV AUC (%)',exact:true}).press('Tab');
    await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
    await page.getByRole('spinbutton',{name:'GMR dự kiến AUC (T/R)',exact:true}).fill('0.93');
    await page.getByRole('spinbutton',{name:'GMR dự kiến AUC (T/R)',exact:true}).press('Tab');
    await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
    await go('Phân tích NCA');
    await go('Thiết kế và cỡ mẫu BE');
    for (const [label, value] of [['CV AUC (%)',24.7],['GMR dự kiến AUC (T/R)',.93]]) {
      const field = page.getByRole('spinbutton',{name:label,exact:true});
      await field.waitFor();
      await page.waitForFunction(([el,expected]) => Number(el.value.replace(',','.'))===expected,
        [await field.elementHandle(),value]);
    }
    proof.checks.push('CV=24.7 / GMR=.93 survive page navigation');
    await go('Kiểm soát chất lượng (QC)');
    await page.getByText('Editor theo sample_id cố định', {exact:false}).waitFor();
    const period = page.getByRole('combobox',{name:'Kỳ cần sửa',exact:true});
    await period.focus();
    await period.press('ArrowDown');
    await period.press('End');
    await period.press('Enter');
    const editor = page.locator('[data-testid="stDataFrame"]').first();
    await editor.locator('canvas').first().waitFor({state:'visible'});
    fs.writeFileSync(path.join(folder,'editor-dom.txt'), await page.locator('body').innerText());
    await page.screenshot({path:path.join(folder,'editor.png'),fullPage:true});
    const cells = await page.getByRole('gridcell').count();
    console.log('Grid cells:', cells);
    console.log('Grid text:', await editor.innerText());
    console.log('Frame bounds:', await editor.boundingBox());
    const edits = [[3,'333.7'],[4,'225.4'],[5,'331.9']];
    const editCell = async (row,value) => {
      await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
      await editor.locator('.dvn-scroller').first().dblclick({position:{x:170,y:36+35*row+17}});
      const input=page.locator('textarea.gdg-input');
      try { await input.waitFor({state:'visible',timeout:1500}); }
      catch { await page.keyboard.press('Enter'); await input.waitFor({state:'visible'}); }
      await input.fill(value);
      await input.press('Enter');
      await input.waitFor({state:'hidden'});
    };
    for (const [row,value] of edits) {
      await editCell(row,value);
      await page.getByText(new RegExp(`Chưa áp dụng: ${edits.findIndex(e=>e[0]===row)+1} mẫu`)).waitFor();
    }
    const before = saved();
    if(Object.keys(before.pending).length!==3 || !Object.keys(before.pending).every(id=>id.includes('_P2_'))) throw Error('Editor wrote wrong subject/period/row');
    proof.checks.push('Three real canvas edits persisted by stable sample_id in subject S0001 period 2');
    await go('Phân tích NCA');
    if(!await page.getByRole('button',{name:'Phân tích NCA và BE',exact:true}).isDisabled()) throw Error('Pending data permitted analysis');
    await go('Kiểm soát chất lượng (QC)');
    await editor.locator('canvas').first().waitFor({state:'visible'});
    if(JSON.stringify(saved().pending)!==JSON.stringify(before.pending)) throw Error('Edits lost on navigation');
    await page.screenshot({path:path.join(folder,'editor-pending-restored.png'),fullPage:true});
    for(const [name,value] of [['Lý do correction','Browser regression assay correction'],['Người rà soát độc lập','QA-browser'],['Tham chiếu bằng chứng correction','LAB-browser-003']]) {
      const field=page.getByRole('textbox',{name,exact:true}); await field.fill(value); await field.press('Tab');
    }
    await page.getByRole('button',{name:'Áp dụng các sửa đổi',exact:true}).click();
    await page.getByText('Chưa áp dụng: 3 mẫu',{exact:false}).waitFor({state:'hidden'});
    await page.getByRole('button',{name:'Data Freeze và khóa SAP',exact:true}).click();
    await page.getByText('Dữ liệu đã khóa.',{exact:false}).waitFor();
    await go('Phân tích NCA');
    await page.getByRole('button',{name:'Phân tích NCA và BE',exact:true}).click();
    await page.getByText('Kết quả hiện hành của đầu vào đã xác nhận.',{exact:true}).waitFor();
    const calculated=saved();
    for(const [id,patch] of Object.entries(before.pending)) {
      const input=calculated.run.validated_data.find(row=>row.sample_id===id);
      if(input.concentration!==Number(patch.concentration)) throw Error('Calculation input differs from edited cell');
    }
    proof.checks.push('Actual NCA/BE snapshot uses the three corrected concentrations');
    await go('Báo cáo CTD / Xuất dữ liệu');
    await page.getByRole('button',{name:'Chuẩn bị datasets và manifest',exact:true}).click();
    const downloadPromise=page.waitForEvent('download');
    await page.getByRole('button',{name:'Tải input_manifest.json',exact:true}).click();
    const download=await downloadPromise;
    const manifestPath=path.join(folder,'input_manifest.json'); await download.saveAs(manifestPath);
    const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
    if(manifest.input_fingerprint!==calculated.input_fingerprint || manifest.input_revision!==calculated.input_revision) throw Error('Report manifest differs from UI/canonical snapshot');
    proof.checks.push('Downloaded report manifest matches canonical state and calculation revision/fingerprint');
    await go('Kiểm soát chất lượng (QC)');
    await page.getByRole('button',{name:'Tạo revision để sửa dữ liệu',exact:true}).click();
    await page.getByRole('button',{name:'Tạo revision để sửa dữ liệu',exact:true}).waitFor({state:'hidden'});
    await editor.locator('canvas').first().waitFor({state:'visible'});
    await editCell(3,'444.8');
    await page.getByText(/Chưa áp dụng: 1 mẫu/).waitFor();
    await go('Thống kê BE — EMA / FDA');
    await page.getByText('Kết luận hiện hành: cần tính lại',{exact:true}).waitFor();
    await go('Báo cáo CTD / Xuất dữ liệu');
    if(!await page.getByRole('button',{name:'Tạo Word và PDF dự thảo',exact:true}).isDisabled()) throw Error('Stale report permitted');
    proof.checks.push('Stale results are labeled and Word/PDF export disabled');
    const pendingBeforeReload=saved().pending;
    await page.reload();
    await page.getByRole('button',{name:'Mở nghiên cứu đã lưu',exact:true}).waitFor();
    await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
    await page.getByRole('combobox',{name:'Nghiên cứu đã lưu',exact:true}).click();
    await page.getByRole('combobox',{name:'Nghiên cứu đã lưu',exact:true}).press('ArrowDown');
    await page.getByRole('option',{name:/DEMO_2X2/}).click();
    await page.getByTestId('stStatusWidget').waitFor({state:'hidden'});
    await page.getByRole('button',{name:'Mở nghiên cứu đã lưu',exact:true}).click();
    await page.getByTestId('stSidebar').getByText(/DEMO_2X2/).waitFor();
    await go('Kiểm soát chất lượng (QC)');
    await page.getByText(/Chưa áp dụng: 1 mẫu/).waitFor();
    if(JSON.stringify(saved().pending)!==JSON.stringify(pendingBeforeReload)) throw Error('Draft lost after browser reload');
    proof.checks.push('Browser reload + explicit project reopen restores durable pending edits');
    await page.screenshot({path:path.join(folder,'final-restored.png'),fullPage:true});
    proof.passed=true;
    console.log(JSON.stringify({folder,...proof}));
  } catch(error) {
    proof.passed=false; proof.error=String(error);
    if(testPage) {
      await testPage.screenshot({path:path.join(folder,'failure.png'),fullPage:true}).catch(()=>{});
      fs.writeFileSync(path.join(folder,'failure-dom.txt'),await testPage.locator('body').innerText().catch(()=>''));
    }
    fs.writeFileSync(path.join(folder,'server.log'), logs);
    console.error(error);
    process.exitCode=1;
  } finally {
    fs.writeFileSync(path.join(folder,'proof.json'),JSON.stringify(proof,null,2));
    if (browser) await browser.close();
    server.kill();
  }
})();
