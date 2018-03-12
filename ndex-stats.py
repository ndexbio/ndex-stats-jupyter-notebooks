import psycopg2
import sys
# import re
# import numpy as np
import pandas as pd
import pandas.io.sql as sqlio
# from scipy import stats, integrate
from os.path import isfile, expanduser
import json
import argparse
# import datetime
import matplotlib

parser = argparse.ArgumentParser(description='run stats queries vs. the NDEx log database')
parser.add_argument('--config',
                    dest='config_file',
                    action='store',
                    default=expanduser("~/ndexstats_config.json"))

parser.add_argument('--dir',
                    dest='stats_dir',
                    action='store',
                    default=expanduser("~/stats/"))

arg = parser.parse_args()

config = None
if isfile(arg.config_file):
    file = open(arg.config_file, "r")
    config = json.load(file)
    file.close()
else:
    raise Exception("Missing or invalid config file " + arg.config_file)

username = config.get("username")
password = config.get("password")
port = config.get("port")
host = config.get("host")
database = config.get("database")

if not (username and password and port and host and database):
    raise Exception("Parameters missing in config file " + arg.config_file)

#--------------------------------------
#  Queries
#--------------------------------------

get_network_by_day = "select date_trunc('day', start_time) as d, count(*) from request_record_raw  " + \
      "where function_name = 'getCompleteNetworkAsCX' " + \
      "and start_time > '2018-01-12' " + \
      "and start_time < '2018-02-12' " + \
      "group by d " + \
      "order by d asc;"

# print("-----")
#print(get_network_by_day)

get_anon_search_by_day = "select date_trunc('day', start_time) as d, count(*) from request_record_raw " + \
      "where function_name = 'searchNetwork' " + \
      "and start_time > '2018-01-12' " + \
      "and start_time < '2018-02-12' " + \
      "group by d " + \
      "order by d asc;"

#--------------------------------------
#  Run
#--------------------------------------


try:
    #conn = psycopg2.connect(conn_string)
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=username,
        password=password)
    #print("-----")
    #print(conn)
    network_by_day_df = sqlio.read_sql_query(get_network_by_day, conn)
    network_by_day_df.rename(index=str, inplace=True, columns={"count": "networks accessed", "d": "date"})

    anon_by_day_df = sqlio.read_sql_query(get_anon_search_by_day, conn)
    anon_by_day_df.rename(index=str, inplace=True, columns={"count": "anon searches", "d": "date"})
    #print("-----")
    #
    conn.close()

    merged = pd.merge(network_by_day_df, anon_by_day_df, on='date')
    merged['date'] = merged['date'].apply(lambda x: x.strftime('%m/%d'))

    merged.plot(
        x='date',
        #y='count',
        kind='bar',
        grid=True,
        #colormap='autumn',
        alpha=0.5,
        figsize=(16,8),
        title='Network Access and Anonymous Search (not including browse)',
        width=.8,
        linewidth=1.2
        #stacked=True
    )

    matplotlib.pyplot.xlabel('date')
    matplotlib.pyplot.ylabel('count')
    fig_path = arg.stats_dir + "access_and_searches.jpg"
    matplotlib.pyplot.savefig(fig_path)

except:
    e = sys.exc_info()[0]
    # print("Error: %s %tb" % e)
    print("Error: %s" % e)
    sys.exit()


