library(survival)
library(coxme)
library(car)
library(htmlTable)
library(OIsurv)
library(sqldf)
# if (!require("devtools")) install.packages("devtools")
# devtools::install_github("mkuhn/dict")
library("dict")
library(ggplot2)
library(survminer)


## Read data
surv_data <- read.csv("../data/surv_data.csv", sep=",", stringsAsFactors = FALSE) 
table(surv_data$u_gender)
## Preliminaries

# Sanity checks for raw data
nrow(surv_data)
names(surv_data)
length(unique(surv_data$u_id)) 
length(unique(surv_data$p_id)) 

# Basic gender stats
table(sqldf("select u_id, u_gender from surv_data group by u_id")$u_gender)
# Fix late_abandoners few empty entries
surv_data = subset(surv_data, u_gender != "" & u_gender != "0")

# Overview of time windows 
windows = sort(unique(surv_data$window))
windows

# Overview of programming languages
t = table(surv_data$p_lang)
langs = names(t[t>=10000])
langs

# Group infrequent languages
d_langs = dict()
for (l in langs){
  d_langs[[ l ]] = l
}
d_langs$keys()
d_langs$values()
d_langs[[ "" ]] = "OTHER"
str(d_langs$get("PHP1", "OTHER"))

surv_data$p_lang_simple = unlist(lapply(surv_data[,c('p_lang')], function(x) { d_langs$get(x[1], "OTHER") } ))
str(surv_data$p_lang)
str(surv_data$p_lang_simple)

tail(surv_data[,c("p_lang","p_lang_simple")])
table(surv_data$p_lang)
table(surv_data$p_lang_simple)

# Record language as late_abandoners factor
surv_data$f_p_lang = as.factor(surv_data$p_lang)
surv_data$f_p_lang_simple = as.factor(surv_data$p_lang_simple)

# Record user id as late_abandoners factor
length(unique(surv_data$u_id))
surv_data$u_id = as.factor(surv_data$u_id)

# Fix language diversity, it was reverse coded
surv_data$lang_div = 1 - surv_data$p_div_langdenom

# Record gender=F as factor
table(surv_data$u_gender)
surv_data$u_gender_female = surv_data$u_gender == "Female"

# Count time as months (instead of quarters)
summary(surv_data$u_windows_active_to_date)
surv_data$u_months_active = (surv_data$u_windows_active_to_date+1) * 3
surv_data$u_months_active_start = surv_data$u_months_active - 3

## More interesting things

# Label as "abandoned" those users who stopped contributing for late_abandoners year
surv_data$u_dead = surv_data$u_temp_failure_1_year
surv_data$u_dead_half = surv_data$u_temp_failure

