import assert from 'node:assert/strict'
import test,{after} from 'node:test'
import {mkdtempSync,rmSync,mkdirSync} from 'node:fs'
import {fileURLToPath,pathToFileURL} from 'node:url'
import path from 'node:path'
import {buildSync} from 'esbuild'
import {createElement} from 'react'
import {renderToStaticMarkup} from 'react-dom/server'

const frontend=fileURLToPath(new URL('../',import.meta.url))
mkdirSync(path.join(frontend,'.tmp'),{recursive:true})
const temporary=mkdtempSync(path.join(frontend,'.tmp','native-'))
after(()=>rmSync(temporary,{recursive:true,force:true}))
buildSync({stdin:{contents:"export * from './src/native';export {default as RankHistory} from './src/RankHistory';export {default as ExplainableTips} from './src/ExplainableTips';export {filterChampions} from './src/ChampionExplorer';export {default as NativeMatch} from './src/NativeMatch';export {default as NativePlayerReport} from './src/NativePlayerReport';export {I18nContext} from './src/i18n';export {translate,localizedRole} from './src/translation';",resolveDir:frontend},bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic',outfile:path.join(temporary,'native.mjs')})
const {parseGoal,goalProgress,recentForm,filterChampions,NativeMatch,NativePlayerReport,ExplainableTips,RankHistory,I18nContext,translate,localizedRole}=await import(pathToFileURL(path.join(temporary,'native.mjs')).href)
const render=(component,props,language='en')=>renderToStaticMarkup(createElement(I18nContext.Provider,{value:{language,locale:language==='ko'?'ko-KR':'en-US',setLanguage:()=>{},t:(text,values)=>translate(language,text,values),roleName:role=>localizedRole(language,role)}},createElement(component,props)))
const game=(id,time,role='MIDDLE')=>({id,played_at:time,role,win:true,cs_per_min:6,vision_score:30,duration_minutes:30,deaths:4,kill_participation:.5})
const goal={version:1,role:'MIDDLE',metric:'cs_per_min',target:6,created_at:1800000000000,excluded_ids:['existing']}

test('practice goals reject corrupt storage and impossible targets',()=>{
 assert.deepEqual(parseGoal(goal),goal)
 for(const value of [null,{}, {...goal,metric:'__proto__'}, {...goal,role:'ALL'}, {...goal,target:NaN}, {...goal,target:-1}, {...goal,target:31}, {...goal,created_at:Infinity}, {...goal,excluded_ids:[1]}])assert.equal(parseGoal(value),null)
 assert.ok(parseGoal({...goal,metric:'kill_participation',target:100}))
 assert.equal(parseGoal({...goal,metric:'kill_participation',target:101}),null)
})

test('goal progress uses only first three genuinely later same-role games, excluding duplicates and loaded history',()=>{
 const matches=[game('old',goal.created_at-1),game('existing',goal.created_at+1),game('fourth',goal.created_at+4000),game('third',goal.created_at+3000),game('second',goal.created_at+2000),game('first',goal.created_at+1000),game('first',goal.created_at+1000),game('wrong-role',goal.created_at+10,'UTILITY')]
 assert.deepEqual(goalProgress(goal,matches).map(row=>row.id),['first','second','third'])
 assert.ok(goalProgress(goal,matches).every(row=>row.met))
 const match=game('new',goal.created_at+1000)
 assert.equal(goalProgress({...goal,metric:'deaths',target:3},[match])[0].met,false)
 assert.equal(goalProgress({...goal,metric:'vision_per_min',target:1},[match])[0].actual,1)
 assert.equal(goalProgress({...goal,metric:'kill_participation',target:60},[match])[0].actual,50)
})

test('recent form sorts by real match time and compares same-role groups without fabricating a skill score',()=>{
 const games=Array.from({length:10},(_,index)=>({...game(String(index),1800000000+index),win:index>=5}))
 const form=recentForm(games,'MIDDLE')
 assert.equal(form.recent.wins,5)
 assert.equal(form.previous.wins,0)
 assert.equal(form.recent.cs_per_min,6)
 assert.equal(recentForm(games.slice(1),'MIDDLE'),null)
 assert.equal(recentForm(games,'UTILITY'),null)
})

test('champion explorer keeps patch, queue and role cohorts separate and applies minimum counts',()=>{
 const base={champion:'Ahri',role:'MIDDLE',patch:'16.21',queue_id:420,games:10,win_rate:.6,kda:3}
 const groups=[base,{...base,role:'UTILITY',games:3},{...base,patch:'16.20'},{...base,queue_id:440},{...base,champion:'Zed',games:12,win_rate:.4}]
 assert.deepEqual(filterChampions(groups,' ahr ','MIDDLE','16.21',420,5,'games'),[base])
 assert.equal(filterChampions(groups,'','ALL','16.21',420,1,'games').length,3)
 assert.equal(filterChampions(groups,'','MIDDLE','16.21',420,5,'win_rate')[0].champion,'Ahri')
 assert.equal(filterChampions(groups,'','MIDDLE','16.21',420,5,'games')[0].champion,'Zed')
 assert.equal(groups[0],base)
})

test('native scoreboard renders both teams, missing fields and Korean without an outside service',()=>{
 const player={participant_id:3,team_id:100,selected:true,name:'A <script>',tag:'KR1',champion:'Ahri',role:'MIDDLE',kills:4,deaths:3,assists:8,cs:180,cs_per_min:6,damage:null,gold:null,damage_share:null,gold_share:null,vision:30,items:[null,0,3157],runes:[8112],spells:[4,null]}
 const match={patch:'16.21',native:{teams:[{team_id:100,own:true,win:true,kills:20,gold:null,objectives:{tower:null},players:[player]},{team_id:200,own:false,win:false,kills:15,gold:50000,objectives:{tower:3},players:[{...player,participant_id:8,selected:false,champion:'Sylas'}]}],role_opponent:'Sylas',early_comparison:{timestamp_ms:540088,gold_diff:-500,cs_diff:-10,xp_diff:-300},objective_credits:null,death_windows:[]}}
 const en=render(NativeMatch,{match}),ko=render(NativeMatch,{match},'ko')
 for(const text of ['All ten players','Ahri','Sylas','9:00','-500','Item slot unavailable','timing is unavailable'])assert.ok(en.includes(text),text)
 assert.ok(en.includes('&lt;script&gt;'))
 assert.ok(!en.includes('<script>'))
 assert.ok(ko.includes('전체 분석'))
 assert.ok(ko.includes('타임라인이 없어'))
 assert.ok(!ko.includes('Full match review'))
 assert.ok(!en.includes('op.gg/'))
})

test('personal report makes absent objective timing explicit and does not fabricate a reference sample',()=>{
 const match={...game('one',1800000000),champion:'Ahri'}
 const data={player:{platform:'kr',game_name:'Demo',tag_line:'SKKU'},matches:[match]}
 const html=render(NativePlayerReport,{data,match},'ko')
 assert.ok(html.includes('개인 연습 목표'))
 assert.ok(html.includes('타임라인이 없어'))
 assert.ok(!html.includes('기록 0회'))
 assert.ok(html.includes('경기 10개가 필요'))
})

test('purchase history shows recorded skills and explicit ambiguous-undo limits in both languages',()=>{
 const player={participant_id:3,team_id:100,selected:true,name:'Test',tag:'KR1',champion:'Ahri',role:'MIDDLE',kills:1,deaths:2,assists:3,cs:100,cs_per_min:5,damage:null,gold:null,damage_share:null,gold_share:null,vision:10,items:[],runes:[],spells:[]}
 const match={native:{teams:[{team_id:100,own:true,win:true,kills:10,gold:null,objectives:{},players:[player]}],role_opponent:null,early_comparison:null,objective_credits:null,death_windows:[]},loadout:{status:'partial',complete_timeline:true,unresolved_undos:1,invalid_events:0,purchases:[],skill_order:[{timestamp_ms:60000,slot:1,ability:'Q'}],item_events:[{timestamp_ms:45000,kind:'ITEM_PURCHASED',item_id:1001,undone:true},{timestamp_ms:46000,kind:'ITEM_UNDO',before_id:1001,after_id:0,undone:false}]}}
 const en=render(NativeMatch,{match}),ko=render(NativeMatch,{match},'ko')
 for(const value of ['Purchase sequence and skill order','Q','1:00','0:45','Reversed by undo','excluded from trusted build aggregates'])assert.ok(en.includes(value),value)
 for(const value of ['구매 순서와 스킬','신뢰 가능한 빌드 집계에서 제외','되돌리기로 취소됨'])assert.ok(ko.includes(value),value)
 assert.ok(!ko.includes('Purchase and undo log'))
})


test('native tips show numeric evidence, original formula and explicit tier/weight limitations in both languages',()=>{
 const tip={metric:'cs_per_min',actual:4,benchmark:6,percentile:20,gap:.3,impact_weight:.5,consistency:.8,priority:.12,below_games:7,recent_games:10,reference_rows:80,reference_matches:40}
 const report={status:'available',scope:'local_role',role:'MIDDLE',tier:null,weighting:'equal_descriptive',tips:[tip],strength:{...tip,metric:'vision_per_min',percentile:75},tier_status:'requires_verified_rank_data',patch:'16.21',recent_games:10,cohort_matches:40}
 const en=render(ExplainableTips,{report}),ko=render(ExplainableTips,{report},'ko')
 for(const text of ['Your largest consistent gaps','4.00','6.00','30.0%','50.0%','80.0%','0.1200','Relative strength','not learned win-impact','verified pre-match rank'])assert.ok(en.includes(text),text)
 for(const text of ['주요 격차','자체 공식','가중치','티어 비교 모드','6.00'])assert.ok(ko.includes(text),text)
 assert.ok(!ko.includes('Your largest consistent gaps'))
})

test('unavailable native tips never display a made-up weakness or rank',()=>{
 const html=render(ExplainableTips,{report:{status:'tier_unavailable',tips:[],strength:null}})
 assert.ok(html.includes('at least three recent games'))
 assert.ok(!html.includes('Review priority 1'))
 assert.ok(!html.includes('Gold junglers'))
})


test('official rank history shows actual previous values and same-division LP differences in English and Korean',()=>{
 const old={queue:'RANKED_SOLO_5x5',tier:'GOLD',division:'II',league_points:40,wins:20,losses:10,win_rate:2/3},now={...old,league_points:55}
 const previous={observed_at:'2026-10-29T00:00:00+00:00',entries:[old]},latest={observed_at:'2026-10-30T00:00:00+00:00',entries:[now]}
 const history={status:'available',recorded_checks:2,first_observed_at:previous.observed_at,current_observation:latest,previous_observation:previous,observations:[latest,previous]}
 const en=render(RankHistory,{history,current:[now]}),ko=render(RankHistory,{history,current:[now]},'ko')
 for(const text of ['40 LP','55 LP','+15','Previous season rank: not verified','not estimated skill tiers'])assert.ok(en.includes(text),text)
 for(const text of ['골드','같은 티어','+15','지난 시즌 랭크는 미확인'])assert.ok(ko.includes(text),text)
 const promoted=render(RankHistory,{history,current:[{...now,division:'I',league_points:3}]})
 assert.ok(promoted.includes('Tier or division changed'))
 assert.ok(!promoted.includes('LP change: -37'))
})

test('missing rank history and failed current lookup do not invent past-season ranks',()=>{
 const empty=render(RankHistory,{current:[]})
 assert.ok(empty.includes('No previous recorded rank'))
 assert.ok(!empty.includes('GOLD'))
 const saved={observed_at:'2026-10-29T00:00:00+00:00',entries:[]}
 const failed=render(RankHistory,{history:{status:'available',observations:[saved],current_observation:null,previous_observation:null},current:[]})
 assert.ok(failed.includes('no matching saved observation'))
 assert.ok(failed.includes('No rank returned'))
})
