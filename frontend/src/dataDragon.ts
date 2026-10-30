import {normalizePatch} from './resources'
import type {Language} from './translation'

const VERSION=/^[1-9]\d{0,2}\.(?:0|[1-9]\d{0,2})\.\d{1,3}$/
export function matchingVersion(versions:unknown,patch:string):string|null{
 if(!normalizePatch(patch)||!Array.isArray(versions))return null
 return versions.find(value=>typeof value==='string'&&VERSION.test(value)&&normalizePatch(value)===normalizePatch(patch))??null
}

export function parseItemNames(value:unknown):Record<string,string>{
 if(!value||typeof value!=='object'||!('data' in value)||!value.data||typeof value.data!=='object'||Array.isArray(value.data))return {}
 return Object.fromEntries(Object.entries(value.data).filter(([id,row])=>/^[1-9]\d{0,6}$/.test(id)&&row&&typeof row==='object'&&typeof row.name==='string'&&row.name.length>0&&row.name.length<=120).map(([id,row])=>[id,(row as {name:string}).name]))
}

async function read(url:string):Promise<unknown>{
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000)
 try{const response=await fetch(url,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer'});if(!response.ok)return null;const text=await response.text();return text.length<=5_000_000?JSON.parse(text):null}catch{return null}finally{clearTimeout(timer)}
}
let versionsRequest:Promise<unknown>|undefined
export function dataDragonVersions(){return versionsRequest??=read('https://ddragon.leagueoflegends.com/api/versions.json')}
const itemRequests=new Map<string,Promise<{version:string;names:Record<string,string>}|null>>()
export function dataDragonItems(patch:string,language:Language){
 const key=`${patch}:${language}`
 if(!itemRequests.has(key)){
  if(itemRequests.size>=10)itemRequests.delete(itemRequests.keys().next().value!)
  itemRequests.set(key,(async()=>{const version=matchingVersion(await dataDragonVersions(),patch);if(!version)return null;const names=parseItemNames(await read(`https://ddragon.leagueoflegends.com/cdn/${version}/data/${language==='ko'?'ko_KR':'en_US'}/item.json`));return Object.keys(names).length?{version,names}:null})())
 }
 return itemRequests.get(key)!
}

export function itemImageUrl(version:string,id:number):string|null{
 return VERSION.test(version)&&Number.isSafeInteger(id)&&id>0&&id<10_000_000?`https://ddragon.leagueoflegends.com/cdn/${version}/img/item/${id}.png`:null
}
