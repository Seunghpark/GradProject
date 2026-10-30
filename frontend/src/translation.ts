import {appMessages} from './translations/app'
import {profileMessages} from './translations/profiles'
import {resourceMessages} from './translations/resources'
import {predictionMessages} from './translations/prediction'
import {translateApiText} from './translations/api'
import {researchMessages} from './translations/research'
import {nativeMessages} from './translations/native'

export type Language='en'|'ko'
export const LANGUAGE_KEY='lolai-language'
export const messages:Record<string,string>={...appMessages,...profileMessages,...resourceMessages,...predictionMessages,...researchMessages,...nativeMessages}
export function readLanguage(storage?:Pick<Storage,'getItem'>|null):Language{
 try{return storage?.getItem(LANGUAGE_KEY)==='ko'?'ko':'en'}catch{return 'en'}
}
export function translate(language:Language,text:string,values:Record<string,string|number>={}):string{
 const template=language==='ko'?(Object.hasOwn(messages,text)?messages[text]:translateApiText(text)??text):text
 return template.replace(/\{(\w+)\}/g,(match,key)=>Object.hasOwn(values,key)?String(values[key]):match)
}
export function localizedRole(language:Language,role:string):string{
 const roles:Record<string,string>={TOP:'Top',JUNGLE:'Jungle',MIDDLE:'Mid',MID:'Mid',BOTTOM:'Bot',UTILITY:'Support',SUPPORT:'Support',UNKNOWN:'Unknown role'}
 return translate(language,Object.hasOwn(roles,role)?roles[role]:role||'Unknown role')
}
