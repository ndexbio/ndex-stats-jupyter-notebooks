import psycopg2

from pandas.io.sql import read_sql


def parseParamsAndBuildInClause(listOfArgs):
    retString = "("
    if type(listOfArgs) is str:
        retString =  retString + "'" + listOfArgs + "')"
    elif type(listOfArgs) is list:
        for arg in listOfArgs:
            retString = retString + "'" + arg + "', "

        retString = retString[:-2]
        retString += ")"

    return retString


def generateWhereClause(filter, primarySearchColumn):
    retStatement = [];
    
    primary = filter[primarySearchColumn];
    #print "In filter before deleting = ", filter,
    
    primaryWhere = primarySearchColumn + " in " + parseParamsAndBuildInClause(filter[primarySearchColumn])
    del filter[primarySearchColumn]
    del filter['primary']
    #print "In filter after deleting = ", filter
    
    whereClauses = [];
    for key in filter:
        whereClause = key + " in " + parseParamsAndBuildInClause(filter[key])
        whereClauses.append(whereClause)
        
    #print "in generateWhereClause: \nprimaryWhere=", primaryWhere + "\nwhereClauses=", whereClauses
    
    whereClause = ""
    for clause in whereClauses:
        whereClause = whereClause + clause + " and "

    #print "whereClause before = ", whereClause
    if len(whereClause) > 1:
        whereClause = whereClause[:-4]
        whereClause = " and " + whereClause
    
    
    #print "whereClause after = ", whereClause  
        
    return primaryWhere, whereClause



'''
Parameters for eventsOverTime():
--------------------------------
1) filter:  API(s)
            account (anonymous or authenticated) 
            application type (i.e., firefox, chrome, python client, etc.) 
            user owning
            group owning 
            group member access
            network type 
            network collection (i.e., all networks in Cancer Clearinghouse, etc.)

2) timeFrame:  day (08/19/2016) 
               month (07/2016) 
               year (2016) 
               quarter (Q2 2016)
                
3) breakBy:  hour 
             day 
             week
             month
'''
def eventsOverTime(filter, timeFrame, breakBy):
   
    if ((filter is None) or (timeFrame is None) or (breakBy is None)):
        return None
    
    # check timeFrame arg
    # print "filter =", filter, " timeFrame =", timeFrame, " breakBy =", breakBy
    
    if ('primary' not in filter):
        print "no 'primary' key in filter; keys in filter =", filter.keys()
        return None          
    
    if (len(timeFrame.keys()) > 1):
        print "more than one entry in timeFrame arg: ", timeFrame
        return None
    
    
    timeFrameKey = timeFrame.keys()[0]
    timeFrameValue = timeFrame.get(timeFrameKey)
    
    if (timeFrameKey not in ["day", "month", "year"]):
        print "wrong value for timeFrame arg: ", timeFrameKey, "; valid values are 'day', 'month', 'year'"
        return None 
    try:
        year, month, day = timeFrameValue.split("-")
    except:
        print "wrong format for timeFrame arg: ", timeFrameValue, "; valid format is timeFrame['" + \
        timeFrameKey + "']='YYYY-MM-DD'"
        return None


    if timeFrameKey == 'day':
        transactionInterval = "and transaction_year = '" + year + "' and transaction_month='" + month + \
        "' and transaction_day = '" + day + "'"
        #print "transactionInterval = ", transactionInterval
    elif timeFrameKey == 'month':
        transactionInterval = "and transaction_year = '" + year + "' and transaction_month='" + month + "'"
        #print "transactionInterval = ", transactionInterval
    elif timeFrameKey == 'year':
        transactionInterval = "and transaction_year = '" + year + "'"
    
    
    if (breakBy not in ["hour", "day", "week", "month"]):
        print "wrong value for breakBy arg: ", breakBy
        return None
    
    transactionBreakBy = "transaction_hour"
    if breakBy == 'day':
        transactionBreakBy = "transaction_day"
        
    #elif breakBy == 'week':
    #    transactionBreakBy = 'transaction_day' 
        
    elif breakBy == 'month':
        transactionBreakBy = "transaction_month"                
    
    
    primarySearchColumn = filter['primary'];
    #print 'primarySearchColumn = ', primarySearchColumn
    
    if type(primarySearchColumn) is list:
        if (len(primarySearchColumn) > 1):
            print "filter['primary'] should be a string or list with one element; but it is =", filter['primary']
            return None
        else:
            primarySearchColumn = filter['primary'][0]

    if primarySearchColumn not in filter:
        print "filter['primary']=", filter['primary'], "; '" +  primarySearchColumn + \
            "' not a key in filter; filter=", filter
        return None
    
    #validSearchColumns = ['api', 'account', 'applicationType', 'userOwning', \
    #                     'groupOwning', 'groupMemberAccess', 'networkType', 'networkCollection']
    
    validSearchColumns = ['api', 'account']
    if primarySearchColumn not in validSearchColumns:
        print "filter['primary']=", filter['primary'], " '" + primarySearchColumn + \
        "' is not valid search column; select one from the list: ", \
            validSearchColumns
        return None        
                       
    apiWhereClause = [];
    accountWhereClause = [];
    sqlStatement = {};
    
    
    # Define our connection string
    conn_string = "host='<ip address>' port='<port No>' dbname='<database name>' user='<username>' password='<password>'"

    # get a connection, if a connect cannot be made an exception will be raised here
    try:
        conn = psycopg2.connect(conn_string)
    except:
        e = sys.exc_info()[0]
        print "Error: %s" % e 
        sys.exit()

    # conn.cursor will return a cursor object for performing queries
    cursor = conn.cursor()
   
    API_Stats = {'Hours' : [n for n in range(0, 24)]}
    columnHeaders = [];
    
    primaryWhereClause, whereClause = generateWhereClause(filter, primarySearchColumn)

    query = "select transactionBreakBy, count(transaction_id), primarySearchColumn " + \
            " from ndexstats where " + \
            primaryWhereClause + \
            whereClause + transactionInterval + \
            " group by transactionBreakBy, primarySearchColumn order by transactionBreakBy"
        
    query = query.replace("primarySearchColumn", primarySearchColumn)
    query = query.replace("transactionBreakBy", transactionBreakBy)
    
    #print "query = ", query
            
    df = read_sql(query, conn, coerce_float=True, params=None)
    
    cursor.close()
    conn.close()
    
    df = df.pivot(transactionBreakBy, primarySearchColumn, 'count') 
    
    return df


