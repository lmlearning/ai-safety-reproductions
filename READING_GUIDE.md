# Reading the reproduction reports

Every study starts with the original question, what we actually did, and what the result tells us. The detailed sections then give the numerical comparisons, problems and audit records. You can understand the introduction without first reading the paper.

## What kind of work was repeated?

A **new experiment** generates new observations: for example, fresh simulated trials or predictions from a saved model. A **released-data reanalysis** starts with observations the paper's authors already collected and independently repeats the scoring or statistics. It checks whether their numerical result can be recovered; it does not recruit a new participant sample or independently establish that the source data are valid.

A **meta-analysis** combines results from multiple earlier studies. A **pooled estimate** is their weighted summary, rather than one large new trial. Reproducing it can involve rebuilding the effect calculations, weights, uncertainty and comparisons between groups. It does not repeat the original studies or the literature search.

## How to read the numbers

**Percentage points** measure a difference between percentages: 65% versus 50% is a 15-point gap. A **standardized effect size** puts differences measured on different scales onto a common statistical scale. An effect of 0.87 is not an 87% improvement.

A **confidence interval** describes the uncertainty in an estimated quantity under the analysis's assumptions. It is not the range of individual participants' scores. For a difference between groups, zero is the no-difference value; for a ratio, it is one. An interval spanning that value does not establish a difference, and also does not prove the groups are identical.

**Heterogeneity** means the study results differ from one another. Recovering a positive average alongside high heterogeneity does not show that the same benefit occurs in every setting.

**Agreement** concerns how close evaluators' actual scores are. It differs from correlation: two graders could put essays in the same order while consistently awarding different marks. Several reports use an **intraclass correlation coefficient (ICC)** to quantify agreement under a specified statistical model.

## Terms from the model studies

A **checkpoint** is a saved trained model. Running it on test examples is new inference, not new training. **Activations** are internal numerical measurements recorded while a model processes text. A **probe** is a small classifier trained on those measurements; successfully predicting a label does not establish what causes the larger model's behaviour.

## What a successful match establishes

The outcome label applies to the complete central result described in that report. A **strict central reproduction** meets all its adopted criteria. A **near success** retains the earlier strict misses and explains the numerical discrepancy. P165 is separately qualified because material discrepancies remain. None is a claim that every experiment in its paper was repeated.

Large audit counts refer to computational comparisons, such as checking values, input identities or formulas. They are not counts of new participants, independent experiments or independent laboratories. Read a numerical match together with its source assumptions and limitations.