# Compute helper stats per user, aggregating over time windows
helper_stats = sqldf("select u_id, u_gender, 
                     count(distinct window_num) as 'num_windows',
                     count(distinct p_id) as 'num_projects',
                     max(p_team_size) as 'max_team_size',
                     max(u_projects_to_date) as 'num_projs',
                     max(window_num) as 'last_window',
                     min(window_num) as 'first_window',
                     sum(u_dead) as 'num_temp_deaths',
                     sum(u_dead_half) as 'num_temp_deaths_half',
                     max(u_months_active) as 'months_active'
                     from surv_data 
                     group by u_id")

# Some people in the data have more than one 1-year inactivity gap. 
# We will filter them out from subsequent modeling
nrow(helper_stats)
nrow(helper_stats[helper_stats$num_temp_deaths >= 1,])
nrow(helper_stats[helper_stats$num_temp_deaths_half >= 1,])
nrow(helper_stats[helper_stats$num_temp_deaths > 1,])
table(helper_stats[helper_stats$num_temp_deaths > 1, ]$u_gender)
mean(helper_stats$months_active)
mean(helper_stats$num_projects)
median(helper_stats$num_projects)
helper_female = helper_stats[helper_stats$u_gender=="Female",]
helper_male = helper_stats[helper_stats$u_gender=="Male", ]
cliff.delta(helper_female$months_active, helper_male$months_active)
cliff.delta(helper_female$num_projects, helper_male$num_projects)

when_died_last = sqldf("select u_id, 
                       max(window_num) as 'when_died_last', 
                       u_windows_active_to_date 
                       from surv_data
                       where u_dead=1
                       group by u_id")
# View(when_died_last)
last_window = sqldf("select u_id, 
                    max(window_num) as 'last_window', 
                    u_windows_active_to_date 
                    from surv_data
                    group by u_id")
# View(last_window)
died_last_window = merge(when_died_last, last_window)
# View(died_last_window)

# Apply the filters, finally
# - first_window>=17 means only look at people who started after January 2012
# - first_window!=36 means they did not start in the last observable window
# - num_temp_deaths==1 means they died exactly one time (death = 1 year of inactivity)
# - the last long conditional checks that they died in their last window
dead_on_time = helper_stats[helper_stats$first_window>=17 & helper_stats$first_window!=36 &
                              ((helper_stats$num_temp_deaths==1 & 
                                  helper_stats$u_id %in% died_last_window[died_last_window$when_died_last==died_last_window$last_window,]$u_id)),]

nrow(dead_on_time)
table(dead_on_time$u_gender)


# This adds to the data the people who never died, as controls
alive_or_dead_on_time = helper_stats[helper_stats$first_window>=17 & helper_stats$first_window!=36 &
                                       ((helper_stats$num_temp_deaths==1 & 
                                           helper_stats$u_id %in% died_last_window[died_last_window$when_died_last==died_last_window$last_window,]$u_id) |
                                          helper_stats$num_temp_deaths==0),]
nrow(alive_or_dead_on_time)
# View(alive_or_dead_on_time)

# From the panel data, keep only the rows corresponding to valid users
nrow(surv_data)
length(unique(surv_data$u_id))
length(unique(alive_or_dead_on_time$u_id))

filtered = subset(surv_data, 
                  u_id %in% alive_or_dead_on_time$u_id
                  & u_gender > 0
                  & u_gender != ""
                  & u_months_active <= 60)
nrow(filtered)

# Num users who disengaged
length(unique(subset(filtered, u_dead==1)$u_id))
# Num users in the control group
ctrl = setdiff(unique(subset(filtered, u_dead==0)$u_id),
               unique(subset(filtered, u_dead==1)$u_id))
length(ctrl)

# Aggregate data per person across all their time windows
# For robustness, compare two aggregations

fs.max = sqldf("select u_id, window_num, u_months_active_start, u_months_active, 
               max(u_gender_female) as u_gender_female, 
               max(u_dead) as u_dead,
               max(u_commits_to_date) as u_commits_to_date,
               max(u_followers) as u_followers, 
               max(p_num_stars) as p_num_stars,
               max(p_team_size) as p_team_size, 
               max(p_age) as p_age,
               max(p_num_commits) as p_num_commits,
               max(p_num_users_to_date) as p_num_users_to_date,
               max(p_sharenewcomers) as p_sharenewcomers,
               max(p_sharenewcomers_this) as p_sharenewcomers_this,
               max(u_nichewidth) as u_nichewidth, 
               max(p_fam_no_decay) as p_fam_no_decay,
               max(p_recurring_co) as p_recurring_co, 
               max(p_div_langdenom) as p_div_langdenom,
               sum(u_is_owner) as u_is_owner, 
               sum(u_is_major) as u_is_major,
               count(distinct p_id) as u_num_projs,
               max(p_num_commits_to_date) as p_num_commits_to_date,
               sum(owner_company) as p_owner_company,
               sum(u_pr_merge) as u_pr_merge,
               sum(case when owner_gender = 1 then 1 else 0 end) as p_owner_female,
               sum(case when owner_gender = -1 then 1 else 0 end) as p_owner_male,
               sum(case when owner_gender = 0 then 1 else 0 end) as p_owner_unknown
               from filtered
               group by u_id, window_num")
table(fs.max$u_gender_female)
# View(fs.max)

fs.avg = sqldf("select u_id, window_num, u_months_active_start, u_months_active, 
               max(u_gender_female) as u_gender_female, 
               max(u_dead) as u_dead,
               avg(u_commits_to_date) as u_commits_to_date,
               avg(u_followers) as u_followers, 
               avg(p_num_stars) as p_num_stars,
               avg(p_team_size) as p_team_size, 
               avg(p_age) as p_age,
               avg(p_num_commits) as p_num_commits,
               avg(p_num_users_to_date) as p_num_users_to_date,
               avg(p_sharenewcomers) as p_sharenewcomers,
               avg(p_sharenewcomers_this) as p_sharenewcomers_this,
               avg(u_nichewidth) as u_nichewidth, 
               avg(p_fam_no_decay) as p_fam_no_decay,
               avg(p_recurring_co) as p_recurring_co, 
               avg(p_div_langdenom) as p_div_langdenom,
               avg(lang_div) as p_lang_div,
               sum(u_is_owner) as u_is_owner, 
               sum(u_is_major) as u_is_major,
               count(distinct p_id) as u_num_projs,
               avg(p_num_commits_to_date) as p_num_commits_to_date,
               sum(owner_company) as p_owner_company,
               sum(u_pr_merge) as u_pr_merge,
               sum(case when owner_gender = 1 then 1 else 0 end) as p_owner_female,
               sum(case when owner_gender = -1 then 1 else 0 end) as p_owner_male,
               sum(case when owner_gender = 0 then 1 else 0 end) as p_owner_unknown
               from filtered
               group by u_id, window_num")
table(fs.avg$u_gender_female)

# Pick an aggregation

filtered.aggregate = fs.avg
# filtered.aggregate = fs.max
nrow(filtered)
nrow(filtered.aggregate)

# Plot the survival curves for M and F separately

# Ugly version, use the ggplot2 version below instead

# fs.f = filtered.aggregate[filtered.aggregate$u_gender_female == TRUE,]
# nrow(fs.f)
# fs.m = filtered.aggregate[filtered.aggregate$u_gender_female == FALSE,]
# nrow(fs.m)
# S.f = Surv(fs.f$u_months_active_start, fs.f$u_months_active, fs.f$u_dead == 1)
# fit_f = survfit(S.f ~ 1, data=fs.f)
# plot(fit_f) #, log="y", ylim=c(0.01,1))
# S.m = Surv(fs.m$u_months_active_start, fs.m$u_months_active, fs.m$u_dead == 1)
# fit_m = survfit(S.m ~ 1, data=fs.m)
# lines(fit_m, col=2)

ggsurvplot(
  survfit(Surv(filtered.aggregate$u_months_active_start, 
               filtered.aggregate$u_months_active, 
               filtered.aggregate$u_dead) ~ u_gender_female, 
          data = filtered.aggregate),
  size = 1,                 # change line size
  palette = c("#E7B800", "#2E9FDF"),# custom color palettes
  conf.int = TRUE,
  #legend = "none",
  legend.labs = c("Male", "Female"),    # Change legend labels
  legend.title = "Gender",
  legend = c(0.9, 0.8),
  #risk.table.height = 0.25, # Useful to change when you have multiple groups
  xlab = "Time in months",   # customize X axis label.
  break.time.by = 12,     # break X axis in time intervals by 500.
  ggtheme = theme_light()
)
ggsave("base-survival.pdf", width = 6, height = 3)
survdiff(Surv(#filtered.aggregate$u_months_active_start, 
  filtered.aggregate$u_months_active, 
  filtered.aggregate$u_dead) ~ u_gender_female, data = filtered.aggregate)
survfit(Surv(filtered.aggregate$u_months_active_start, 
             filtered.aggregate$u_months_active, 
             filtered.aggregate$u_dead) ~ u_gender_female, 
        data = filtered.aggregate)
# Split data into early disengagers vs the rest
# Model the two groups separately, as they might be affected differently by different factors

early_deaths = unique(filtered.aggregate[filtered.aggregate$u_dead == 1 & 
                                           filtered.aggregate$u_months_active == 3,]$u_id)
length(early_deaths)
# sort(table(filtered.aggregate[filtered.aggregate$u_dead == 1,]$u_months_active))

# Non-early deaths
late_abandoners = subset(filtered.aggregate,
                         !(u_id %in% early_deaths))
nrow(filtered.aggregate)
nrow(late_abandoners)

# Filter out a few outliers

hist(log(late_abandoners$u_followers+1))
table(late_abandoners$u_followers > exp(7))
hist(log(late_abandoners$p_num_stars+1))
table(late_abandoners$p_num_stars > exp(7))
hist(late_abandoners$p_sharenewcomers)
hist(late_abandoners$p_sharenewcomers_this)
hist(log(late_abandoners$u_nichewidth+1))
summary(late_abandoners$u_nichewidth)
table(late_abandoners$u_nichewidth == 0)
table(late_abandoners$u_nichewidth > exp(3))
hist(log(late_abandoners$p_team_size+1))
summary(late_abandoners$p_team_size)
table(late_abandoners$p_team_size > exp(6))
hist(log(late_abandoners$p_div_langdenom+1))
hist(log(late_abandoners$p_fam_no_decay+1))
table(late_abandoners$p_fam_no_decay > exp(3))
hist(log(late_abandoners$p_recurring_co+1))
table(late_abandoners$p_recurring_co > exp(6))

late_abandoners.short = subset(late_abandoners, 
                               u_followers < exp(7)
                               & p_num_stars < exp(7)
                               & u_nichewidth > 0
                               & u_nichewidth < exp(3)
                               & p_team_size < exp(6)
                               & p_fam_no_decay < exp(3)
                               & p_team_size > 0
                               & p_recurring_co < exp(6)
                               & p_team_size >= 1
)
nrow(late_abandoners.short)
length(unique(late_abandoners.short$u_id))

# Check effects

hist(log(late_abandoners.short$p_team_size))
table(late_abandoners.short$p_team_size < 5)
summary(late_abandoners.short$u_followers)
hist(log(late_abandoners.short$u_followers+1))
hist(log(late_abandoners.short$p_num_stars+1))
table(late_abandoners.short$p_num_stars==0)
hist(log(late_abandoners.short$p_div_langdenom+1))
table(late_abandoners.short$p_div_langdenom > 0.1)

# Basic differences between the M-F groups

boxplot(list(F = log(late_abandoners.short[late_abandoners.short$u_gender_female==TRUE & late_abandoners.short$u_dead == 1,]$u_followers+1), 
             M = log(late_abandoners.short[late_abandoners.short$u_gender_female==FALSE & late_abandoners.short$u_dead == 1,]$u_followers+1)))

# boxplot(list(F = log(old_a.short[old_a.short$u_gender_female==TRUE & old_a.short$u_dead == 1,]$p_div_langdenom_sq+1), 
#              M = log(old_a.short[old_a.short$u_gender_female==FALSE & old_a.short$u_dead == 1,]$p_div_langdenom_sq+1)))

boxplot(list(F = log(late_abandoners.short[late_abandoners.short$u_gender_female==TRUE & late_abandoners.short$u_dead == 1,]$p_fam_no_decay+1), 
             M = log(late_abandoners.short[late_abandoners.short$u_gender_female==FALSE & late_abandoners.short$u_dead == 1,]$p_fam_no_decay+1)))

boxplot(list(F = log(late_abandoners.short[late_abandoners.short$u_gender_female==TRUE & late_abandoners.short$u_dead == 1,]$p_recurring_co+1), 
             M = log(late_abandoners.short[late_abandoners.short$u_gender_female==FALSE & late_abandoners.short$u_dead == 1,]$p_recurring_co+1)))

boxplot(list(F = late_abandoners.short[late_abandoners.short$u_gender_female==TRUE & late_abandoners.short$u_dead == 1,]$u_is_major, 
             M = late_abandoners.short[late_abandoners.short$u_gender_female==FALSE & late_abandoners.short$u_dead == 1,]$u_is_major))

boxplot(list(F = log(late_abandoners.short[late_abandoners.short$u_gender_female==TRUE,]$u_is_major+1), 
             M = log(late_abandoners.short[late_abandoners.short$u_gender_female==FALSE,]$u_is_major+1)))

boxplot(list(F = late_abandoners.short[late_abandoners.short$u_gender_female==TRUE,]$u_is_major, 
             M = late_abandoners.short[late_abandoners.short$u_gender_female==FALSE,]$u_is_major))

# Build Cox regression model

m_ph_base_int <- coxph(Surv(u_months_active_start,
                            u_months_active,
                            u_dead == 1) ~
                         log(u_followers+1)
                       + log(p_num_stars+1)
                       + log(u_commits_to_date+1)
                       + (u_is_major>0)
                       + (u_is_owner>0)
                       + p_sharenewcomers_this
                       + log(u_nichewidth+1)
                       + p_lang_div * u_gender_female
                       + log(p_fam_no_decay+1) * u_gender_female
                       + log(p_recurring_co+1) * u_gender_female
                       , data=late_abandoners.short)

summary(m_ph_base_int)

Anova(m_ph_base_int)
Anova(m_ph_base_int, type=2)

# Diagnostics
cox.zph(m_ph_base_int, "rank") 
vif(m_ph_base_int)
dd <- datadist(late_abandoners.short)
options(datadist="dd")

# library(rms)

# Switch to a glm instead of Cox above if you want to plot this interaction
# library(interplot)
# interplot(m = m_ph_base_int, var1 = "u_gender_femaleTRUE", var2 = "p_lang_div")

# library(rcompanion)
# nagelkerke(m_ph_base_int)
# LLf <- m_ph_base_int$loglik[2]
# LL0 <- m_ph_base_int$loglik[1]
# N = nrow(late_abandoners.short)
# as.vector(1 - exp((2/N) * (LL0 - LLf)))
# as.vector((1 - exp((2/N) * (LL0 - LLf))) / (1 - exp(LL0)^(2/N)))


# Model the early abandoners separately

early_abandoners = subset(filtered.aggregate,
                          u_months_active=3)

# Filter out outliers

hist(log(early_abandoners$u_followers+1))
table(early_abandoners$u_followers > exp(7))
hist(log(early_abandoners$p_num_stars+1))
table(early_abandoners$p_num_stars > exp(8))
hist(early_abandoners$p_sharenewcomers)
hist(early_abandoners$p_sharenewcomers_this)
hist(log(early_abandoners$u_nichewidth+1))
summary(early_abandoners$u_nichewidth)
table(early_abandoners$u_nichewidth == 0)
table(early_abandoners$u_nichewidth > exp(2))
hist(log(early_abandoners$p_team_size+1))
summary(early_abandoners$p_team_size)
table(early_abandoners$p_team_size > exp(5))
hist(log(early_abandoners$p_div_langdenom+1))
table(early_abandoners$p_div_langdenom == 1.000e+09)
hist(early_abandoners$p_div_langdenom_sq)
hist(log(early_abandoners$p_fam_no_decay+1))
table(early_abandoners$p_fam_no_decay > exp(4))
hist(log(early_abandoners$p_recurring_co+1))
table(early_abandoners$p_recurring_co > exp(6))

early_abandoners.short = subset(early_abandoners, 
                                u_followers < exp(6) &
                                  p_num_stars < exp(4) &
                                  u_nichewidth > 0 &
                                  u_nichewidth < exp(3) &
                                  p_team_size < exp(7) &
                                  p_team_size > 0 &
                                  p_team_size >= 1)

nrow(early_abandoners)
nrow(early_abandoners.short)
length(unique(early_abandoners.short$u_id))

table(early_abandoners.short$u_dead)

# Use a logistic regression for early abandoners

m_ph_base_int_early <- glm((u_dead == 1) ~
                             log(u_followers+1)
                           + log(p_num_stars+1)
                           + log(u_commits_to_date+1)
                           + (u_is_major>0)
                           + (u_is_owner>0)
                           + p_sharenewcomers_this
                           + log(u_nichewidth+1)
                           + p_lang_div * u_gender_female
                           + log(p_fam_no_decay+1) * u_gender_female
                           + log(p_recurring_co+1) * u_gender_female
                           , data=early_abandoners.short
                           , family="binomial")


vif(m_ph_base_int_early)

summary(m_ph_base_int_early)

anova(m_ph_base_int_early)
Anova(m_ph_base_int_early, type=2)

