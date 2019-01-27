library(psy)
library(car)
library(Hmisc)
library(pls)
library(pscl)
library(pROC)

df <- read.csv("survey.csv", header=T, as.is=T, sep=",")

# remove empty rows
df <- df[!rowSums((is.na(df))),]

# remove "prefer not to answer" from gender
df <- df[!(df$gender_survey==3),]

# add column for female and male activity and number of programming languages
df$female_active <- with(df, ifelse(df$gender_survey == 0 & df$active == 1, 1, 0))
df$male_active <- with(df, ifelse(df$gender_survey == 1 & df$active == 1, 1, 0))
df$programming_languages <- 0
for (i in 1:length(df$languages)) {
  string <- strsplit(df$languages, ";")
  df$programming_languages[i] = length(string[[i]])
}

# remove text columns
df <- df[ , !names(df) %in% c("id","timestamp","start_contributing","project_application","motivations","responsibilities","stop_reason","languages")]


## calculate cronbachs alpha for all scales
alphas <- vector()

satisfaction <- df[, c("sat1","sat2","sat3","sat5","sat6")]
uwes <- df[, c("uwes1","uwes2","uwes3","uwes4","uwes5","uwes6","uwes7","uwes8","uwes9")]
socap <- df[, c("socap1","socap2","socap3","socap4","socap5","socap6","socap7","socap8","socap9","socap10")]
communication <- df[, c("com_personal","com_comments","com_readcode","com_text","com_video","com_email","com_audio","com_socialnetwork")]
alphas <- c(alphas, cronbach(satisfaction))
alphas <- c(alphas, cronbach(uwes))
alphas <- c(alphas, cronbach(socap))
alphas <- c(alphas, cronbach(communication))
alphas

## calculate correlations
ccs <- as.matrix(df)
R <- rcorr(ccs, type="pearson")$r # spearman
p <- rcorr(ccs, type="pearson")$P

## define notions for significance levels; spacing is important.
mystars <- ifelse(p < .001, "***", ifelse(p < .01, "** ", ifelse(p < .05, "* ", " ")))

## trunctuate the matrix that holds the correlations to two decimal
R <- format(round(cbind(rep(-1.11, ncol(ccs)), R), 2))[,-1]

## build a new matrix that includes the correlations with their apropriate stars
Rnew <- matrix(paste(R, mystars, sep=""), ncol=ncol(ccs))
diag(Rnew) <- paste(diag(R), " ", sep="")
rownames(Rnew) <- colnames(ccs)
colnames(Rnew) <- paste(colnames(ccs), "", sep="")

## remove upper triangle
Rnew <- as.matrix(Rnew)
Rnew[upper.tri(Rnew, diag = TRUE)] <- ""
Rnew <- as.data.frame(Rnew)

## remove last column and return the matrix (which is now a data frame)
Rnew <- cbind(Rnew[1:length(Rnew)-1])
write.csv(Rnew, "correlations.csv")

# gender and perceived expertise (computed gender)
#ageAov = aov(age~gender_computed,data=df)
ageAov = aov(age~gender_survey,data=df)
summary(ageAov)
boxplot(age~gender_survey,data=df, names=c("female","male"))

# gender and perceived expertise (computed gender)
#exp_compAov = aov(exp_comp~gender_computed,data=df)
exp_compAov = aov(exp_comp~gender_survey,data=df)
summary(exp_compAov)
boxplot(exp_comp~gender_survey,data=df, names=c("female","male"))

# gender and years of experience (computed gender)
#exp_yearsAov = aov(exp_years~gender_computed,data=df)
exp_yearsAov = aov(exp_years~gender_survey,data=df)
summary(exp_yearsAov)
boxplot(exp_years~gender_survey,data=df, names=c("female","male"))

# gender and programming languages (computed gender)
#exp_yearsAov = aov(programming_languages~gender_computed,data=df)
programming_languagesAov = aov(programming_languages~gender_survey,data=df)
summary(programming_languagesAov)
boxplot(programming_languages~gender_survey,data=df, names=c("female","male"))

# gender and education (computed gender)
#educationAov = aov(education~gender_computed,data=df)
educationAov = aov(education~gender_survey,data=df)
summary(educationAov)
boxplot(education~gender_survey,data=df, names=c("female","male"))
# gender and satisfaction (computed gender)
#satAov = aov(satAvg~gender_computed,data=df)
satAov = aov(satAvg~gender_survey,data=df)
summary(satAov)
boxplot(satAvg~gender_survey,data=df, names=c("female","male"))

