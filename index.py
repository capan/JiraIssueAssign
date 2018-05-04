from jira import JIRA
from textblob.classifiers import NaiveBayesClassifier
import time
import datetime as d
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import psycopg2

cur_date = d.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
conn = psycopg2.connect("dbname=Jiradb user=postgres password=1 port=5433")
cur = conn.cursor()
print('Program started. (' + cur_date + ')')
user_name = 'user.name'
password = 'secret'
mail_password = 'mail_secret'
train = []
start_time = time.time()

# Jira Server Connection
options = {'server': 'http://your.domain.com'}
# Authentication
try:
    jira = JIRA(options, basic_auth=(f'{user_name}', f'{password}'))

except BaseException as Be:

    print(Be)

props = jira.application_properties()

# JQL for all closed issues
# All closed issues of the last month

all_closed_issues = jira.search_issues(
    ‘resolution in (Resolved, Cancelled, Repeated ,”Not Repeatable”) and assignee is not EMPTY order by createdDate asc’, maxResults=False)
)
i = 0
for i in range(0, len(all_closed_issues)):
    train.append((str(all_closed_issues[i].key.split('-')[0]) + ' ' + str(
        all_closed_issues[i].fields.summary), all_closed_issues[i].fields.assignee.name))
    
cl = NaiveBayesClassifier(train)
# Mail definition
def sendemail(from_addr,
              to_addr_list,
              cc_addr_list,
              subject, body,
              login, password,
              smtpserver='smtp-mail.outlook.com:587'):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = (str(all_open_issues[i].key) + " can be assigned to:  " + str(cl.classify(issue)))
    msg['From'] = from_addr
    msg['To'] = ", ".join(to_addr_list)
    html = f""" """
    part2 = MIMEText(html, 'html')
    msg.attach(part2)
    part = MIMEBase('application', "octet-stream")
    msg.attach(part)
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, password)
    server.sendmail(from_addr, to_addr_list, msg.as_string())
    server.quit()

while True:
    all_open_issues = jira.search_issues(
        'assignee = EMPTY AND (category = IG-Ankara OR category = YY-Ankara)', maxResults=False
    )
    if len(all_open_issues) > 0:
        for i in range(0, len(all_open_issues)):
            issue = str(all_open_issues[i].key.split('-')[0]) + \
                ' ' + str(all_open_issues[i].fields.summary)
            assignee_ = cl.classify(issue)
            print(all_open_issues[i].key,
                  ' can be assigned to : ', assignee_)
            jira.assign_issue(all_open_issues[i].key, assignee_)
            ts = d.datetime.now().strftime('%Y/%m/%d')
            cur.execute("INSERT INTO auto_assigned (i_key ,assignee,timestamp_) VALUES ("+f"'{all_open_issues[i].key}'"+ ","+ f"'{assignee_}'"+","+f"'{ts}'"+")")
            conn.commit()
            comment = jira.add_comment(all_open_issues[i], 'This issue is automatically assigned.', visibility={'type': 'role', 'value': 'Administrators'})  # for admins only,
            total_time_lapse = time.time() - start_time            
            cur_date = d.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"--- Total Time:  {total_time_lapse} seconds ---")
            try:
                sendemail(from_addr='huseyin.capan@netcad.com.tr',
                          to_addr_list=['capanh@gmail.com'],
                          cc_addr_list='',
                          subject=str(all_open_issues[i].key) +
                          " is assigned to:  " + str(cl.classify(issue)),
                          body=f"Total time lapsed :  {total_time_lapse} seconds ---",
                          login="huseyin.capan@netcad.com.tr",
                          password=f'{mail_password}')
            except BaseException as Be:
                print(Be)
    else:
        cur_date = d.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(
            "There aren't any issues to be assigned. It will be tried again in a minute. ( " + cur_date + " )")
        time.sleep(60)
