import test,{after} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,rmSync} from 'node:fs'
import {fileURLToPath,pathToFileURL} from 'node:url'
import path from 'node:path'
import {buildSync} from 'esbuild'
import {createElement} from 'react'
import {renderToStaticMarkup} from 'react-dom/server'

const frontend=fileURLToPath(new URL('../',import.meta.url))
mkdirSync(path.join(frontend,'.tmp'),{recursive:true})
const temporary=mkdtempSync(path.join(frontend,'.tmp','research-test-'))
after(()=>rmSync(temporary,{recursive:true,force:true}))
buildSync({stdin:{contents:"export {default as ResearchTools,localRequest} from './src/ResearchTools'; export {I18nContext} from './src/i18n'; export {translate} from './src/translation'; export {parseProviderData,buildEvidence,matchupGuide} from './src/providerData'; export {matchingVersion,parseItemNames,itemImageUrl,dataDragonItems} from './src/dataDragon';",resolveDir:frontend},bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic',outfile:path.join(temporary,'tools.mjs')})
const {ResearchTools,localRequest,I18nContext,translate,parseProviderData,buildEvidence,matchupGuide,matchingVersion,parseItemNames,itemImageUrl,dataDragonItems}=await import(pathToFileURL(path.join(temporary,'tools.mjs')).href)
const render=language=>renderToStaticMarkup(createElement(I18nContext.Provider,{value:{language,locale:language==='ko'?'ko-KR':'en-US',setLanguage:()=>{},t:(text,values)=>translate(language,text,values),roleName:role=>role}},createElement(ResearchTools,{match:{id:'DEMO_0001',champion:'Ahri',champion_id:103,role:'MIDDLE',patch:'16.21.1'}})))

test('new research tools render in English and Korean, with honest defaults and consent gate',()=>{
 const english=render('en'),korean=render('ko')
 for(const text of ['Private behavior and peer notes','Own live stats and review prompts','Connect OP.GG','Peer report (unverified)','fewer than five','No enemy tracking'])assert.ok(english.includes(text),text)
 for(const text of ['비공개 행동','실시간 통계','OP.GG 연결','동료 의견 (미검증)','5개 미만','적 추적'])assert.ok(korean.includes(text),text)
 assert.match(english,/<button[^>]*disabled=""[^>]*>Save private note/)
 assert.ok(!english.includes('Connected to local game'))
 assert.ok(!english.includes('79%'))
})

test('local tool requests use the private marker and JSON body without credentials',async()=>{
 const original=globalThis.fetch
 try{
  globalThis.fetch=async(url,options)=>{assert.equal(url,'/api/private-feedback');assert.equal(options.headers['X-Lolai-Local'],'1');assert.equal(options.headers['Content-Type'],'application/json');assert.equal(options.headers.Authorization,undefined);return new Response('{"entries":[]}',{status:200,headers:{'Content-Type':'application/json'}})}
  assert.deepEqual(await localRequest('/api/private-feedback'),{entries:[]})
 }finally{globalThis.fetch=original}
})

test('old backend and rejected requests show actionable errors',async()=>{
 const original=globalThis.fetch
 try{
  globalThis.fetch=async()=>new Response('old server',{status:404})
  await assert.rejects(localRequest('/api/live-self'),/backend 0.3.0/)
  globalThis.fetch=async()=>new Response('{"detail":"Private tools are available only from the local LolAi app."}',{status:403})
  await assert.rejects(localRequest('/api/private-feedback'),/only from the local/)
  globalThis.fetch=async()=>new Response('{"detail":"Feedback entry not found."}',{status:404})
  await assert.rejects(localRequest('/api/private-feedback/missing'),error=>error.message==='Feedback entry not found.')
  globalThis.fetch=async()=>new Response('null',{status:200})
  await assert.rejects(localRequest('/api/private-feedback'),/could not be completed/)
 }finally{globalThis.fetch=original}
})

const compact='class LolGetChampionAnalysis: champion,position,data\nclass Data: core_items\nclass CoreItems: ids,ids_names,play,win,pick_rate\n\nLolGetChampionAnalysis("AHRI","MID",Data(CoreItems([3118,4645,3157],["Malignance","Shadowflame","Zhonya\'s Hourglass"],6120,3232,0.18)))'
test('official compact provider records become named build evidence without executing provider text',()=>{
 const builds=buildEvidence(parseProviderData(compact))
 assert.equal(builds.length,1)
 assert.deepEqual(builds[0],{kind:'core_items',ids:[3118,4645,3157],names:['Malignance','Shadowflame',"Zhonya's Hourglass"],plays:6120,wins:3232,pickRate:.18})
 const data={data:{boots:{ids:[3020],ids_names:['Sorcerer'],play:100,win:55,pick_rate:.5}}}
 assert.deepEqual(parseProviderData('',data),data)
 assert.deepEqual(buildEvidence(parseProviderData(JSON.stringify(data))),buildEvidence(data))
})

test('provider parser rejects executable expressions, malformed records, nonfinite values and deep nesting',()=>{
 for(const text of [compact+'; alert(1)',compact.replace('6120','Infinity'),compact.replace('CoreItems([','Unknown(['),compact.replace('3232','0/0'),'class Foo: data\nFoo(globalThis.fetch("https://evil.example"))','class Foo: data\nFoo('+ '['.repeat(30)+'0'+']'.repeat(30)+')','x'.repeat(500001)])assert.equal(parseProviderData(text),null)
 const invalid={data:{boots:{ids:[3020],ids_names:['Boots'],play:5,win:6,pick_rate:.5}}}
 assert.deepEqual(buildEvidence(invalid),[])
 invalid.data.boots.win=2;invalid.data.boots.ids_names=[]
 assert.deepEqual(buildEvidence(invalid),[])
})

test('matchup responses accept arrays, deduplicate builds and rank frequency rather than sparse win rates',()=>{
 const row=(id,play,win,pick_rate)=>({ids:[id],ids_names:[`Item ${id}`],play,win,pick_rate})
 const result=buildEvidence({data:{core_items:[row(1,10,10,.01),row(2,100,40,.8),row(2,100,40,.8),row(3,50,20,.3),row(4,40,20,.2)],boots:[row(5,10,5,.1),row(6,100,50,.7)]}})
 assert.deepEqual(result.filter(item=>item.kind==='core_items').map(item=>item.ids[0]),[2,3,4])
 assert.equal(result.find(item=>item.kind==='boots').ids[0],6)
 assert.deepEqual(buildEvidence({data:{core_items:[row(1,Number.MAX_SAFE_INTEGER+1,1,.2)]}}),[])
})

test('matchup tips retain provider identity, accept missing text and reject malformed identity or excessive text',()=>{
 const data={my_champion:'Sylas',opponent_champion:'Warwick',position:'jungle',data:{opponent_champion_tip:'Review the matchup.',recommended_play_style:'even',lane_advantage_champion:'EVEN',lane_solo_kill_advantage_champion:'Warwick'}}
 assert.deepEqual(matchupGuide(data),{champion:'Sylas',opponent:'Warwick',position:'jungle',tip:'Review the matchup.',style:'even',laneAdvantage:'EVEN',soloKillAdvantage:'Warwick'})
 assert.equal(matchupGuide({...data,position:'unknown'}),null)
 assert.equal(matchupGuide({...data,opponent_champion:null}),null)
 assert.equal(matchupGuide({...data,data:{}}).tip,null)
 assert.equal(matchupGuide({...data,data:{opponent_champion_tip:'x'.repeat(4001)}}).tip,null)
})

test('Data Dragon chooses the exact historical patch and refuses unsafe versions and item image paths',()=>{
 assert.equal(matchingVersion(['16.21.1','16.20.2','16.20.1'],'16.20.724.7307'),'16.20.2')
 assert.equal(matchingVersion(['16.21.1','16.20.2'],'16.2'),null)
 assert.equal(matchingVersion(['16.20.2?bad=1'],'16.20'),null)
 assert.equal(itemImageUrl('16.20.2',3157),'https://ddragon.leagueoflegends.com/cdn/16.20.2/img/item/3157.png')
 for(const version of ['latest','../16.20.2','16.20.2?x=1'])assert.equal(itemImageUrl(version,3157),null)
 assert.equal(itemImageUrl('16.20.2',NaN),null)
 assert.deepEqual(parseItemNames({data:{3157:{name:"Zhonya's Hourglass"},bad:{name:'discard'},999:{name:1},888:null}}),{3157:"Zhonya's Hourglass"})
 assert.deepEqual(parseItemNames({data:[]}),{})
})

test('item metadata requests are shared, localized, credential-free and never substitute a different patch',async()=>{
 const original=globalThis.fetch,calls=[]
 try{
  globalThis.fetch=async(url,options)=>{calls.push(url);assert.equal(options.credentials,'omit');assert.equal(options.referrerPolicy,'no-referrer');return new Response(JSON.stringify(url.endsWith('versions.json')?['16.21.1','16.20.2']:{data:{3157:{name:url.includes('ko_KR')?'존야의 모래시계':"Zhonya's Hourglass"}}}),{status:200})}
  const [one,two]=await Promise.all([dataDragonItems('16.20','en'),dataDragonItems('16.20','en')])
  assert.deepEqual(one,two);assert.equal(one.version,'16.20.2');assert.equal(calls.length,2)
  const korean=await dataDragonItems('16.20','ko')
  assert.equal(korean.names['3157'],'존야의 모래시계');assert.equal(calls.length,3)
  assert.equal(await dataDragonItems('16.19','en'),null);assert.equal(calls.length,3)
 }finally{globalThis.fetch=original}
})
