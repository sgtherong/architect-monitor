import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(fs.readFileSync(process.argv[2]||0,'utf8'));
const ids=new Set(JSON.parse(fs.readFileSync(path.join(root,'data/targets.json'),'utf8')).map(t=>t.id));
const fields={items:['key','videoId','kind','collectedAt','publishedAt','novelty','sentiment','direction','summary_ko','note','url','authorRole','sample'],checks:['key','videoId','kind','day','checkedAt','status','fetched','firstObserved','analyzed','excluded','hasMore','method','note']};
const out={schemaVersion:1,publishedAt:new Date().toISOString(),baseline:{reviewedAt:'2026-10-13',videos:7,chatMessages:1844,sample:258,evidence:79}};
for(const type of ['items','checks']){
 const seen=new Set();out[type]=(data[type]||[]).map(r=>{if(!ids.has(r.videoId))throw Error('Unexpected video');if(!/^[a-f0-9]{64}$/.test(r.key)||seen.has(r.key))throw Error('Invalid/duplicate key');seen.add(r.key);const date=type==='items'?r.collectedAt:r.checkedAt;if(Number.isNaN(Date.parse(date)))throw Error('Invalid date');if(type==='checks'&&new Date(Date.parse(date)+9*3600000).toISOString().slice(0,10)!==r.day)throw Error('KST date mismatch');if(type==='items'){const u=new URL(r.url);if(!['www.youtube.com','youtube.com','www.facebook.com','facebook.com'].includes(u.hostname)||!(u.searchParams.get('v')===r.videoId||u.pathname.split('/').includes(r.videoId)))throw Error('Wrong evidence URL');}return Object.fromEntries(fields[type].map(k=>[k,r[k]??null]));}).sort((a,b)=>(a.collectedAt||a.checkedAt).localeCompare(b.collectedAt||b.checkedAt)||a.key.localeCompare(b.key));
}
const output=path.join(root,'docs/data/reactions.json');fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({output,items:out.items.length,checks:out.checks.length}));
