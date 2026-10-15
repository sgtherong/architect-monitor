"""Public, bounded collector for the exact targets. Never uses paid APIs or stored credentials.
Raw candidate text is transient input for analysis: DO NOT commit the output.
python scripts/collect-reactions.py --metrics metrics.json --state private-reactions.json --output raw.json
"""
import argparse,datetime,hashlib,html,json,re
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent.parent
TARGETS=json.loads((ROOT/'data/targets.json').read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def day(t):return (datetime.datetime.fromisoformat(t.replace('Z','+00:00'))+datetime.timedelta(hours=9)).date().isoformat()
def key(kind,vid,source_id):return hashlib.sha256((kind+'|'+vid+'|'+source_id).encode()).hexdigest()
def nodes(obj,name):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k==name:yield v
   yield from nodes(v,name)
 elif isinstance(obj,list):
  for v in obj:yield from nodes(v,name)
def text(v):return v if isinstance(v,str) else (v or {}).get('simpleText') or ''.join(r.get('text','') for r in (v or {}).get('runs',[]))
def config(s,k):
 m=re.search('"'+k+'"\\s*:\\s*',s);return json.JSONDecoder().raw_decode(s[m.end():])[0] if m else None
def fetch(url,data=None):
 req=Request(url,data=json.dumps(data).encode() if data is not None else None,headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/json','Origin':'https://www.youtube.com'} if 'youtube.com' in url else {'User-Agent':'Mozilla/5.0'})
 with urlopen(req,timeout=25) as r:return r.read().decode()
def initial(s,k):
 m=re.search(r'(?:var\s+)?'+k+r'\s*=\s*',s);return json.JSONDecoder().raw_decode(s[m.end():])[0] if m else {}
def check(vid,kind,status,fetched=None,first=None,analyzed=0,excluded=0,more=None,method='public',note='',at=None):
 at=at or now();return dict(key=key('check',vid,kind+'|'+at),videoId=vid,kind=kind,day=day(at),checkedAt=at,status=status,fetched=fetched,firstObserved=first,analyzed=analyzed,excluded=excluded,hasMore=more,method=method,note=note)
def collect(target,metrics,state):
 vid=target['id'];seen={r['key'] for r in state.get('seen',[])};out={'checks':[],'candidates':[],'seen':[]}
 previous=[c for c in state.get('checks',[]) if c['videoId']==vid and c['kind']=='comment' and c['status'] in ['complete','partial','count_zero']]
 previous_at=max((c['checkedAt'] for c in previous),default=None)
 latest=max((r for r in metrics.get('rows',[]) if r['videoId']==vid and r['status']!='unavailable'),key=lambda r:r['observedAt'],default=None)
 if target['platform']=='facebook':
  try:fetch(target['url']);note='공개 영상 페이지 확인. 이 수집 경로에서는 해당 영상의 댓글·채팅 원문을 검증하여 추출할 수 없습니다.'
  except Exception as e:note='공개 원문 접근 실패: '+str(e)[:150]
  for kind in ['comment','chat']:out['checks'].append(check(vid,kind,'unavailable',note=note))
  return out
 archived=any(c['videoId']==vid and c['kind']=='chat' and c['status'] in ['complete','archived'] and c['hasMore'] is False for c in state.get('checks',[]))
 if archived:out['checks'].append(check(vid,'chat','archived',method='종료 방송 기록 유지',note='종료된 방송의 확보된 채팅은 재집계하지 않습니다. 일반 댓글은 별도로 확인합니다.',more=False))
 zero=latest and latest['day']==day(now()) and latest['comments']==0
 if zero:out['checks'].append(check(vid,'comment','count_zero',fetched=0,first=0,more=False,method='현재 공개 댓글 수',note='원문 조회 생략: '+latest['observedAt']+' 관측 댓글 수 0. 방송 채팅 수와는 별개입니다.',at=latest['observedAt']))
 if zero and archived:return out
 try:
  page=fetch(target['url']);data=initial(page,'ytInitialData');player=initial(page,'ytInitialPlayerResponse');ctx=config(page,'INNERTUBE_CONTEXT');api_key=config(page,'INNERTUBE_API_KEY')
  if not ctx or not api_key:raise ValueError('공개 수집 컨텍스트 없음')
  owner=next((o.get('navigationEndpoint',{}).get('browseEndpoint',{}).get('browseId') for o in nodes(data,'videoOwnerRenderer')),None)
  def api(endpoint,token):return json.loads(fetch('https://www.youtube.com/youtubei/v1/'+endpoint+'?key='+api_key,{'context':ctx,'continuation':token}))
  if not zero:
   try:
    sec=next(s for s in nodes(data,'itemSectionRenderer') if s.get('targetId')=='comments-section');token=next(nodes(sec,'continuationCommand'))['token'];r=api('next',token)
    menus=list(nodes(r,'sortFilterSubMenuRenderer'));newest=next((x for m in menus for x in m.get('subMenuItems',[]) if any(w in x.get('title','').lower() for w in ['newest','최신','최근','ล่าสุด'])),None)
    if newest:r=api('next',next(nodes(newest,'continuationCommand'))['token'])
    collected=now();msgs=[]
    for c in nodes(r,'commentEntityPayload'):
     prop=c.get('properties',{});cid=prop.get('commentId');body=prop.get('content',{}).get('content');author=c.get('author',{}).get('channelId')
     if cid and body is not None:msgs.append(dict(sourceId=cid,text=body,kind='reply' if prop.get('replyLevel',0)>0 else 'comment',publishedAt=None,publishedLabel=prop.get('publishedTime'),isOwner=bool(author and owner and author==owner),ownerVerified=bool(author and owner)))
    # Only inspect continuations in comment result lists, never sort-menu tokens.
    lists=[v for k in ['appendContinuationItemsAction','reloadContinuationItemsCommand'] for v in nodes(r,k)]
    more=any(list(nodes(v.get('continuationItems',[]),'continuationItemRenderer')) for v in lists)
    unique={m['sourceId']:m for m in msgs};msgs=list(unique.values())[:100];fresh=0;excluded=0
    for m in msgs:
     k=key(m['kind'],vid,m['sourceId'])
     if k in seen:continue
     out['seen'].append(dict(key=k,videoId=vid,kind=m['kind'],firstSeenAt=collected));fresh+=1
     if m['isOwner']:excluded+=1;continue
     out['candidates'].append(dict(key=k,videoId=vid,kind=m['kind'],collectedAt=collected,publishedAt=m['publishedAt'],publishedLabel=m['publishedLabel'],novelty='first_observed',text=m['text'],authorRole='viewer_verified' if m['ownerVerified'] else 'unverified',url=target['url']+'&lc='+m['sourceId'],sample=True))
    # Empty extraction is not proof of no comments when reported count is positive.
    status='partial' if more or not newest or (not msgs and latest and (latest['comments'] or 0)>0) else 'complete'
    out['checks'].append(check(vid,'comment',status,len(msgs),fresh,excluded=excluded,more=more,method='공개 댓글 최신순' if newest else '공개 댓글 표시순',note='상대 작성일은 정확한 시각으로 환산하지 않습니다. '+('추가 페이지/답글은 미확인.' if more else '확보한 스레드 기준. 답글 전체 확보를 보장하지 않습니다.'),at=collected))
   except Exception as e:out['checks'].append(check(vid,'comment','unavailable',note='댓글 원문 추출 실패: '+str(e)[:150]))
  if not archived:
   try:
    live=next(nodes(data,'liveChatRenderer'));token=live['continuations'][0]['reloadContinuationData']['continuation'];r=api('live_chat/get_live_chat_replay',token)
    menus=list(nodes(r,'sortFilterSubMenuRenderer'));allchat=next((x for m in menus for x in m.get('subMenuItems',[]) if x.get('title') in ['실시간 채팅 다시보기','Live chat replay','แชทสดย้อนหลัง']),None)
    if allchat:token=allchat['continuation']['reloadContinuationData']['continuation']
    messages={};tokens=set();complete=False
    for page_no in range(40):
     if token in tokens:break
     tokens.add(token);r=api('live_chat/get_live_chat_replay',token);lc=r.get('continuationContents',{}).get('liveChatContinuation',{})
     for action in lc.get('actions',[]):
      replay=action.get('replayChatItemAction',{});offset=int(replay.get('videoOffsetTimeMsec') or 0)
      for typ in ['liveChatTextMessageRenderer','liveChatPaidMessageRenderer','liveChatMembershipItemRenderer']:
       for m in nodes(replay,typ):
        aid=m.get('authorExternalChannelId');published=datetime.datetime.fromtimestamp(int(m['timestampUsec'])/1000000,datetime.timezone.utc).isoformat() if m.get('timestampUsec') else None
        messages[m['id']]=dict(sourceId=m['id'],text=text(m.get('message') or m.get('headerSubtext')),offsetMs=offset,publishedAt=published,isOwner=bool(owner and aid==owner),ownerVerified=bool(owner and aid))
     cont=list(nodes(lc.get('continuations',[]),'liveChatReplayContinuationData'))
     if not cont:complete=bool(lc);break
     token=cont[0]['continuation']
    collected=now();fresh=[];excluded=0;fresh_count=0
    for m in sorted(messages.values(),key=lambda m:(m['offsetMs'],m['sourceId'])):
     k=key('chat',vid,m['sourceId'])
     if k in seen:continue
     out['seen'].append(dict(key=k,videoId=vid,kind='chat',firstSeenAt=collected));fresh_count+=1
     if m['isOwner'] or not m['text'].strip() or re.search(r'https?://',m['text']):excluded+=1;continue
     fresh.append(dict(key=k,videoId=vid,kind='chat',collectedAt=collected,publishedAt=m['publishedAt'],novelty='backfill',text=m['text'],authorRole='viewer_verified' if m['ownerVerified'] else 'unverified',url=target['url']+'&t='+str(max(0,m['offsetMs']//1000))+'s',sample=True))
    cap=min(40,len(fresh));selected=sorted({round(i*(len(fresh)-1)/max(1,cap-1)) for i in range(cap)})
    out['candidates'] += [fresh[n] for n in selected]
    out['checks'].append(check(vid,'chat','complete' if complete else 'partial',len(messages),fresh_count,excluded=excluded,more=not complete,method='종료 방송 전체 채팅 다시보기 · 균등 간격 최대 40건',note='오늘 작성된 반응이 아닌 종료 방송의 추가 확보분. 방송자·링크·빈 메시지를 표본에서 제외.',at=collected))
   except Exception as e:out['checks'].append(check(vid,'chat','unavailable',note='방송 채팅 원문 확보 실패: '+str(e)[:150]))
 except Exception as e:
  if not zero:out['checks'].append(check(vid,'comment','unavailable',note='공개 영상 접근 실패: '+str(e)[:150]))
  if not archived:out['checks'].append(check(vid,'chat','unavailable',note='공개 영상 접근 실패: '+str(e)[:150]))
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--metrics',required=True);ap.add_argument('--state',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();metrics=json.loads(Path(args.metrics).read_text());state=json.loads(Path(args.state).read_text())
 with ThreadPoolExecutor(max_workers=2) as ex:results=list(ex.map(lambda t:collect(t,metrics,state),TARGETS))
 batch={k:[v for r in results for v in r[k]] for k in ['checks','candidates','seen']};Path(args.output).write_text(json.dumps(batch,ensure_ascii=False,indent=2));print(json.dumps({'checks':len(batch['checks']),'candidates':len(batch['candidates']),'firstObserved':len(batch['seen'])}))
