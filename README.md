# icse2019

These Python files were used to calculate social capital ... for paper .....

Required dependencies:
pickle
sqlalchemy
pandas
scipy

In the MySQL database, there are the following tables:
users
commits
ght_namsor_s (created using the MySQL query provided in `MySQL_queries/ght_namsor_s`

Procedure of running the code: 
1. Use `MySQL_queries/filter_valid_users` to find valid users. For all valid users, run `determine_gender.py` to determine their genders.

2. Run `sample_user.py` to get a balanced sample of equal number of male and female contributors. The result is saved in `data/uid.list`.

3. Run `setup.py`, which reads files `dict/alias_map_b.dict`,
`dict/reverse_alias_map_b.dict`, and `data/uid.list`, and generates files
`data/pid.list`, `data/all_contributors.list`, `dict/contr_projs.dict`,
`data/all_projs.list`, and `dict/proj_contrs_count.dict`.

4. Run `get_user_info.py`, `get_proj_info.py`, and `get_user_proj_info.py`. They write to `data/results_users.csv`, `data/results_proj.csv`, and `data/results_user_proj.csv` repectively.

5. Run `merge_result.py` to combine these tables. The result will be saved in `data/proj_user_proj.csv`, which will be used for data analysis.