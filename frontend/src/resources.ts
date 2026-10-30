export function normalizePatch(value:unknown):string|null {
 if(typeof value!=='string')return null
 const version=value.trim()
 if(!/^[1-9]\d{0,2}\.(?:0|[1-9]\d{0,2})(?:\.\d{1,10}){0,2}$/.test(version))return null
 return version.split('.').slice(0,2).join('.')
}

export function parseDataDragonVersions(value:unknown):{version:string;patch:string}|null {
 if(!Array.isArray(value)||!value.length||!value.every(item=>typeof item==='string')||!/^[1-9]\d{0,2}\.(?:0|[1-9]\d{0,2})\.\d{1,3}$/.test(value[0]))return null
 return {version:value[0],patch:normalizePatch(value[0])!}
}

export function youtubeSearchUrl(champion:string,role:string,patch:string,kind:'guide'|'otp'):string|null {
 const normalized=normalizePatch(patch)
 if(patch.trim()&&!normalized)return null
 const query=[champion.trim(),role.trim(),normalized?`patch ${normalized}`:'',kind==='otp'?'challenger one trick':'guide'].filter(Boolean).join(' ')
 return `https://www.youtube.com/results?${new URLSearchParams({search_query:query})}`
}
