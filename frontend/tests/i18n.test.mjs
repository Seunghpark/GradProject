import assert from 'node:assert/strict'
import test,{after} from 'node:test'
import {mkdtempSync,rmSync,mkdirSync,readFileSync,readdirSync} from 'node:fs'
import {fileURLToPath,pathToFileURL} from 'node:url'
import path from 'node:path'
import {buildSync} from 'esbuild'
import {createElement} from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import ts from 'typescript'

const frontend=fileURLToPath(new URL('../',import.meta.url))
mkdirSync(path.join(frontend,'.tmp'),{recursive:true})
const temporary=mkdtempSync(path.join(frontend,'.tmp','i18n-'))
after(()=>rmSync(temporary,{recursive:true,force:true}))
buildSync({stdin:{contents:"export * from './src/translation'; export {I18nContext} from './src/i18n'; export {apiMessages,translateApiText} from './src/translations/api'; export {default as App} from './src/App'; export {default as PlayerProfile} from './src/PlayerProfile'; export {default as ModelComparison} from './src/ModelComparison'; export {default as PredictionReview} from './src/PredictionReview'; export {default as LearningResources} from './src/LearningResources';",resolveDir:frontend},bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic',outfile:path.join(temporary,'locale.mjs')})
const {translate,readLanguage,localizedRole,messages,apiMessages,translateApiText,I18nContext,App,PlayerProfile,ModelComparison,PredictionReview,LearningResources}=await import(pathToFileURL(path.join(temporary,'locale.mjs')).href)
const render=(Component,props={},language='ko')=>renderToStaticMarkup(createElement(I18nContext.Provider,{value:{language,locale:language==='ko'?'ko-KR':'en-US',setLanguage:()=>{},t:(text,values)=>translate(language,text,values),roleName:role=>localizedRole(language,role)}},createElement(Component,props)))

test('English is the default; only an explicitly saved Korean preference overrides it',()=>{
 assert.equal(readLanguage(),'en')
 assert.equal(readLanguage({getItem:()=>null}),'en')
 assert.equal(readLanguage({getItem:()=>'en'}),'en')
 assert.equal(readLanguage({getItem:()=>'ko'}),'ko')
 assert.equal(readLanguage({getItem:()=>'unexpected'}),'en')
 assert.equal(readLanguage({getItem:()=>{throw new Error('Storage blocked')}}),'en')
})

test('Korean templates preserve numbers, keep missing placeholders, and never replace interpolation recursively',()=>{
 assert.equal(translate('ko','Across {games} analyzed matches',{games:20}),'분석한 20경기 기준')
 assert.equal(translate('en','Across {games} analyzed matches',{games:20}),'Across 20 analyzed matches')
 assert.equal(translate('ko','Across {games} analyzed matches'),'분석한 {games}경기 기준')
 assert.equal(translate('ko','{name}',{name:'{games}'}),'{games}')
 assert.equal(translate('ko','Unknown upstream message'),'Unknown upstream message')
 for(const key of ['__proto__','constructor','toString'])assert.equal(translate('ko',key),key)
 assert.equal(localizedRole('ko','UTILITY'),'서포터')
 assert.equal(localizedRole('en','UTILITY'),'Support')
 assert.equal(localizedRole('ko','__proto__'),'__proto__')
})

test('dictionary templates keep the same placeholders in both languages',()=>{
 const placeholders=text=>(text.match(/\{\w+\}/g)??[]).sort()
 for(const [english,korean] of Object.entries(messages))assert.deepEqual(placeholders(english),placeholders(korean),english)
})

test('all literal translated component messages have a catalog entry',()=>{
 const missing=[]
 for(const name of readdirSync(path.join(frontend,'src')).filter(name=>name.endsWith('.tsx'))){
  const source=ts.createSourceFile(name,readFileSync(path.join(frontend,'src',name),'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX)
  const visit=node=>{if(ts.isCallExpression(node)&&ts.isIdentifier(node.expression)&&node.expression.text==='t'&&node.arguments[0]&&ts.isStringLiteral(node.arguments[0])){const key=node.arguments[0].text;if(!Object.hasOwn(messages,key)&&!translateApiText(key))missing.push(`${name}: ${key}`)}ts.forEachChild(node,visit)}
  visit(source)
 }
 assert.deepEqual(missing,[])
})

test('known API caveats, composed warnings and numerical insights translate without changing data claims',()=>{
 for(const [english,korean] of Object.entries(apiMessages))assert.equal(translate('ko',english),korean)
 const warning='Showing a saved Riot analysis (cached for up to five minutes). Riot rate limit reached. Retry in 60 seconds. Synthetic demo: fictional player and matches for presentation. These are not Riot results or evidence of real-world model accuracy.'
 const result=translate('ko',warning)
 assert.ok(result.includes('60초'))
 assert.ok(result.includes('합성 데모'))
 assert.ok(!result.includes('Riot rate limit reached'))
 assert.ok(translate('ko','5 wins from 10 recent eligible ranked games. This small, player-selected sample is descriptive and does not establish a long-term skill or improvement trend.').includes('10경기에서 5승'))
 const sentence="In 3 other loaded games in the same champion and role, you averaged 5.1 CS/min, 40% kill participation and 1.25 vision/min. This match: 6.0, 50% and 1.50. Review differences in matchup, duration and game state before setting a goal; this small sample is not a skill ranking or a causal explanation."
 const translated=translate('ko',sentence)
 for(const number of ['3','5.1','40%','1.25','6.0','50%','1.50'])assert.ok(translated.includes(number))
 assert.ok(translated.includes('인과관계'))
})

test('main form, navigation and accessibility labels render in either language',()=>{
 const korean=render(App),english=render(App,{},'en')
 for(const text of ['대시보드','연구 방법','분석 중…','한국','샘플 데모','서버 확인 중','English'])assert.ok(korean.includes(text),text)
 assert.ok(korean.includes('aria-label="Switch to English"'))
 for(const text of ['Dashboard','Methodology','Analyzing…','Korea','Sample demo','한국어'])assert.ok(english.includes(text),text)
 assert.ok(!korean.includes('Find the patterns behind your matches'))
 assert.ok(korean.includes('noValidate=""'))
})

test('profile, model and review content render Korean with stable metrics and scientific limits',()=>{
 const blank={games:0,wins:0,win_rate:null,kda:null,cs_per_min:null,kill_participation:null,vision_per_min:null}
 const profile=render(PlayerProfile,{profile:{games:0,roles:['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'].map(role=>({...blank,role})),champions:[],main_role:null,main_role_tied:false,main_role_stats:null,off_role_stats:null,unknown_role_games:0,notice:Object.keys(apiMessages).find(x=>x.startsWith('Only the loaded'))}})
 for(const role of ['탑','정글','미드','바텀','서포터'])assert.ok(profile.includes(`>${role}</th>`))
 assert.ok(profile.includes('역할 자료 부족'))
 assert.ok(!profile.includes('0%'))
 const comparison=render(ModelComparison,{comparison:{notice:'The same holdout was previously viewed for the logistic baseline. This is an exploratory comparison, not fresh independent validation.',train_count:83,test_count:21,active_model_unchanged:true,models:[{algorithm:'random_forest',status:'evaluated',metrics:{accuracy:14/21,roc_auc:.590909,brier_score:.260681}}]}})
 for(const text of ['랜덤 포레스트','66.67%','0.591','0.261','독립 검증','서비스의 MLP'])assert.ok(comparison.includes(text),text)
 const review=render(PredictionReview,{match:{snapshot_timestamp_ms:540088,insights:[],sensitivity:{available:true,notice:'Snapshot or model is invalid; input sensitivity is unavailable.',items:[{feature:'gold_diff',observed_value:-1000,reference_value:50,probability_at_reference:.4,difference:-.2}]},events:[{timestamp_ms:601001,kind:'BUILDING_KILL',label:'Tower destroyed',side:'own'}]}})
 for(const text of ['9:00','-20.0','40.0%','포탑 파괴','우리 팀','인과 효과'])assert.ok(review.includes(text),text)
})

test('Korean resource display preserves canonical English search query and original proper names',()=>{
 const html=render(LearningResources,{match:{champion:'Ahri',role:'MIDDLE',patch:'16.21'},roleLabel:'미드'})
 assert.ok(html.includes('Ahri'))
 assert.ok(html.includes('미드'))
 assert.ok(html.includes('Ahri+Mid+patch+16.21+guide'))
 assert.ok(!html.includes('Ahri+%EB%AF%B8%EB%93%9C'))
})
