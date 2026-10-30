import {createContext,useContext,useEffect,useState,type ReactNode} from 'react'
import {LANGUAGE_KEY,localizedRole,readLanguage,translate,type Language} from './translation'

type I18n={language:Language;locale:'en-US'|'ko-KR';setLanguage:(language:Language)=>void;t:(text:string,values?:Record<string,string|number>)=>string;roleName:(role:string)=>string}
export const I18nContext=createContext<I18n>({language:'en',locale:'en-US',setLanguage:()=>{},t:(text,values)=>translate('en',text,values),roleName:role=>localizedRole('en',role)})
export function LanguageProvider({children}:{children:ReactNode}){
 const [language,setLanguage]=useState<Language>(()=>{try{return readLanguage(window.localStorage)}catch{return 'en'}})
 const t=(text:string,values?:Record<string,string|number>)=>translate(language,text,values)
 useEffect(()=>{
  document.documentElement.lang=language
  document.title=translate(language,'LolAi.gg · Match intelligence')
  document.querySelector('meta[name="description"]')?.setAttribute('content',translate(language,'LolAi.gg historical League of Legends analysis. SKKU graduation project.'))
  try{window.localStorage.setItem(LANGUAGE_KEY,language)}catch{/* Language switching still works when browser storage is unavailable. */}
 },[language])
 return <I18nContext.Provider value={{language,locale:language==='ko'?'ko-KR':'en-US',setLanguage,t,roleName:role=>localizedRole(language,role)}}>{children}</I18nContext.Provider>
}
export const useI18n=()=>useContext(I18nContext)
