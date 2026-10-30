// OP.GG's compact records are parsed as data; provider text is never executed.
export function parseProviderData(text:string,structured?:unknown):unknown{
 if(structured&&typeof structured==='object')return structured
 if(text.length>500000)return null
 try{return JSON.parse(text)}catch{/* Official compact records use class field declarations. */}
 try{
  const classes=new Map<string,string[]>(),lines=text.trim().split(/\r?\n/)
  while(lines.length&&(!lines[0].trim()||lines[0].startsWith('class '))){
   const line=lines.shift()!.trim();if(!line)continue
   const match=/^class ([A-Za-z][A-Za-z0-9_]{0,63}): ([A-Za-z][A-Za-z0-9_]*(?:,[A-Za-z][A-Za-z0-9_]*)*)$/.exec(line)
   if(!match||classes.has(match[1]))return null
   const fields=match[2].split(',');if(fields.length>64||new Set(fields).size!==fields.length)return null
   classes.set(match[1],fields)
  }
  if(!classes.size||classes.size>100)return null
  const source=lines.join('\n');let cursor=0,tokens=0
  const space=()=>{while(/\s/.test(source[cursor]??'')&&cursor<source.length)cursor++}
  function value(depth=0):unknown{
   if(depth>20||++tokens>20000)throw Error('Provider data limit')
   space();const char=source[cursor]
   if(char==='"'){
    const start=cursor++;let escaped=false
    while(cursor<source.length){const current=source[cursor++];if(current==='"'&&!escaped)return JSON.parse(source.slice(start,cursor));escaped=current==='\\'&&!escaped}
    throw Error('Invalid string')
   }
   if(char==='['){cursor++;return sequence(']',depth)}
   const numeric=/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(source.slice(cursor))
   if(numeric){cursor+=numeric[0].length;const result=Number(numeric[0]);if(!Number.isFinite(result))throw Error('Invalid number');return result}
   const identifier=/^[A-Za-z][A-Za-z0-9_]*/.exec(source.slice(cursor))?.[0]
   if(!identifier)throw Error('Invalid token')
   cursor+=identifier.length
   if(['null','None','true','True','false','False'].includes(identifier))return ['null','None'].includes(identifier)?null:['true','True'].includes(identifier)
   const fields=classes.get(identifier);space()
   if(!fields||source[cursor++]!=='(')throw Error('Unknown record')
   const args=sequence(')',depth)
   if(args.length!==fields.length)throw Error('Record fields differ')
   return Object.fromEntries(fields.map((field,index)=>[field,args[index]]))
  }
  function sequence(end:string,depth:number):unknown[]{
   const values:unknown[]=[];space();if(source[cursor]===end){cursor++;return values}
   for(;;){values.push(value(depth+1));space();const next=source[cursor++];if(next===end)return values;if(next!==',')throw Error('Invalid sequence')}
  }
  const output=value();space();return cursor===source.length?output:null
 }catch{return null}
}

export type BuildEvidence={kind:'core_items'|'starter_items'|'boots';ids:number[];names:string[];plays:number;wins:number;pickRate:number|null}
export function buildEvidence(data:unknown):BuildEvidence[]{
 if(!data||typeof data!=='object'||!('data' in data)||!data.data||typeof data.data!=='object')return []
 const output:BuildEvidence[]=[]
 for(const kind of ['core_items','starter_items','boots'] as const){
  const raw=(data.data as Record<string,unknown>)[kind]
  const candidates:BuildEvidence[]=[]
  for(const value of (Array.isArray(raw)?raw.slice(0,100):[raw])){
  if(!value||typeof value!=='object')continue
  const row=value as Record<string,unknown>
  if(!Array.isArray(row.ids)||!row.ids.length||row.ids.length>8||!row.ids.every(id=>Number.isInteger(id)&&id>0)
   ||!Array.isArray(row.ids_names)||row.ids_names.length!==row.ids.length||!row.ids_names.every(name=>typeof name==='string'&&name.length>0&&name.length<=100)
   ||!Number.isSafeInteger(row.play)||Number(row.play)<1||!Number.isSafeInteger(row.win)||Number(row.win)<0||Number(row.win)>Number(row.play))continue
  candidates.push({kind,ids:row.ids,names:row.ids_names,plays:Number(row.play),wins:Number(row.win),pickRate:typeof row.pick_rate==='number'&&Number.isFinite(row.pick_rate)&&row.pick_rate>=0&&row.pick_rate<=1?row.pick_rate:null})
  }
  // Frequency is descriptive; selecting by observed win rate would favor sparse survivor samples.
  candidates.sort((a,b)=>(b.pickRate??-1)-(a.pickRate??-1)||b.plays-a.plays)
  const selected=candidates.filter((value,index)=>candidates.findIndex(other=>other.ids.join(',')===value.ids.join(','))===index)
  output.push(...selected.slice(0,kind==='core_items'?3:1))
 }
 return output
}

export type MatchupGuide={champion:string;opponent:string;position:string;tip:string|null;style:string|null;laneAdvantage:string|null;soloKillAdvantage:string|null}
export function matchupGuide(value:unknown):MatchupGuide|null{
 if(!value||typeof value!=='object')return null
 const row=value as Record<string,unknown>
 if(!row.data||typeof row.data!=='object'||Array.isArray(row.data))return null
 const data=row.data as Record<string,unknown>
 const text=(field:unknown,max=120)=>typeof field==='string'&&field.trim().length>0&&field.length<=max?field:null
 const champion=text(row.my_champion),opponent=text(row.opponent_champion),position=text(row.position)
 if(!champion||!opponent||!position||!['top','mid','jungle','adc','support','none'].includes(position))return null
 const tip=text(data.opponent_champion_tip,4000)
 return {champion,opponent,position,tip,style:text(data.recommended_play_style),laneAdvantage:text(data.lane_advantage_champion),soloKillAdvantage:text(data.lane_solo_kill_advantage_champion)}
}
