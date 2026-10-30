# Verified English research references

Verified 2026-10-28 from primary publisher/proceedings sources. These are literature references, not this project's measured results. Summaries are compact; do not repeat them to pad the report or transfer published performance values to LolAi.gg.

## E1. Deep representations

Y. LeCun, Y. Bengio, G. Hinton. Deep learning. Nature 521,436-444(2015). DOI: [10.1038/nature14539](https://doi.org/10.1038/nature14539).

The publisher's abstract describes multilayer representation learning and parameter learning through backpropagation. It provides conceptual background for a nonlinear multilayer network; it does not establish performance on this project's small game dataset. Publisher metadata/abstract were available through the primary search result; full article access was unavailable.

## E2. Neural overfitting

N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, R. Salakhutdinov. Dropout: A Simple Way to Prevent Neural Networks from Overfitting. Journal of Machine Learning Research15(56),1929-1958(2014). [Primary publisher](https://www.jmlr.org/papers/v15/srivastava14a.html).

The paper describes randomly removing units during training as a regularization approach. It is relevant to discussing neural overfitting. LolAi.gg uses L2 regularization, not dropout, so this reference is theoretical context and a possible future comparison, not an implemented feature. Publisher abstract and bibliographic record were read.

## E3. LoL sequence-based prediction

A. L. C. Silva, G. L. Pappa, L. Chaimowicz. Continuous Outcome Prediction of League of Legends Competitive Matches Using Recurrent Neural Networks. Proceedings of SBGames2018, Computing Track-Short Papers,639-642(2018). [Primary proceedings PDF](https://www.sbgames.org/sbgames2018/files/papers/ComputacaoShort/188226.pdf).

The paper compares recurrent models on professional match sequences at different game intervals. LolAi.gg instead uses a fixed early snapshot of KR ranked matches and a feedforward MLP. Its different data, time scope and protocol prevent a direct accuracy ranking. The full four-page proceedings text, including match-level split discussion, was read. No DOI was visible, so none is invented.

## Integration

Use these three English papers alongside the three Korean papers in KOREAN_RELATED_WORK.md. Official Riot/scikit-learn documentation can support implementation but is not substituted for the required research-paper count. Mark source-access limits honestly and include an in-text reference number for claims attributed to each paper.
