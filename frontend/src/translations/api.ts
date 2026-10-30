// API payloads stay unchanged; translate known application messages only at display time.
export const apiMessages:Record<string,string>={
 'Match analysis is available, but shared-data saving or refresh did not finish.':'경기 분석은 가능하지만 공유 경기 자료의 저장 또는 통계 갱신을 마치지 못했습니다.',
 'Review missed farm':'놓친 CS 복기','Farming foundation':'파밍 기록','Review your deaths':'데스 장면 복기','Check your involvement':'팀 합류 상황 검토','Vision review':'시야 복기','Your recent sample':'최근 경기 표본','Make review measurable':'측정할 수 있는 복기 목표','Keep the evidence separate':'자료의 의미 구분','Compare with your own games':'자신의 경기와 비교',
 'Post-match feedback uses final statistics. Historical predictions use information available at each displayed snapshot. The main estimate and time-specific models are exploratory; neither establishes that a metric caused the result.':'경기 후 피드백은 최종 통계를 사용하고, 과거 시점의 예측은 표시된 관측 시각까지의 정보만 사용합니다. 주 추정과 시점별 모형은 모두 탐색적 결과이며, 특정 지표가 승패의 원인이었다는 근거는 아닙니다.',
 'Only the loaded, eligible matches are counted. Most-played role describes this sample, not your preferred role or autofill status. Win rates are descriptive; small groups and mixed patches/queues do not establish skill or improvement.':'불러온 경기 중 분석 조건에 맞는 경기만 집계합니다. 최다 플레이 역할은 이 표본의 기록이며 선호 역할이나 자동 배정 여부를 뜻하지 않습니다. 승률은 기술 통계이며, 적은 표본이나 서로 다른 패치·대전 유형의 기록만으로 실력이나 개선 효과를 입증할 수는 없습니다.',
 'Selected match excluded. Other displayed matches may be earlier or later. These final-statistic comparisons are for post-match review only, not model inputs or evidence that a change caused the result. Three games is a display minimum, not statistical validation.':'선택한 경기는 비교에서 제외합니다. 다른 경기는 선택 경기보다 이전 또는 이후의 경기일 수 있습니다. 최종 통계 비교는 사후 복기용이며 예측 입력이나 인과관계의 근거가 아닙니다. 3경기는 표시를 위한 최소 수이며 통계적 검증 기준이 아닙니다.',
 "Inputs are blue minus red. Each comparison replaces one input with its training-set mean. Differences use your team's probability and do not add up to an explanation of the result. These are model sensitivity checks, not causal effects, SHAP values, or gameplay recommendations.":'입력은 파란 팀에서 빨간 팀을 뺀 차이입니다. 입력 하나를 학습 평균으로 바꾸어 비교하며, 확률 차이는 우리 팀을 기준으로 표시합니다. 이 차이들을 합쳐 결과를 설명할 수는 없습니다. 모형의 민감도 검사이며 인과 효과, SHAP 값 또는 플레이 권장 사항이 아닙니다.',
 'Snapshot or model is invalid; input sensitivity is unavailable.':'관측 자료 또는 모형이 유효하지 않아 입력 민감도를 제공할 수 없습니다.',
 'Exploratory retrospective probabilities from separately trained minute-specific MLPs. Each point uses the latest complete frame at or up to one minute before its target. The same small holdout was already viewed; these are uncalibrated research outputs, not independent validation, causal effects, or live coaching. Late-match samples select games still in progress.':'분 단위로 따로 학습한 MLP의 탐색적 과거 시점 확률입니다. 각 점은 목표 시각부터 최대 1분 전까지의 마지막 완전한 프레임을 사용합니다. 이미 확인한 소규모 평가셋을 재사용한 보정되지 않은 연구 결과로, 독립 검증이나 인과 효과 또는 실시간 코칭을 뜻하지 않습니다. 후반 표본에는 해당 시점까지 진행 중인 경기만 남습니다.',
 'No separately trained temporal models are installed; no probability curve is estimated.':'따로 학습한 시점별 모형이 설치되지 않아 확률 곡선을 추정하지 않습니다.',
 'Temporal model and match data sources differ; probabilities are disabled.':'시점별 모형과 경기 자료의 출처가 달라 확률을 제공하지 않습니다.',
 'Synthetic demonstration only; no real-match performance claim.':'합성 자료 시연이며 실제 경기 성능을 주장하지 않습니다.',
 'Temporal model or snapshot is invalid; probabilities are disabled.':'시점별 모형 또는 관측 자료가 유효하지 않아 확률을 제공하지 않습니다.',
 'Synthetic demo: fictional player and matches for presentation. These are not Riot results or evidence of real-world model accuracy.':'합성 데모: 발표용 가상 플레이어와 경기입니다. 실제 Riot 결과나 실제 환경에서의 모형 정확도를 입증하는 자료가 아닙니다.',
 'Model artifact is invalid; predictions are disabled.':'저장 모형이 유효하지 않아 예측을 제공하지 않습니다.',
 'No trained model is installed. No real-match prediction performance is established.':'학습 모형이 설치되지 않았으며 실제 경기 예측 성능을 확인하지 못했습니다.',
 'Synthetic demo only. Evaluation measures a fictional data generator, not real League of Legends performance.':'합성 자료 시연입니다. 평가는 가상 자료 생성기의 결과를 측정하며 실제 리그 오브 레전드 성능을 나타내지 않습니다.',
 'Deep MLP retrospective pilot. Small, previously viewed holdout; no calibrated or general accuracy established.':'심층 MLP의 과거 경기 예비 실험입니다. 이미 확인한 소규모 평가 자료를 사용했으며 확률 보정이나 일반적인 정확도를 검증하지 않았습니다.',
 'Retrospective minute-10 model. Holdout results apply only to the documented dataset.':'과거 경기의 10분까지의 정보를 사용하는 모형입니다. 평가 결과는 명시된 자료에만 적용됩니다.',
 'No complete eligible minute-10 snapshot is available for this match.':'이 경기에는 조건에 맞는 완전한 10분까지의 스냅샷이 없습니다.',
 'Unsupported team or data provenance.':'지원하지 않는 팀 또는 자료 출처입니다.',
 'Model and match data sources differ; this model cannot estimate this match.':'모형과 경기 자료의 출처가 달라 이 모형으로 해당 경기를 추정할 수 없습니다.',
 'Snapshot or model is invalid; prediction is unavailable.':'관측 자료 또는 모형이 유효하지 않아 예측을 제공할 수 없습니다.',
 'The same holdout was previously viewed for the logistic baseline. This is an exploratory comparison, not fresh independent validation.':'로지스틱 회귀 기준선에서 이미 확인한 평가 자료를 재사용합니다. 탐색적 비교이며 새로운 독립 검증이 아닙니다.',
 'Exploratory comparison on the already-viewed, unchanged holdout. RF/XGBoost parameters were chosen after that holdout had been seen, without tuning them on its results. This is not fresh independent validation and does not select or replace the active MLP. The lost historical 1,000-match results are not reproduced by this experiment.':'이미 확인한 동일 평가셋의 탐색적 비교입니다. RF/XGBoost 설정은 평가셋을 본 뒤 정했으며 그 결과에 맞춘 튜닝은 하지 않았습니다. 새로운 독립 검증이나 현재 MLP의 교체·선정을 뜻하지 않습니다. 유실된 과거 1,000경기 결과를 이 실험으로 재현하지 않았습니다.',
 'XGBoost is not installed in this Python environment; no dependency was installed.':'현재 Python 환경에 XGBoost가 설치되지 않았으며 추가 의존성을 설치하지 않았습니다.',
 'Current account context from Riot, cached for up to five minutes. It is not the rank or mastery at the time of the selected match and is not used by the historical predictor. Mastery points reflect recorded play, not verified expertise.':'Riot에서 조회한 현재 계정 정보이며 최대 5분간 캐시합니다. 선택한 경기 당시의 랭크·숙련도가 아니며 과거 경기 예측에 사용하지 않습니다. 숙련도 점수는 플레이 기록이며 검증된 전문성을 뜻하지 않습니다.',
 'This match has no validated champion ID.':'이 경기에는 확인된 챔피언 ID가 없습니다.',
 'No current solo/flex rank entries were returned.':'현재 개인/2인·자유 랭크 기록이 반환되지 않았습니다.',
 'Riot returned an invalid rank response; no rank is inferred.':'Riot 랭크 응답이 올바르지 않아 랭크를 추정하지 않습니다.',
 'Riot returned no mastery record for this champion.':'Riot에서 이 챔피언의 숙련도 기록을 반환하지 않았습니다.',
 'Riot returned an invalid mastery response; no level or points are inferred.':'Riot 숙련도 응답이 올바르지 않아 레벨이나 점수를 추정하지 않습니다.',
 'Riot returned an invalid account response.':'Riot 계정 응답이 올바르지 않습니다.',
 'Live lookup needs RIOT_API_KEY in the backend .env file.':'실제 조회를 사용하려면 백엔드 .env에 RIOT_API_KEY를 설정해야 합니다.',
 'Riot did not respond in time. Please try again.':'Riot 응답 시간이 초과되었습니다. 다시 시도하세요.',
 'Riot is temporarily unreachable. Please try again.':'일시적으로 Riot에 연결할 수 없습니다. 다시 시도하세요.',
 'The backend Riot key is invalid or expired. Development keys expire after 24 hours.':'백엔드 Riot 키가 유효하지 않거나 만료되었습니다. 개발용 키는 24시간 뒤 만료됩니다.',
 'Riot could not find this player or match. Check Riot ID, tagline and platform.':'Riot에서 플레이어 또는 경기를 찾지 못했습니다. 라이엇 ID·태그·지역을 확인하세요.',
 'Riot could not complete the request. Please try again later.':'Riot에서 요청을 완료하지 못했습니다. 나중에 다시 시도하세요.',
 'Riot returned an unreadable response. Please try again.':'Riot 응답을 읽을 수 없습니다. 다시 시도하세요.',
 'Choose a supported platform.':'지원하는 지역을 선택하세요.',
 'Enter a game name and tagline without the # separator.':'# 구분자를 제외한 게임 이름과 태그를 입력하세요.',
 'Showing a saved Riot analysis (cached for up to five minutes).':'저장된 Riot 분석 결과입니다(최대 5분간 캐시).',
 'Riot returned an incomplete player record.':'Riot 플레이어 기록이 불완전합니다.',
 'Riot returned an incomplete match list.':'Riot 경기 목록이 불완전합니다.',
 'Ineligible or incomplete match records were skipped.':'분석 조건에 맞지 않거나 불완전한 경기 기록은 제외했습니다.',
 'A mismatched match record was skipped.':'요청과 일치하지 않는 경기 기록은 제외했습니다.',
 'Some timelines are incomplete; those matches have no historical prediction.':'일부 타임라인이 불완전하여 해당 경기의 과거 시점 예측을 제공하지 않습니다.',
 'Some timelines are unavailable; those matches have no historical prediction.':'일부 타임라인을 이용할 수 없어 해당 경기의 과거 시점 예측을 제공하지 않습니다.',
 'One match was no longer available from Riot and was skipped.':'Riot에서 더 이상 제공하지 않는 경기 한 개를 제외했습니다.',
 'Only part of the match history loaded.':'경기 기록의 일부만 불러왔습니다.',
 "No eligible ranked Summoner's Rift games were found in the requested recent history. Remakes and other queues are excluded.":'요청한 최근 기록에 분석 가능한 소환사의 협곡 랭크 경기가 없습니다. 다시하기와 다른 대전 유형은 제외합니다.',
 'Riot lookup failed; showing previously saved data, up to seven days old.':'Riot 조회에 실패하여 최대 7일 전까지 저장된 자료를 표시합니다.',
 'trained':'학습 완료','not trained':'학습 전','synthetic demo':'합성 데모','invalid':'유효하지 않음','riot':'Riot 실제 경기','synthetic':'합성 자료','Deep MLP (16-8-4)':'심층 MLP (16-8-4)',
};

