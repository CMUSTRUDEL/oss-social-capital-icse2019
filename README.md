[![DOI](https://zenodo.org/badge/167657061.svg)](https://zenodo.org/badge/latestdoi/167657061)
reStructedText

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

## Survey analysis

The survey analysis script can be found in the R subfolder. It contains
code to calculate reliability measures, correlations, variable plots and conduct
logistic regression analysis on the collected survey data.

## License

[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
