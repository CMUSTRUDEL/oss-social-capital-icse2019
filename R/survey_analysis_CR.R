library(psy)
library(car)
library(Hmisc)
library(sjstats)
library(pls)
library(nFactors)

survey = read.csv("survey.csv", header=T, as.is=T, sep=",")
#survey = read.csv("~/Documents/mizzou/paper-gh-gender-networks/survey/survey2_cleaned.csv", header=T, as.is=T, sep=",")
nrow(survey)
# View(survey)

# remove empty rows
survey = survey[!rowSums((is.na(survey))),]
nrow(survey)
table(survey$gender_survey)

# remove "prefer not to answer" from gender
survey = survey[!(survey$gender_survey==3),]
nrow(survey)

# add column for female and male activity and number of programming languages
survey$female_active = with(survey, ifelse(gender_survey == 0 & active == 1, 1, 0))
survey$male_active = with(survey, ifelse(gender_survey == 1 & active == 1, 1, 0))
# survey$female_active = with(survey, ifelse(gender_computed == 0 & active == 1, 1, 0))
# survey$male_active = with(survey, ifelse(gender_computed == 1 & active == 1, 1, 0))
table(survey$female_active)
table(survey$male_active)

# add columns for team satisfaction and communication
survey$satTeamAvg <- ave(survey$sat2, survey$sat3, survey$sat5)
survey$communicationAvg <- ave(survey$com_personal, survey$com_comments, survey$com_readcode, survey$com_text, survey$com_video, survey$com_email, survey$com_audio, survey$com_socialnetwork)

survey$programming_languages <- 0
for (i in 1:length(survey$languages)) {
  string <- strsplit(survey$languages, ";")
  survey$programming_languages[i] = length(string[[i]])
}

str(survey$programming_languages)




alphas <- vector()

satisfaction <- survey[, c("sat1","sat2","sat3","sat5","sat6")]
satTeam <- survey[, c("sat2","sat3","sat5")]
uwes <- survey[, c("uwes1","uwes2","uwes3","uwes4","uwes5","uwes6","uwes7","uwes8","uwes9")]
socap <- survey[, c("socap1","socap2","socap3","socap4","socap5","socap6","socap7","socap8","socap9","socap10")]
socapBridging <- survey[, c("socap1","socap2","socap3","socap4","socap5","socap6")]
socapBonding <- survey[, c("socap7","socap8","socap9","socap10")]
communication <- survey[, c("com_personal","com_comments","com_readcode","com_text","com_video","com_email","com_audio","com_socialnetwork")]
alphas <- c(alphas, cronbach(satisfaction))
alphas <- c(alphas, cronbach(satTeam))
alphas <- c(alphas, cronbach(uwes))
alphas <- c(alphas, cronbach(socap))
alphas <- c(alphas, cronbach(socapBridging))
alphas <- c(alphas, cronbach(socapBonding))
alphas <- c(alphas, cronbach(communication))
alphas



# gender and age (computed gender)
#ageAov = aov(age~gender_computed,data=survey)
ageAov = aov(age ~ gender_survey, data=survey)
summary(ageAov)
boxplot(age ~ gender_survey, data=survey, names=c("female","male")) 

summary(survey$age)
names(survey)



# gender and perceived expertise (computed gender)
#exp_compAov = aov(exp_comp~gender_computed,data=survey)
exp_compAov = aov(exp_comp~gender_survey,data=survey)
summary(exp_compAov)
boxplot(exp_comp~gender_survey,data=survey, names=c("female","male")) 
eta_sq(exp_compAov)
#omega_sq(exp_compAov)



# gender and years of experience (computed gender)
#exp_yearsAov = aov(exp_years~gender_computed,data=survey)
exp_yearsAov = aov(exp_years~gender_survey,data=survey)
summary(exp_yearsAov)
boxplot(exp_years~gender_survey,data=survey, names=c("female","male")) 
#wilcox.test(exp_years~gender_survey,data=survey)



# gender and programming languages (computed gender)
#exp_yearsAov = aov(programming_languages~gender_computed,data=survey)
programming_languagesAov = aov(programming_languages~gender_survey,data=survey)
summary(programming_languagesAov)
boxplot(programming_languages~gender_survey,data=survey, names=c("female","male")) 
eta_sq(programming_languagesAov)
#omega_sq(programming_languagesAov)



