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
const temporary=mkdtempSync(path.join(frontend,'.tmp','profile-review-'))
after(()=>rmSync(temporary,{recursive:true,force:true}))
buildSync({stdin:{contents:"export {default as PlayerProfile} from './src/PlayerProfile';export {default as PredictionReview} from './src/PredictionReview';export {default as ProbabilityTimeline} from './src/ProbabilityTimeline';export {default as VideoResources,parseVideoResults} from './src/VideoResources';export {default as ModelComparison} from './src/ModelComparison'",resolveDir:frontend},bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic',outfile:path.join(temporary,'components.mjs')})
const {PlayerProfile,PredictionReview,ProbabilityTimeline,VideoResources,parseVideoResults,ModelComparison}=await import(pathToFileURL(path.join(temporary,'components.mjs')).href)
const blank={games:0,wins:0,win_rate:null,kda:null,cs_per_min:null,kill_participation:null,vision_per_min:null}

test('empty role profile keeps five roles and does not invent a main role or win rate',()=>{
 const html=renderToStaticMarkup(createElement(PlayerProfile,{profile:{games:0,roles:['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'].map(role=>({...blank,role})),champions:[],main_role:null,main_role_tied:false,main_role_stats:null,off_role_stats:null,unknown_role_games:0,notice:'Loaded sample only.'}}))
 for(const role of ['Top','Jungle','Mid','Bot','Support'])assert.ok(html.includes(`>${role}</th>`))
 assert.ok(html.includes('Not enough role data'))
 assert.ok(!html.includes('0%'))
 assert.ok(!html.includes('Champion history'))
})

test('profile displays role ties, champions, sample counts and unknown-role warning',()=>{
 const html=renderToStaticMarkup(createElement(PlayerProfile,{profile:{games:3,roles:[],champions:[{...blank,champion:'Kai\'Sa',games:2,wins:1,win_rate:.5}],main_role:null,main_role_tied:true,main_role_stats:null,off_role_stats:null,unknown_role_games:1,notice:'Sample only.'}}))
 assert.ok(html.includes('Tied — no single main role'))
 assert.ok(html.includes('Champion history (1)'))
 assert.ok(html.includes('50%'))
 assert.ok(html.includes('1 match has no known role'))
})

test('match review shows actual snapshot and correct signed sensitivity without causal claims',()=>{
 const html=renderToStaticMarkup(createElement(PredictionReview,{match:{snapshot_timestamp_ms:540088,sensitivity:{available:true,method:'training_mean_replacement',notice:'Input sensitivity only.',items:[{feature:'gold_diff',observed_value:-1000,reference_value:50,probability_at_reference:.4,difference:-.2}]},events:[{timestamp_ms:601001,minute:10.02,kind:'BUILDING_KILL',label:'Tower destroyed',team_id:200,side:'own'}]}}))
 assert.ok(html.includes('>9:00</strong>'))
 assert.ok(html.includes('-20.0 pp'))
 assert.ok(html.includes('40.0%'))
 assert.ok(html.includes('>10:01</time>'))
 assert.ok(html.includes('Your team'))
 assert.ok(html.includes('not causal effects'))
 assert.ok(html.includes('including when you played red'))
})

test('missing optional fields and unavailable sensitivities remain renderable',()=>{
 assert.equal(renderToStaticMarkup(createElement(PredictionReview,{match:{}})),'<div class="prediction-review"></div>')
 const html=renderToStaticMarkup(createElement(PredictionReview,{match:{sensitivity:{available:false,method:'training_mean_replacement',notice:'No model.',items:[]},personal_comparison:{basis:'none',games:1,averages:null,deltas:null,notice:'Three other same-role games required.'},control_wards_placed:0,surrendered:false}}))
 assert.ok(html.includes('Sensitivity is unavailable'))
 assert.ok(html.includes('Three other same-role games required'))
 assert.ok(html.includes('Control wards placed: 0'))
 assert.ok(html.includes('Game ended in surrender: no'))
 assert.ok(!html.includes('vs NaN'))
})

test('probability timeline keeps missing model windows as gaps and shows actual frame time',()=>{
 const points=[{minute:5,snapshot_timestamp_ms:240100,probability:.2},{minute:6,snapshot_timestamp_ms:300100,probability:.4},{minute:8,snapshot_timestamp_ms:420100,probability:.7}]
 const html=renderToStaticMarkup(createElement(ProbabilityTimeline,{timeline:{available:true,notice:'Separately trained models.',points,evaluation:[]}}))
 const curve=html.match(/class="probability-path" d="([^"]+)"/)[1]
 assert.equal((curve.match(/M/g)??[]).length,2)
 assert.equal((curve.match(/L/g)??[]).length,1)
 assert.ok(html.includes('>4:00</td>'))
 assert.ok(html.includes('>20.0%</td>'))
 assert.ok(html.includes('reused-set scores are exploratory'))
 assert.equal(points[0].minute,5)
})

test('unavailable probability timeline does not draw a misleading curve',()=>{
 const html=renderToStaticMarkup(createElement(ProbabilityTimeline,{timeline:{available:false,notice:'No trained artifact.',points:[],evaluation:[]}}))
 assert.ok(html.includes('No compatible time-specific estimates'))
 assert.ok(!html.includes('<svg'))
})

test('video panel is on demand and disables loading for invalid patch input',()=>{
 const ready=renderToStaticMarkup(createElement(VideoResources,{champion:'Ahri',role:'Mid',patch:'16.21',valid:true}))
 assert.ok(ready.includes('Load video results'))
 assert.ok(ready.includes('aria-label="Sort videos"'))
 assert.ok(ready.includes('aria-label="Video publication window"'))
 assert.ok(!ready.includes('<li>'))
 const invalid=renderToStaticMarkup(createElement(VideoResources,{champion:'Ahri',role:'Mid',patch:'',valid:false}))
 assert.match(invalid,/<button[^>]*disabled=""[^>]*>Load video results<\/button>/)
})

test('video response parsing keeps genuine metadata and rejects unsafe or malformed result fields',()=>{
 const video={id:'ABCdef123_-',url:'https://www.youtube.com/watch?v=ABCdef123_-',title:'Guide',channel:'A player',published_at:'2026-10-30T00:00:00Z',views:1024,patch_mentioned:true}
 const payload={status:'ok',notice:'Views are not quality evidence.',videos:[video]}
 assert.deepEqual(parseVideoResults(payload),payload)
 assert.ok(parseVideoResults({...payload,videos:[{...video,views:null}]}))
 assert.ok(parseVideoResults({status:'not_configured',notice:'No backend key.',videos:[]}))
 for(const bad of [null,{}, {...payload,status:'not_configured'}, {...payload,videos:[{...video,url:'javascript:alert(1)'}]}, {...payload,videos:[{...video,views:'1024'}]}, {...payload,videos:[{...video,views:NaN}]}, {...payload,videos:[{...video,published_at:'not a date'}]}, {...payload,videos:[null]}])assert.equal(parseVideoResults(bad),null)
})

test('model comparison displays measured metrics and preserves exploratory serving-model caveats',()=>{
 const html=renderToStaticMarkup(createElement(ModelComparison,{comparison:{notice:'Already-viewed holdout.',train_count:83,test_count:21,active_model_unchanged:true,models:[{algorithm:'random_forest',status:'evaluated',metrics:{accuracy:14/21,roc_auc:.590909,brier_score:.260681}},{algorithm:'xgboost',status:'unavailable',notice:'Not installed.'}]}}))
 assert.ok(html.includes('Random forest'))
 assert.ok(html.includes('66.67%'))
 assert.ok(html.includes('0.591'))
 assert.ok(html.includes('0.261'))
 assert.ok(html.includes('83 earlier training matches'))
 assert.ok(html.includes('21 later holdout matches'))
 assert.ok(html.includes('XGBoost: Not installed.'))
 assert.ok(html.includes('serving MLP is unchanged'))
 assert.ok(html.includes('does not establish a winning model'))
})

test('absent or unavailable comparisons never fabricate benchmark metrics',()=>{
 for(const comparison of [null,undefined,{}, {notice:'No compatible benchmark.'}])assert.equal(renderToStaticMarkup(createElement(ModelComparison,{comparison})), '')
 const html=renderToStaticMarkup(createElement(ModelComparison,{comparison:{notice:'No benchmark available.',train_count:0,test_count:0,models:[{algorithm:'xgboost',status:'unavailable'}],active_model_unchanged:true}}))
 assert.ok(html.includes('unavailable'))
 assert.ok(!html.includes('0.00%'))
 assert.ok(!html.includes('0.000'))
})
