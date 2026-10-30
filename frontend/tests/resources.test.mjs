import assert from 'node:assert/strict'
import test from 'node:test'
import {normalizePatch,parseDataDragonVersions,youtubeSearchUrl} from '../src/resources.ts'

test('patches accept match versions and reject malformed or unsafe values',()=>{
 assert.equal(normalizePatch('16.20.724.7307'),'16.20')
 assert.equal(normalizePatch(' 16.21 '),'16.21')
 for(const value of [null,undefined,16.21,'','latest','16','16.21?x=1','16.21<script>','16..21','16.21.1.2.3','016.21'])assert.equal(normalizePatch(value),null)
})
test('Data Dragon accepts a version list and rejects unexpected payloads',()=>{
 assert.deepEqual(parseDataDragonVersions(['16.21.1','16.20.1']),{version:'16.21.1',patch:'16.21'})
 assert.deepEqual(parseDataDragonVersions(['16.21.1','10.10.3216176','lolpatch_7.20']),{version:'16.21.1',patch:'16.21'})
 for(const value of [null,{},[],['16.21'],['16.21.1',null],['latest'],['16.21.1?x=1']])assert.equal(parseDataDragonVersions(value),null)
})
test('YouTube URLs preserve punctuation and encode all search context',()=>{
 for(const champion of ["Cho'Gath",'Nunu & Willump','Kai’Sa','Dr. Mundo']){
  const url=new URL(youtubeSearchUrl(champion,'Mid','16.20.724.7307','guide'))
  assert.equal(url.origin,'https://www.youtube.com')
  assert.equal(url.pathname,'/results')
  assert.equal(url.searchParams.get('search_query'),`${champion} Mid patch 16.20 guide`)
  assert.equal([...url.searchParams].length,1)
 }
 assert.equal(new URL(youtubeSearchUrl('Ahri','Mid','','otp')).searchParams.get('search_query'),'Ahri Mid challenger one trick')
 assert.equal(youtubeSearchUrl('Ahri','Mid','16.21&evil=1','guide'),null)
})