# gender and work satisfaction (computed gender)
#uwesAov = aov(uwesAvg~gender_computed,data=df)
uwesAov = aov(uwesAvg~gender_survey,data=df)
summary(uwesAov)
boxplot(uwesAvg~gender_survey,data=df, names=c("female","male"))

# gender and social capital (computed gender)
#socapAov = aov(socapAvg~gender_computed,data=df)
socapAov = aov(socapAvg~gender_survey,data=df)
summary(socapAov)
boxplot(socapAvg~gender_survey,data=df, names=c("female","male"))

# gender and in person communication (computed gender)
#com_personalAov = aov(com_personal~gender_computed,data=df)
com_personalAov = aov(com_personal~gender_survey,data=df)
summary(com_personalAov)
boxplot(com_personal~gender_survey,data=df, names=c("female","male"))

# gender and communication via comments (computed gender)
#com_commentsAov = aov(com_comments~gender_computed,data=df)
com_commentsAov = aov(com_comments~gender_survey,data=df)
summary(com_commentsAov)
boxplot(com_comments~gender_survey,data=df, names=c("female","male"))

#$nder and communication via reading code (computed gender)
#com_readcodeAov = aov(com_readcode~gender_computed,data=df)
com_readcodeAov = aov(com_readcode~gender_survey,data=df)
summary(com_readcodeAov)
boxplot(com_readcode~gender_survey,data=df, names=c("female","male"))

# gender and communication via video messaging (computed gender)
#com_videoAov = aov(com_video~gender_computed,data=df)
com_videoAov = aov(com_video~gender_survey,data=df)
summary(com_videoAov)
boxplot(com_video~gender_survey,data=df, names=c("female","male"))

# gender and communication via email (computed gender)
#com_emailAov = aov(com_email~gender_computed,data=df)
com_emailAov = aov(com_email~gender_survey,data=df)
summary(com_emailAov)
boxplot(com_email~gender_survey,data=df, names=c("female","male"))


# gender and communication via email (computed gender)
#com_audioAov = aov(com_audio~gender_computed,data=df)
com_audioAov = aov(com_audio~gender_survey,data=df)
summary(com_audioAov)
boxplot(com_audio~gender_survey,data=df, names=c("female","male"))


# gender and communication via social network (computed gender)
#com_socialnetworkAov = aov(com_socialnetwork~gender_computed,data=df)
com_socialnetworkAov = aov(com_socialnetwork~gender_survey,data=df)
summary(com_socialnetworkAov)
boxplot(com_socialnetwork~gender_survey,data=df, names=c("female","male"))


# gender and communication average (computed gender)
#comAvgAov = aov(comAvg~gender_computed,data=df)
comAvgAov = aov(comAvg~gender_survey,data=df)
summary(comAvgAov)
boxplot(comAvg~gender_survey,data=df, names=c("female","male"))

# gender and still being active (computed gender)
#activeAov = aov(active~gender_computed,data=df)
activeAov = aov(active~gender_survey,data=df)
summary(activeAov)
boxplot(active~gender_survey,data=df, names=c("female","male"))


# regression
# selecting males and females
males = df[which(df$gender_survey == 1),]
females = df[which(df$gender_survey == 0),]

# creating training and test sets (80% of females and males)
train <- rbind(males[1:47,], females[1:27,])
test <- rbind(males[48:59,], females[28:34,])

# training the model
model <- glm(active~socapAvg+exp_years,family=binomial(link='logit'),data=train)
summary(model)

#predict train set
p = predict(model, train, type = "response")

#apply roc function
analysis <- roc(response=train$active, predictor=p)

#Find t that minimizes error
e <- cbind(analysis$thresholds,analysis$sensitivities+analysis$specificities)
opt_t <- subset(e,e[,2]==max(e[,2]))[,1]

#Plot ROC Curve
plot(1-analysis$specificities,analysis$sensitivities,type="l",
     ylab="Sensitiviy",xlab="1-Specificity",col="black",lwd=2,
     main = "ROC Curve for Simulated Data")
abline(a=0,b=1)
abline(v = opt_t) #add optimal t to ROC curve

#define classification threshold
opt_t #print t

#predictive accuracy
fitted.results <- predict(model,newdata=test, type='response')
fitted.results <- ifelse(fitted.results > opt_t,1,0)
misClasificError <- mean(fitted.results != test$active)
print(paste('Accuracy',1-misClasificError))
#mean absolute error
#check rmse

# significance of model
anova(model, test="Chisq")

library(stargazer)
stargazer(model)

model1 <- glm(active~age +
              exp_comp +
              exp_years +
              programming_languages +
              education +
              satAvg +
              uwesAvg +
              socapAvg +
              exp_years,family=binomial(link='logit'),data=train)
vif(model1)
summary(model1)