const patterns:[RegExp,(...parts:string[])=>string][]=[
 [/^([\d.]+) CS\/min in this match\. Review a few waves you missed and set a small personal farming target; this is a review prompt, not a rank benchmark\.$/,v=>`이 경기의 분당 CS는 ${v}입니다. 놓친 미니언 웨이브를 복기하고 작은 개인 파밍 목표를 세워 보세요. 복기 안내이며 랭크 기준치는 아닙니다.`],
 [/^You recorded ([\d.]+) CS\/min\. Compare this with your own games on the same champion and role\.$/,v=>`분당 CS ${v}를 기록했습니다. 같은 챔피언·역할로 플레이한 자신의 경기와 비교해 보세요.`],
 [/^You died (\d+) times\. Use the replay to review the minute before each death; aggregate data cannot establish positioning or intent\.$/,v=>`${v}번 사망했습니다. 리플레이에서 각 데스 1분 전을 살펴보세요. 집계 자료만으로 위치 선정이나 의도를 판단할 수는 없습니다.`],
 [/^You participated in (\d+)% of your team's kills\. Review when you could safely join allies and when farming was more valuable\.$/,v=>`팀 킬의 ${v}%에 관여했습니다. 안전하게 아군과 합류할 수 있었던 시점과 파밍이 더 중요했던 시점을 복기하세요.`],
 [/^Vision score: ([\d.]+) over ([\d.]+) minutes\. Review your ward timing around objectives; vision score alone does not prove ward quality\.$/,(score,time)=>`${time}분 동안 시야 점수 ${score}를 기록했습니다. 오브젝트 전후의 와드 설치 시점을 살펴보세요. 시야 점수만으로 와드의 품질을 입증할 수는 없습니다.`],
 [/^(\d+) wins from (\d+) recent eligible ranked games\. This small, player-selected sample is descriptive and does not establish a long-term skill or improvement trend\.$/,(wins,games)=>`최근 분석 가능한 랭크 ${games}경기에서 ${wins}승을 기록했습니다. 플레이어를 선택해 얻은 작은 표본의 기록이며 장기적인 실력이나 개선 추세를 입증하지 않습니다.`],
 [/^Average ([\d.]+) CS\/min and (\d+)% kill participation\. Choose one review goal and compare future games in the same role\.$/,(cs,kp)=>`평균 분당 CS ${cs}, 킬 관여율 ${kp}%입니다. 복기 목표 하나를 정하고 같은 역할의 이후 경기와 비교하세요.`],
 [/^At least (\d+) other loaded games in the same known role are needed for a personal comparison\. No benchmark is invented\.$/,n=>`개인 비교에는 같은 역할의 다른 경기 최소 ${n}개가 필요합니다. 비교 기준을 임의로 만들지 않습니다.`],
 [/^In (\d+) other loaded games in the (same champion and role|same role), you averaged ([\d.]+) CS\/min, (\d+)% kill participation and ([\d.]+) vision\/min\. This match: ([\d.]+), (\d+)% and ([\d.]+)\. Review differences in matchup, duration and game state before setting a goal; this small sample is not a skill ranking or a causal explanation\.$/,(games,basis,cs,kp,vision,ownCs,ownKp,ownVision)=>`${basis==='same role'?'같은 역할':'같은 챔피언·역할'}의 다른 ${games}경기 평균은 분당 CS ${cs}, 킬 관여율 ${kp}%, 분당 시야 점수 ${vision}입니다. 이번 경기는 각각 ${ownCs}, ${ownKp}%, ${ownVision}입니다. 목표를 정하기 전에 상대 조합·경기 시간·상황의 차이를 확인하세요. 이 작은 표본은 실력 순위나 인과관계의 설명이 아닙니다.`],
 [/^Riot rate limit reached\. Retry in (\d+) seconds\.$/,n=>`Riot 요청 한도에 도달했습니다. ${n}초 뒤 다시 시도하세요.`],
 ];

export function translateApiText(text:string):string|undefined{
 if(Object.hasOwn(apiMessages,text))return apiMessages[text]
 for(const [pattern,format] of patterns){const match=text.match(pattern);if(match)return format(...match.slice(1))}
 // The backend joins known warning sentences. Translate each without touching unknown upstream text.
 for(const [english,korean] of Object.entries(apiMessages)){
  if(text.startsWith(english+' '))return `${korean} ${translateApiText(text.slice(english.length+1))??text.slice(english.length+1)}`
 }
 const rate=text.match(/^Riot rate limit reached\. Retry in (\d+) seconds\. (.+)$/)
 if(rate)return `Riot 요청 한도에 도달했습니다. ${rate[1]}초 뒤 다시 시도하세요. ${translateApiText(rate[2])??rate[2]}`
 return undefined
}
