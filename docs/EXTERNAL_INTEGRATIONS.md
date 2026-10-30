# 외부 자료와 현재 Riot 컨텍스트 연동

업데이트: 2026-10-30, Asia/Seoul. 아래에서 구현한 경로, 실제 외부 응답을 확인한 경로, 연결에 실패한 경로를 구분한다. 과거 프로토타입은 [프로젝트 이력](PROJECT_HISTORY_AND_IDEAS.md)에 별도 보관한다.

## 현재 자료 허브

선택한 경기의 챔피언·역할·패치를 표시하고 OP.GG, FOW, GGQ, DEEPLOL, YOUR.GG 공식 사이트로 이동하는 링크를 제공한다. 사이트 안에서 해당 챔피언을 검색해야 하며, 상대 서비스의 통계·점수·구독 기능을 가져오는 연동은 아니다. 이 링크에 플레이어 Riot ID를 포함하지 않는다.

YouTube 가이드와 challenger/one-trick 검색 링크는 챔피언·역할·입력 패치를 URL 인코딩한다. 잘못된 패치는 차단하며 경기 변경 시 패치를 초기화한다. [Data Dragon 공개 버전 목록](https://ddragon.leagueoflegends.com/api/versions.json)을 한 번 조회하고 실패하면 수동 입력을 유지한다. [Riot 문서](https://developer.riotgames.com/docs/lol#data-dragon)에 따라 Data Dragon 버전과 지역 클라이언트의 경기 패치는 다를 수 있으므로 별도로 표시한다.

이전 MVP 브라우저에서 Data Dragon 16.21.1, 잘못된 패치 차단, Orianna/Mid/16.21 검색 URL, 경기 변경을 확인했다. [당시 화면](screenshots/learning-resources.png)은 새 영상 API 패널·현재 랭크/숙련도·확장 기능의 브라우저 검증 증거가 아니다.

## 구현된 YouTube API 경로

`VideoResources.tsx`의 **Load video results** 버튼이 같은 서버의 `/api/videos`를 요청한다. 백엔드는 [YouTube search.list](https://developers.google.com/youtube/data/docs/search/list)로 결과를 찾고 [videos.list](https://developers.google.com/youtube/data/docs/videos/list)에서 제목·채널·공개 시각·조회수를 읽는다. 선택 기준은 최신순 또는 조회수순, 공개 기간은 14/30/90일이다. 최대 6개 결과를 반환하고 6시간 캐시한다. 검색 시 Riot ID는 보내지 않는다.

키는 `YOUTUBE_API_KEY`라는 **백엔드 전용 환경 설정**이다. 브라우저에 키를 넣는 입력란은 없으며, Google 요청에서도 헤더로 전달한다. 현재는 무시된 로컬 백엔드 환경에 키를 설정하고 서버를 재시작하여 **실제 영상 메타데이터 조회에 성공했다**. 설정 전에는 `not_configured`와 안내문을 실제로 확인했다. 오류/할당량/네트워크 실패에는 `unavailable`을 반환하고 일반 검색 링크를 유지한다. 빈 정상 검색 결과와 설정·요청 실패를 구분한다. 가상 영상이나 조회수를 채우지 않는다.

프런트엔드는 요청 문맥이 바뀌면 이전 요청을 취소하고 결과를 숨긴다. 문맥에는 챔피언·역할·패치·정렬·기간과 패치 유효성도 포함한다. 응답의 영상 ID·고정 YouTube URL·시각·조회수 형식을 검사하며, 잘못된 메타데이터를 링크로 표시하지 않는다.

패치 일치 표시는 제목/설명에 패치 문자열이 있는지를 검사한 것이다. 실제 영상이 그 패치로 플레이됐는지, 해당 챔피언 장인인지, 조언이 유용한지는 검증하지 않는다. 조회수·최근 업로드는 품질 점수가 아니다. 전문가/플레이어와 채널의 검증된 연결, 영상 내용 분석과 추천 효과 연구는 미구현이다.

코드: [영상 백엔드](../backend/app/videos.py), [영상 패널](../frontend/src/VideoResources.tsx), [자료 허브](../frontend/src/LearningResources.tsx). 자동 테스트는 모의 응답을 사용하므로 실제 Google 접근 성공을 뜻하지 않는다.

### 0.2.0에서 실제 확인한 영상 응답

2026-10-30 브라우저에서 Ahri/Mid, 패치 16.21, 조회수순, 최근 30일 조건으로 조회하여 [How to Climb With AHRI Guide - S16 League of Legends](https://www.youtube.com/watch?v=BnwE5CD1-qA) 한 건이 표시되었다. 반환된 채널은 Coach Mysterias, 공개 날짜는 2026-10-02, 당시 조회수는 22,765회였다. 패치 문자열이 본문에 없어 **Patch not found in text**로 표시했다. 이는 실제 메타데이터 조회 성공이며 해당 패치 영상·장인 신원·조언 품질을 보증하거나 추천한 것이 아니다.

이후 실제 Riot 분석 JSON을 내보내 393,515바이트의 10경기/5역할 자료를 확인했다. 각 경기의 민감도 6개, 시간별 확률 총 110개를 기존 캐시의 원자료와 설치된 모델로 재현했고, 평가 보고서는 원래 모델과 일치했다. Riot/Google 키 형태 검사는 발견 0건이었다. 현재 랭크/숙련도와 영상은 별도 요청 패널이며 이 분석 JSON에 모두 포함된 것으로 주장하지 않는다.

## 현재 Riot 랭크와 챔피언 숙련도

선택 경기 아래 **Load current Riot context** 버튼이 `/api/player-context`를 요청한다. ACCOUNT-V1으로 계정을 확인한 후 LEAGUE-V4의 PUUID 랭크와 CHAMPION-MASTERY-V4의 선택 챔피언 숙련도를 백엔드에서 조회한다. 선택한 매치의 챔피언 ID가 없으면 숙련도를 만들어내지 않는다. 설정된 Riot 키와 기존 캐시/요청 간격을 재사용하며, 5분 캐시와 조회 실패/빈 결과/미보유 상태를 표시한다.

이 값은 **현재 계정 상태**다. 예전 경기 시점의 티어나 숙련도를 뜻하지 않으며 예측 모델 입력에도 넣지 않는다. 현재 랭크만으로 학습 자료를 저티어/고티어로 소급 분류하지 않는다. DemoPlayer는 가상이므로 해당 버튼을 비활성화한다. 서버 재시작 후 0.2.0 브라우저에서 Molybdite#KR1의 실제 응답을 확인했다. 당시 현재 랭크는 Bronze II/73 LP, 221승/245패였고, 선택된 Sylas의 숙련도는 레벨 9/71,768점, 마지막 플레이 날짜는 2026-10-29였다. 한 계정의 성공 경로를 확인한 것으로 다른 지역·오류·빈 응답 전체 검증을 뜻하지 않는다.

코드: [Riot 컨텍스트](../backend/app/player_context.py), [현재 컨텍스트 패널](../frontend/src/PlayerContext.tsx).

## OP.GG 공식 MCP: 연구와 실제 실패 기록

**OP.GG는 공식 오픈소스 MCP가 있다.** [공식 소개](https://op.gg/open-source/opgg-mcp), [GitHub](https://github.com/opgginc/opgg-mcp), [국문 README](https://github.com/opgginc/opgg-mcp/blob/main/README.ko.md)에서 챔피언 분석·빌드·상성·시너지·장인 리더보드·전적·프로 Riot ID 등의 도구를 안내한다. 원격 엔드포인트는 `https://mcp-api.op.gg/mcp`이며 Streamable HTTP를 사용한다.

읽기 전용 [탐색 스크립트](../backend/scripts/probe_opgg.py)를 구현하고 실행했다. 고정된 공식 엔드포인트에서 초기화/도구 스키마를 확인하려는 시도였지만 이 환경의 DNS/연결 단계에서 **ConnectError**가 발생했다. 초기화나 스키마 조회, 도구 호출에 성공한 것이 아니다. Riot 키·계정 정보는 보내지 않았으며 OP.GG 데이터가 현재 앱으로 유입되지 않았다. 실제 API 어댑터, 아이템 빌드 표시, 장인 목록 통합은 여전히 미구현이다.

[MIT 라이선스](https://github.com/opgginc/opgg-mcp/blob/main/LICENSE)는 공개 코드에 적용된다. 원격 MCP 클라이언트 저장소가 OP.GG 전체 데이터 백엔드를 자가 호스팅하는 소스이거나 모든 데이터의 재배포 권한을 뜻하지는 않는다. [데이터 도움말](https://help.op.gg/hc/en-us/articles/31091405109401-Can-I-use-OP-GG-data)과 [이용약관](https://op.gg/lol/policies/agreement)의 제공 범위를 함께 확인한다. 네트워크가 허용되는 환경에서 스크립트를 다시 실행한 뒤 실제 스키마와 한 도구를 확인해야 연결 성공을 주장할 수 있다.

## 다른 서비스: 공식 링크와 미연동 범위

- **FOW:** [챔피언 통계](https://www.fow.lol/stats), [장인 랭킹](https://www.fow.lol/champranking), [멀티서치](https://www.fow.lol/multi). 검사한 공식 페이지에서는 개발자 API·소스 저장소를 확인하지 못했다. [약관](https://www.fow.lol/view/accessterms)의 복제·이용 범위를 확인해야 한다.
- **GGQ:** [공식 홈페이지](https://ggq.gg/?hl=ko_KR), [데스크톱 기능](https://ggq.gg/download), [코치 안내](https://ggq.gg/membership/intro)는 빌드·밴픽·하이라이트·오버레이·음성 코칭 등을 소개한다. 검사 범위에서 외부 API·라이선스를 확인하지 못했으며 [공식 문의](https://ggq.gg/feedback)가 확인 경로다.
- **DEEPLOL:** [홈페이지](https://www.deeplol.gg/?hl=ko)에서 전적·AI-Score·빌드·랭킹을 안내한다. 내부 점수식이나 공개 API를 확인하지 못했고 [제휴 안내](https://www.deeplol.gg/advertise?hl=ko)가 있다.
- **YOUR.GG:** [멤버십 안내](https://m.your.gg/ko/kr/membership?region=kr)는 챔피언·역할 PLAYREPORT와 코칭·오버레이 등을 설명한다. 외부 API·통합 라이선스는 검사 범위에서 확인하지 못했다.

확인하지 못했다는 기록은 API가 절대 존재하지 않는다는 결론이 아니다. 현재는 사이트 링크 외에 이 네 제공사의 데이터 어댑터, 점수 재현, 유료 기능 병합, 스크레이핑/iframe 복제가 없다. G-Assist, Overwolf, Blitz, oracle-devrel/leagueoflegends-optimizer도 과거 참고 목록이며 통합하지 않았다.

## 검증 범위와 남은 작업

현재 프런트엔드 **13개 테스트**, TypeScript·Vite 빌드가 통과했다. 현재 집중 백엔드 검사 **108개 + 하위 검사 6개**는 전체 비동기 API/수집기 재실행을 포함하지 않는다. 이전 MVP의 정상 Cursor 터미널 **44개 + 하위 검사 6개** 통과와 브라우저/내보내기 증거는 별도 이력이다. 사용자가 서버를 재시작한 뒤 health 0.2.0, 데모 프로필/모델 비교, 실제 Molybdite#KR1 10경기(5승/5패), 시점/민감도/시간별 곡선, 현재 Riot 컨텍스트, 실제 YouTube 결과와 JSON 내보내기를 확인했다. 전체 135개 검사의 정상 터미널 실행 결과는 아직 대기 중이다.

다음 단계는 정상 터미널의 전체 135개 검사 결과를 기록하는 것이다. 최신 서버 재시작과 주요 성공 경로는 확인했으며, 할당량·네트워크 실패·빈 응답·다른 계정/지역 경로는 별도 검사 대상으로 남는다. OP.GG 탐색을 네트워크가 가능한 환경에서 재시도한 후 제공 범위에 맞는 작은 통합부터 구현한다. 키가 없거나 연결에 실패한 상태를 완료된 연동으로 표시하지 않는다.

[Riot 게임 무결성 정책](https://developer.riotgames.com/docs/lol#game-integrity)을 확인하면서 확장한다. 모든 실시간 도구가 일괄 금지라는 뜻은 아니지만, 현재 범위는 완료 경기 분석이다. 채팅·동료 평가 수집은 별도 동의·라벨 기준·정정 절차가 필요하며 미구현이다. 통계만으로 인성·고의 패배·팀워크를 판정하지 않는다.

원래 104경기 MLP의 낮은 성능, 새로운 RF 비교와 11개 시간별 MLP는 서로 구분한다. [시간별 모델 설명](TEMPORAL_MODELS.md)과 [상세 기능 감사](FEATURE_COVERAGE_AUDIT.md)를 참조한다. 과거 1,000경기·XGBoost 79%는 원자료와 실험을 복구하기 전까지 역사적 기록이다. 예측 정확도와 사용자 조언의 효과도 서로 다른 평가 대상이다.
