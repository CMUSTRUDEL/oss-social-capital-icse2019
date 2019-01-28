[![DOI](https://zenodo.org/badge/167657061.svg)](https://zenodo.org/badge/latestdoi/167657061)

## Overview

This research artifact accompanies our ICSE 2019 paper 
["Going Farther Together: The Impact of Social Capital on 
Sustained Participation in Open Source"](https://cmustrudel.github.io/papers/icse19social.pdf).
If you use the artifact, please consider citing:

```
@inproceedings{QiuNBSV19,
  author = {Qiu, Huilian Sophie and 
  		Nolte, Alexander and 
  		Brown, Anita and 
  		Serebrenik, Alexander and 
  		Vasilescu, Bogdan},
  title = {Going Farther Together: The Impact of Social Capital on Sustained Participation in Open Source},
  booktitle = {Proceedings of the 41st International Conference on Software Engineering (ICSE) 2019, Montreal, Canada},
  note = {to appear},
  organization = {IEEE},
  year = {2019},
}
```

The artifact consists of three main parts:

1. **Data collection** scripts, written in Python.

	The code can be used to select open source contributors, collect their GitHub projects, gather data such as contributors’ years of experience on GitHub, and projects’ age and size. The code also calculates social capital measures, including *team familiarity*, *recurring cohesion*, and *heterogeneity of programming language expertise*. 

	The final output is a csv file, each row of which is a data point used in our survival analysis. Each row consists of information *per person per project per quarter* (three-month time window), including all the social capital measures.

	The code was implemented in Python 2 and tested on a Linux machine. Required dependencies: `pymysql`, `sqlalchemy`, `numpy`, `scipy`, `sklearn`, and `pandas`. You also need to have (access to) a MySQL dump of [GHTorrent](http://ghtorrent.org).


2. The [**survey instrument**](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/survey_instrument.pdf) used in the paper.

3. **Survey analysis** scripts, written in R.

We give more details on data collection scripts next.

## Data Collection

### Tables in the MySQL database:

In addition to the standard GHTorrent tables, we created a table 
[`ght_namsor_s`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/MySQL_queries/ght_namsor_s), containing inferred gender data kindly provided by [NamSor](https://www.namsor.com) (thanks, Elian Carsenat!) 


### How to run the code: 

1. Use [`MySQL_queries/filter_valid_users`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/MySQL_queries/filter_valid_users) to find valid users. 

2. Run [`sample_user.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/sample_user.py) to construct a balanced sample of male and female contributors. The result is saved in `data/uid.list`.
In order to obtain a sample with equal number of men and women,
`sample_user.py` calls our gender classifier to determine users'
genders.
The code for the gender classifier is stored in the `gender/` folder. 
Details about these files are in the following section.

3. Run [`setup.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/setup.py), which reads the files `dict/alias_map_b.dict`,
`dict/reverse_alias_map_b.dict`, and `data/uid.list`, and generates files
`data/pid.list`, `data/all_contributors.list`, `dict/contr_projs.dict`,
`data/all_projs.list`, and `dict/proj_contrs_count.dict`.

4. Run [`get_user_info.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/get_user_info.py), [`get_proj_info.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/get_proj_info.py), and [`get_user_proj_info.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/get_user_proj_info.py). They write to `data/results_users.csv`, `data/results_proj.csv`, and `data/results_user_proj.csv` repectively.

5. Run [`merge_result.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/merge_result.py) to combine these tables. The result will be saved in `data/proj_user_proj.csv`, which will be used for data analysis.

### To determine gender:

Our gender classifier uses names' n-grams as well as results from 
two other existing gender classifiers, [NamSor](https://www.namsor.com) 
and [genderComputer](https://github.com/tue-mdse/genderComputer) 
as features.

In the `gender/` folder are two Python files that demostrate how 
our gender classifer works.
First, [`get_feature.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/gender/get_feature.py) reads users' 
information from the MySQL `ght_namsor_s` table, which contains 
users' combined data from GHTorrent and origin and gender 
information obtained from [NamSor](https://www.namsor.com). 
Then it gets classification results from [genderComputer](https://github.com/tue-mdse/genderComputer).
To get a better result from genderComputer, we need to know the 
user's country. 
For this, we use the data provided by Namsor on one's origin, 
computed based on their names. 

There are other gender classifiers one can use, e.g., [genderize.io](https://genderize.io). 
To use them, simply make the result a new feature in the model. 

In [`determine_gender.py`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/gender/determine_gender.py), our 
classifier divides the name into n-grams and uses them as 
additional features.
The result will be written to `data/gender.csv`, which will later 
be used in `sample_user.py` for balance sampling as described above.

## Data analysis

### Survey 

The survey analysis script is [`survey.R`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/R/survey.R). It contains
code to calculate reliability measures, correlations, plots, and conduct logistic regression analysis on the collected survey data.

### Survival analysis

The models as reported in the paper are created by the
[`survival_analysis.R`](https://github.com/CMUSTRUDEL/oss-social-capital-icse2019/blob/master/R/survival_analysis.R) R script.
We have also included an annonymous version of data we used for this paper in [data/surv_data_anonymized.csv.zip](data/surv_data_anonymized.csv.zip)
Each row in the csv file is one data point in our model. It represents one user's activity in one project during one three-month window.
The csv file consists of 34 columns. Those with prefix "u_" are information about users and those start with "p_" are about projects:
- `u_age` is the number of three-month windows since the user's first activity.
- `u_commits_to_date` is the number of commits made by this user across all projects up to that three-month window.
- `u_email` is the md5 hash of the user's email address.
- `u_follower` is the number of followers the user had up to that three-month window.
- `u_gender` is the user's gender.
- `u_id` is the id of the user in the GHTorrent dataset `users` table.
- `u_login` is the md5 has of the user's login.
- `u_nichewidth` is the number of programming languages that the user had used up to that three-month window.
- `u_projects_to_date` is the number of projects to which the user had submitted commits up to that three-month window.
- `u_temp_failure` is a binary indicator of whether the user had been inactive for half a year (2 three-month windows).
- `u_temp_failure_1_year` is a binary indicator of whether the user had been inactive for a year (4 three-month windows).
- `u_window_active_to_date` is the number of three-month windows during whith the user had submitted commits.
- `window_num` represents the current three-month window. 2008 Jan to 2008 Mar will be `window_num = 1`.
- `owner_company` is a binary indicator of whether the owner of the repository displays their company in their profile.
- `owner_gender` is the repository owners' genders, with -1 representing male, 1 female, and 0 unknown.
- `p_id` is the id of the project in the GHTorrent dataset `projects` table.
- `u_is_major` is a binary indicator of whether the user is a major contributor (more than 5% commits) to that project.
- `u_is_owner` is a binary indicator of whether the user is the owner of that project.
- `u_pr_merge` is a binary indicator of whether the user can merge pull request in that project.
- `p_age` is the number of three-month windows since the creation of that project.
- `p_div_langdenom` is the value of the programming language diversity of that project `p_id` in that window `window_num`.
- `p_fam_no_decay` is the value of the team familiarity of that project in that window.
- `p_lang` is the major programming language of that project.
- `p_num_commits` is the number of commits of that project in that window.
- `p_num_commits_to_date` is the total number of commits of that project since is creation.
- `p_num_stars` is the project's number of stars in that window.
- `p_num_users_to_date` is the number of users who had sent commits to the project up to that window.
- `p_owner` is the project owner's id in GHTorrent dataset `users` table.
- `p_recurring_co` is the value of the recurring cohesion of that project in that window.
- `p_sharenewcomers` is the percentage of new GitHub users out of the users who had sent commits to that project.
- `p_sharenewcomers` is the percentage of new users to that project out of the users who had sent commits to that project.
- `p_team_size`
- `p_windows_active_to_date` is the number of three-month windows that the project received commits.
- `window` is the date format of three-month window.

## License

[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
