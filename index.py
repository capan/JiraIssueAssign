from jira import JIRA
import numpy as np
from textblob.classifiers import NaiveBayesClassifier
import os
import time
import datetime as d

# Credentials
user_name = 'username'
password = 'secret'
mail_password = 'mail_secret'
train = []
start_time = time.time()

# Jira Server Connection
# Write your domain
options = {

    'server': 'http://your.domain.adress'}

# Authentication
try:

    jira = JIRA(options, basic_auth=(f'{user_name}', f'{password}'))

except BaseException as Be:

    print(Be)

props = jira.application_properties()

# Write your JQL to find all closed issues
# Fetch all closed issues to train classifier
 
all_closed_issues = jira.search_issues(
    'resolution in (Çözüldü, "Daha Sonra Çözülecek" ,"İptal Edildi" ,Mükerrer ,"Yeniden Tekrarlanamadı" , "İptal Edildi") and assignee is not EMPTY  order by createdDate  asc', maxResults=False
)

for i in range(0, len(all_closed_issues)):

    train.append((str(all_closed_issues[i].key.split('-')[0]) + ' ' + str(

        all_closed_issues[i].fields.summary), all_closed_issues[i].fields.assignee.name))

cl = NaiveBayesClassifier(train)

# Find all issues without an assignee to assign them automatically

all_open_issues = jira.search_issues(
    'assignee = EMPTY AND (category = IG-Ankara OR category = YY-Ankara)'
)
for i in range(0, len(all_open_issues)):

    issue = str(all_open_issues[i].key.split('-')[0]) + \
        ' ' + str(all_open_issues[i].fields.summary)

    print(all_open_issues[i].key,' can be assigned to : ',cl.classify(issue))

    jira.assign_issue(all_open_issues[i].key,cl.classify(issue))

# Write total execution time of the script for information.
total_time_lapse  = time.time() - start_time
cur_date = d.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"--- Total Time:  {total_time_lapse} seconds ---")
