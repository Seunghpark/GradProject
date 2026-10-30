# LolAi.gg: short graduation demonstration

Use the existing local build at http://127.0.0.1:8000. Start from the project folder with start.cmd and leave that terminal running. Use a second Cursor terminal for check.cmd. Never open the key file or developer-portal key screen during a presentation.

## 0:00-0:30 - State the implemented problem

Say: "LolAi.gg reviews completed League of Legends ranked matches. It combines Riot match history, descriptive post-match insights and an early-snapshot deep neural network with logistic and constant baselines. The current implementation is React/TypeScript with a FastAPI backend."

## 0:30-1:30 - Demonstrate one genuine player

Enter Molybdite#KR1, choose Korea and Live Riot API, then Analyze player. Allow uncached calls to finish. Confirm the displayed player and the live/cached source label. Repeated requests may correctly show Cached Riot data.

Select one completed match. Explain KDA, CS/min, kill participation and vision score as descriptive statistics. Show the full-match team gold-difference chart. Select another match or filter victories to demonstrate the interaction. Read a review prompt and explain that it suggests a replay review; aggregate statistics cannot prove why a player won or lost.

## 1:30-2:30 - Explain the historical model honestly

Show the historical estimate. Say: "Prediction inputs use the latest complete frame from minutes nine to ten. Later events and final scores are excluded. In this genuine snapshot the selected frames are around minute nine because the next frame is slightly after the strict ten-minute cutoff. The winner is the training label only."

Open Model & evaluation. Say: "The network has three ReLU hidden layers of 16, 8 and 4 units, and 289 learned weights/biases. The pilot contains 104 unique genuine KR matches: 83 earlier training and 21 later evaluation. Both the neural and logistic models use identical train-only scaling and partitions."

Say: "The neural model correctly classified 10 of 21 later games, or 47.6%, versus logistic regression's 12 of 21, or 57.1%. Neural AUC is 0.491 and Brier is 0.373; logistic Brier is 0.264 and the constant baseline is 0.260. Lower Brier is better. Neural training accuracy is 95.2%, so the large gap is consistent with overfitting. The deep model did not improve quality in this pilot. The evaluation set was previously viewed, so this is an exploratory comparison rather than independent validation."

Explain that displayed individual matches may be training examples. They illustrate inference; only the separate holdout supplies evaluation. Do not claim calibration, broad accuracy, superior prediction quality, causal coaching or improved player win rate.

## 2:30-3:00 - Show resilience and limits

Choose Sample demo and analyze DemoPlayer#SKKU. Confirm the fictional source/player label. Match statistics and reviews remain available without a working Riot connection. With the genuine-only model active, synthetic-match probabilities are intentionally unavailable; they must not be presented as genuine predictions.

Say: "The sample keeps the interface demonstrable offline. Research limitations include a small holdout, overlapping players, selection bias and patch drift. More diverse data and independent validation are needed."

## Before recording or submitting

Run check.cmd from a normal terminal and retain its actual result. Verify Export analysis by opening the downloaded JSON and checking its player/source/match count. Rehearse a fresh startup, and verify required report/slides/video against the university rubric. Current known checks and blocks are in QA_RESULTS.md; exact dataset/model evidence is in REAL_MODEL_RESULTS.md.

Earlier uploaded report/PPT files are samples per the user and are not final submission evidence. Deep learning is mandatory and an actual three-hidden-layer MLP is implemented. Use the actual designated report/PPT forms, measured negative result and limitations. Complete adviser review/online signature and final submission before October 30 at 23:59.

## 예상 질문과 답변

**신경망이 실제로 구현되었나요?** 네. 6→16→8→4→1 구조의 세 은닉층 MLP이며 매개변수는 289개입니다. 실제 저장된 가중치로 추론합니다.

**성능이 좋은가요?** 아니요. 원래 21경기 평가에서 MLP는 정확도 47.62%, AUC 0.490909, Brier 0.372683이었습니다. 학습 정확도는 95.18%여서 과적합이 뚜렷합니다. 신경망의 우수성은 입증하지 못했습니다.

**왜 추가 35경기에서는 57.14%인가요?** 표본이 달라서 나온 값입니다. 모형을 바꾸거나 재학습하지 않았으므로 개선으로 볼 수 없습니다. 같은 표본에서 로지스틱은 80.00%였고, MLP의 Brier 0.319481은 상수 기준선 0.267321보다 나빴습니다.

**추가 35경기는 외부 검증인가요?** 아닙니다. 모형과 제외 목록은 미리 고정했지만, 평가 규칙을 회고적으로 정한 편의표본입니다.

**입력에 최종 경기 결과가 들어가나요?** 들어가지 않습니다. 입력은 540~600초 창의 최신 프레임에서 뽑은 골드, 경험치, CS, 킬, 타워, 드래곤의 팀 차이 여섯 개이고, 실제 프레임은 약 9분입니다.

**복기 팁이 승률을 올려 주나요?** 입증하지 않았습니다. 우선순위는 격차 × 동일 가중치 × 최근 일관성이며, 인과 효과가 아니라 복기할 항목의 순서입니다.

**참고 집단은 어떻게 만드나요?** 같은 역할, 패치, 대전 유형으로 제한하고 본인과 불러온 경기를 제외합니다. 지표마다 별도 30경기, 서로 다른 플레이어 10명, 최근 관측 3개가 필요합니다.

**OP.GG를 그대로 가져온 건가요?** 아닙니다. Riot 자료로 직접 분석합니다. OP.GG 공식 MCP 등 외부 자료는 선택적 보조 입력이며 상용 서비스의 모든 기능을 구현한 것은 아닙니다.

**실시간 코칭이 되나요?** 아니요. 완료 경기 분석이 범위입니다. 본인 Live Client 읽기 코드는 있지만 실제 게임에서 검증하지 않았습니다.

**예전 1,000경기 실험 결과는요?** 잃어버린 컴퓨터의 기록이며 원자료와 로그를 복구하지 못했으므로 이 작품의 결과로 제시하지 않습니다.

**API 키는 어디에 있나요?** 서버의 무시된 `backend/.env`에만 있고 브라우저 응답과 내보내기 파일에는 포함되지 않습니다.
