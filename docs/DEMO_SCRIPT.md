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