# gender and education (computed gender)
#educationAov = aov(education~gender_computed,data=survey)
educationAov = aov(education~gender_survey,data=survey)
summary(educationAov)
boxplot(education~gender_survey,data=survey, names=c("female","male")) 
summary(survey$education)



# gender and communication (computed gender)
communicationAov = aov(communicationAvg~gender_survey,data=survey)
summary(communicationAov)
boxplot(communicationAvg~gender_survey,data=survey, names=c("female","male")) 
summary(survey$communicationAvg)



# gender and responsibility related to code (computed gender)
#codeAov = aov(code~gender_computed,data=survey)
codeAov = aov(code~gender_survey, data=survey)
summary(codeAov)
boxplot(code~gender_survey, data=survey, names=c("female","male")) 



# gender and responsibility not related to code (computed gender)
#nonCodeAov = aov(nonCode~gender_computed,data=survey)
nonCodeAov = aov(nonCode~gender_survey, data=survey)
summary(nonCodeAov)
boxplot(nonCode~gender_survey, data=survey, names=c("female","male")) 



# gender and satisfaction (computed gender)
#satAov = aov(satAvg~gender_computed,data=survey)
satAov = aov(satAvg~gender_survey,data=survey)
summary(satAov)
boxplot(satAvg~gender_survey,data=survey, names=c("female","male"))



# gender and satisfaction with team (computed gender)
#satTeamAov = aov(satTeamAvg~gender_computed,data=survey)
satTeamAov = aov(satTeamAvg~gender_survey,data=survey)
summary(satTeamAov)
boxplot(satTeamAvg~gender_survey,data=survey, names=c("female","male"))



# gender and work satisfaction (computed gender)
#uwesAov = aov(uwesAvg~gender_computed,data=survey)
uwesAov = aov(uwesAvg~gender_survey,data=survey)
summary(uwesAov)
boxplot(uwesAvg~gender_survey,data=survey, names=c("female","male")) 



# gender and social capital (computed gender)
#socapAov = aov(socapAvg~gender_computed,data=survey)
socapAov = aov(socapAvg~gender_survey,data=survey)
summary(socapAov)
boxplot(socapAvg~gender_survey,data=survey, names=c("female","male")) 



# gender and bridging social capital (computed gender)
survey$socapBridgingAvg = as.numeric(survey$socapBridgingAvg)
socapBridgingAov = aov(socapBridgingAvg~gender_survey,data=survey)
summary(socapBridgingAov)
boxplot(socapBridgingAvg~gender_survey,data=survey, names=c("female","male")) 



# gender and bonding social capital (computed gender)
survey$socapBondingAvg = as.numeric(survey$socapBondingAvg)
socapBondingAov = aov(socapBondingAvg~gender_survey,data=survey)
summary(socapBondingAov)
boxplot(socapBondingAvg~gender_survey,data=survey, names=c("female","male")) 
eta_sq(socapBondingAov)
#omega_sq(socapBondingAov)



# # selecting males and females
# males = survey[which(survey$gender_survey == 1),]
# females = survey[which(survey$gender_survey == 0),]
# 
# # creating training and test sets (80% of females and males)
# train <- rbind(males[1:47,], females[1:27,])
# test <- rbind(males[38:59,], females[28:34,])

# training the model
model <- glm(disengagement ~ satAvg + 
               uwesAvg + 
               socapBridgingAvg + 
               socapBondingAvg + 
               exp_comp + 
               exp_years + 
               education + 
               # gender_computed + 
               gender_survey +
               programming_languages,
             family=binomial(link='logit'),
             data=survey)
vif(model)
summary(model)
Anova(model)
library(pscl)
pR2(model)

# remove rows with active participants
survey = survey[survey$active < 1,]

# gender and stop because of personal reasons (computed gender)
stopPersonalAov = aov(stopPersonal~gender_survey,data=survey)
summary(stopPersonalAov)
boxplot(stopPersonal~gender_survey,data=survey, names=c("female","male")) 
eta_sq(stopPersonalAov)


# gender and stop because of work related reasons (computed gender)
stopWorkAov = aov(stopWork~gender_survey,data=survey)
summary(stopWorkAov)
boxplot(stopWork~gender_survey,data=survey, names=c("female","male")) 

# gender and stop because of project related reasons (computed gender)
stopProjectAov = aov(stopProject~gender_survey,data=survey)
summary(stopProjectAov)
boxplot(stopProject~gender_survey,data=survey, names=c("female","male")) 

