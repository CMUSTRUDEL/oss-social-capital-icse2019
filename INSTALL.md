To reproduce the model in our paper, one can run [R/survival_analysis.R](R/survival_analysis.R). `survival_analysis.R` reads data from 
`surv_data.csv`, which one can obtain by downloading and upzipping [data/surv_data_anonymized.csv.zip](data/surv_data_anonymized.csv.zip) and saving it in the
same directory as the file `survival_analysis.R`.

`survival_analysis.R` requires the following libraries: `survival`, `coxme`, `htmlTable`, `OIsurv`, `sqldf`, `ggplot2`, and `survminer`.

To reproduce the model of survey result, one can run [R/survey.R](R/survey.R). `survey.R` reads data from `survey.csv`, which can be found in the [data/](data/) folder.

`survey.R` requires the following libraries: `psy`, `Hmisc`, `pls`, `pscl`, and `pROC`.
