import psycopg2
import sys
import pandas as pd
import pandas.io.sql as sqlio
import matplotlib.pyplot as plt
import datetime

my_username = "ndexstats"
my_password = "dashboard2018"
my_port = "5432"
my_host = "stats.ndexbio.org"
my_db_name = 'ndexstats'

conn_string = "host={} port={}  dbname={}  user={}  password={}".format(
        my_host,
        my_port,
        my_db_name,
        my_username,
        my_password)

print("will connect with\n\t->{}".format(conn_string))
get_network_by_day = "select date_trunc('day', start_time) as d, count(*) from request_record_raw  " + \
      "where function_name = 'getCompleteNetworkAsCX' " + \
      "and start_time > '2018-01-12' " + \
      "and start_time < '2018-02-12' " + \
      "group by d " + \
      "order by d asc;"

print("-----")
print(get_network_by_day)

get_anon_search_by_day = "select date_trunc('day', start_time) as d, count(*) from request_record_raw " + \
      "where function_name = 'searchNetwork' " + \
      "and start_time > '2018-01-12' " + \
      "and start_time < '2018-02-12' " + \
      "group by d " + \
      "order by d asc;"

print("-----")
print(get_anon_search_by_day)

get_network = {}
anon_search = {}
# conn.cursor will return a cursor object for performing queries
# get a connection, if a connect cannot be made an exception will be raised here
try:
    #conn = psycopg2.connect(conn_string)
    conn = psycopg2.connect(
        host=my_host,
        port=my_port,
        dbname=my_db_name,
        user=my_username,
        password=my_password)
    print("-----")
    print(conn)
    network_by_day_df = sqlio.read_sql_query(get_network_by_day, conn)
    network_by_day_df.rename(index=str, inplace=True, columns={"count": "networks accessed", "d": "date"})
    anon_by_day_df = sqlio.read_sql_query(get_anon_search_by_day, conn)

    conn.close()

    merged = pd.merge(network_by_day_df, anon_by_day_df, on='d')

    #print(network_by_day_df)
    merged['d'] = merged['d'].apply(lambda x: x.strftime('%m/%d'))

    #merged.applymap(lambda x: )
    print(merged)
except:
    e = sys.exc_info()[0]
    print("Error: %s" % e)
    sys.exit()

