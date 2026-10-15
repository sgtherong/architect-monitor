import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const input=JSON.parse(fs.readFileSync(process.argv[2]||0,'utf8'));
const targets=JSON.parse(fs.readFileSync(path.join(root,'data/targets.json'),'utf8'));
const ids=new Set(targets.map(t=>t.id));
const fields=['videoId','day','observedAt','views','likes','comments','reactions','source','precision','status','note'];
const keys=new Set();
const rows=input.rows.map(row=>{
 if(!ids.has(row.videoId))throw Error('Unexpected video ID');
 if(Number.isNaN(Date.parse(row.observedAt)))throw Error('Invalid observedAt');
 const kstDay=new Date(Date.parse(row.observedAt)+9*3600000).toISOString().slice(0,10);
 if(row.day!==kstDay)throw Error('Observation date must be KST');
 for(const key of ['views','likes','comments','reactions']){
  if(row[key]!==null&&(!Number.isSafeInteger(row[key])||row[key]<0))throw Error('Invalid count: '+key);
 }
 const key=row.videoId+'@'+row.observedAt;
 if(keys.has(key))throw Error('Duplicate observation');
 keys.add(key);
 return Object.fromEntries(fields.map(field=>[field,row[field]??(field==='note'?'':null)]));
}).sort((a,b)=>Date.parse(a.observedAt)-Date.parse(b.observedAt));
if(new Set(rows.map(r=>r.videoId)).size!==8)throw Error('All eight targets must be preserved');
const snapshot={schemaVersion:1,publishedAt:new Date().toISOString(),rows,config:{scheduleStatus:input.config?.scheduleStatus||'unknown',historyStatus:input.config?.historyStatus||'실제 확보한 날짜만 표시합니다. 미확인 날짜는 추정하지 않습니다.'},stored:true};
const output=path.join(root,'docs/data/observations.json');
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(snapshot,null,2)+'\n');
console.log(JSON.stringify({output,observations:rows.length,targets:ids.size,publishedAt:snapshot.publishedAt}));
