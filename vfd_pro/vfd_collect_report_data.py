import mysql.connector
from statistics import mean 
from decimal import Decimal
import html

def special_divide(numerator, denominator):
    if denominator!=0:
        result=numerator/denominator
    else:
        result=Decimal(0.0)
    return result

def get_metrics_from_database(
    config,
    client_id):
    # A handy query:
    # SELECT client_id, COUNT(DISTINCT `offset`) FROM client_transaction WHERE `offset` <=0 GROUP BY client_id;
    # nominal_name_exclude="account.name NOT IN ('Corp Tax', 'Corporation Tax', 'Dividend', 'Taxes', 'Interest', 'Depreciation', 'Depn', 'Amortisation', 'Amortization', 'Corporate Tax', 'Business Tax')"
    # nominal_name_exclude="account.name NOT LIKE '%Corp Tax%' AND account.name NOT LIKE '%Corporation Tax%' AND account.name NOT LIKE '%Dividend%' AND account.name NOT LIKE '%Taxes%' AND account.name NOT LIKE '%Interest%' AND account.name NOT LIKE '%Depreciation%' AND account.name NOT LIKE '%Depn%' AND account.name NOT LIKE '%Amortisation%' AND account.name NOT LIKE '%Amortization%' AND account.name NOT LIKE '%Corporate Tax%' AND account.name NOT LIKE '%Business Tax%'"
    #nominal_name_exclude="((account.name NOT LIKE '%Corp Tax%' AND account.name NOT LIKE '%Corporation Tax%' AND account.name NOT LIKE '%Dividend%' AND account.name NOT LIKE '%Taxes%' AND account.name NOT LIKE '%Interest%' AND account.name NOT LIKE '%Int.%' AND account.name NOT LIKE '%Depreciation%' AND account.name NOT LIKE '%Depn%' AND account.name NOT LIKE '%Amortisation%' AND account.name NOT LIKE '%Amortization%' AND account.name NOT LIKE '%Corporate Tax%' AND account.name NOT LIKE '%Business Tax%') OR (category NOT IN ('Cost of Sales', 'Overheads')))"
    nominal_name_exclude=html.unescape(" \
        ( \
         (account.name NOT LIKE '%Corp Tax%' AND \
          account.name NOT LIKE '%Corporation Tax%' AND \
          account.name NOT LIKE '%Dividend%' AND \
          account.name NOT LIKE '%Taxes%' AND \
          account.name NOT LIKE '%Interest%' AND \
          account.name NOT LIKE '%Int.%' AND \
          account.name NOT LIKE '%Depreciation%' AND \
          account.name NOT LIKE '%Depn%' AND \
          account.name NOT LIKE '%Amortisation%' AND \
          account.name NOT LIKE '%Amortization%' AND \
          account.name NOT LIKE '%Corporate Tax%' AND \
          account.name NOT LIKE '%Business Tax%' AND \
          account.name NOT LIKE '%Amortissement%' AND \
          account.name NOT LIKE '%Imp&ocirc;t sur les Soci&eacute;t&eacute;s%' AND \
          account.name NOT LIKE '%D&eacute;pr&eacute;ciation%' AND \
          account.name NOT LIKE '%Dividende%' AND \
          account.name NOT LIKE '%Int&eacute;r&ecirc;t%' AND \
          account.name NOT LIKE '%Taxation%') OR \
         (category NOT IN ('Cost of Sales', 'Overheads') \
         ) \
        )")
    nominal_type_exclude="account.type NOT LIKE '%OTHERINCOME%'"

    metric_definitions={
        'chart_assets_month-0': "category IN ('Fixed assets', 'Current assets') AND `offset`<=0",
        'chart_assets_month-12': "category IN ('Fixed assets', 'Current assets') AND `offset`<=-12",
        'chart_liabilities_month-0': "category IN ('Current liabilities', 'Long term liabilities') AND `offset`<=0",
        'chart_liabilities_month-12': "category IN ('Current liabilities', 'Long term liabilities') AND `offset`<=-12",

        'chart_current_assets_month-0': "category='Current assets' AND `offset`<=0",
        'chart_current_assets_month-12': "category='Current assets' AND `offset`<=-12",
        'chart_current_liabilities_month-0': "category='Current liabilities' AND `offset`<=0",
        'chart_current_liabilities_month-12': "category='Current liabilities' AND `offset`<=-12",

        # Rolling 12 month Overheads for the previous 13 months.
        'chart_overheads_month-0': "category='Overheads' AND `offset`>=-11 AND `offset`<=0",
        'chart_overheads_month-1': "category='Overheads' AND `offset`>=-12 AND `offset`<=-1",
        'chart_overheads_month-2': "category='Overheads' AND `offset`>=-13 AND `offset`<=-2",
        'chart_overheads_month-3': "category='Overheads' AND `offset`>=-14 AND `offset`<=-3",
        'chart_overheads_month-4': "category='Overheads' AND `offset`>=-15 AND `offset`<=-4",
        'chart_overheads_month-5': "category='Overheads' AND `offset`>=-16 AND `offset`<=-5",
        'chart_overheads_month-6': "category='Overheads' AND `offset`>=-17 AND `offset`<=-6",
        'chart_overheads_month-7': "category='Overheads' AND `offset`>=-18 AND `offset`<=-7",
        'chart_overheads_month-8': "category='Overheads' AND `offset`>=-19 AND `offset`<=-8",
        'chart_overheads_month-9': "category='Overheads' AND `offset`>=-20 AND `offset`<=-9",
        'chart_overheads_month-10': "category='Overheads' AND `offset`>=-21 AND `offset`<=-10",
        'chart_overheads_month-11': "category='Overheads' AND `offset`>=-22 AND `offset`<=-11",
        'chart_overheads_month-12': "category='Overheads' AND `offset`>=-23 AND `offset`<=-12",

        # Rolling 12 month Cost of Sales for the previous 13 months.
        'chart_cost_of_sales_month-0': "category='Cost of Sales' AND `offset`>=-11 AND `offset`<=0",
        'chart_cost_of_sales_month-1': "category='Cost of Sales' AND `offset`>=-12 AND `offset`<=-1",
        'chart_cost_of_sales_month-2': "category='Cost of Sales' AND `offset`>=-13 AND `offset`<=-2",
        'chart_cost_of_sales_month-3': "category='Cost of Sales' AND `offset`>=-14 AND `offset`<=-3",
        'chart_cost_of_sales_month-4': "category='Cost of Sales' AND `offset`>=-15 AND `offset`<=-4",
        'chart_cost_of_sales_month-5': "category='Cost of Sales' AND `offset`>=-16 AND `offset`<=-5",
        'chart_cost_of_sales_month-6': "category='Cost of Sales' AND `offset`>=-17 AND `offset`<=-6",
        'chart_cost_of_sales_month-7': "category='Cost of Sales' AND `offset`>=-18 AND `offset`<=-7",
        'chart_cost_of_sales_month-8': "category='Cost of Sales' AND `offset`>=-19 AND `offset`<=-8",
        'chart_cost_of_sales_month-9': "category='Cost of Sales' AND `offset`>=-20 AND `offset`<=-9",
        'chart_cost_of_sales_month-10': "category='Cost of Sales' AND `offset`>=-21 AND `offset`<=-10",
        'chart_cost_of_sales_month-11': "category='Cost of Sales' AND `offset`>=-22 AND `offset`<=-11",
        'chart_cost_of_sales_month-12': "category='Cost of Sales' AND `offset`>=-23 AND `offset`<=-12",

        'COS_Month_TY': "category='Cost of Sales' AND `offset`=0",
        'COS_Month_LY': "category='Cost of Sales' AND `offset`=-12",
        'COS_Last_3_Months_TY': "category='Cost of Sales' AND `offset`>=-2 AND `offset`<=0",
        'COS_Last_3_Months_LY': "category='Cost of Sales' AND `offset`>=-14 AND `offset`<=-12",
        'COS_Last_6_Months_TY': "category='Cost of Sales' AND `offset`>=-5 AND `offset`<=0",
        'COS_Last_6_Months_LY': "category='Cost of Sales' AND `offset`>=-17 AND `offset`<=-12", 
        'COS_Last_9_Months_TY': "category='Cost of Sales' AND `offset`>=-8 AND `offset`<=0",
        'COS_Last_9_Months_LY': "category='Cost of Sales' AND `offset`>=-20 AND `offset`<=-12",
        'COS_Last_12_Months_TY': "category='Cost of Sales' AND `offset`>=-11 AND `offset`<=0",
        'COS_Last_12_Months_LY': "category='Cost of Sales' AND `offset`>=-23 AND `offset`<=-12",

        'Overheads_Month_TY': "category='Overheads' AND `offset`=0",
        'Overheads_Month_LY': "category='Overheads' AND `offset`=-12",
        'Overheads_Last_3_Months_TY': "category='Overheads' AND `offset`>=-2 AND `offset`<=0",
        'Overheads_Last_3_Months_LY': "category='Overheads' AND `offset`>=-14 AND `offset`<=-12",
        'Overheads_Last_6_Months_TY': "category='Overheads' AND `offset`>=-5 AND `offset`<=0",
        'Overheads_Last_6_Months_LY': "category='Overheads' AND `offset`>=-17 AND `offset`<=-12",
        'Overheads_Last_9_Months_TY': "category='Overheads' AND `offset`>=-8 AND `offset`<=0",
        'Overheads_Last_9_Months_LY': "category='Overheads' AND `offset`>=-20 AND `offset`<=-12",
        'Overheads_Last_12_Months_TY': "category='Overheads' AND `offset`>=-11 AND `offset`<=0",
        'Overheads_Last_12_Months_LY': "category='Overheads' AND `offset`>=-23 AND `offset`<=-12",

        'Net_Worth_Current_Month_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=0",
        'Net_Worth_Current_Month_-1_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-1",
        'Net_Worth_Current_Month_-2_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-2",
        'Net_Worth_Current_Month_-3_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-3",
        'Net_Worth_Current_Month_-4_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-4",
        'Net_Worth_Current_Month_-5_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-5",
        'Net_Worth_Current_Month_-6_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-6",
        'Net_Worth_Current_Month_-7_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-7",
        'Net_Worth_Current_Month_-8_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-8",
        'Net_Worth_Current_Month_-9_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-9",
        'Net_Worth_Current_Month_-10_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-10",
        'Net_Worth_Current_Month_-11_TY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-11",

        'Net_Worth_Current_Month_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-12",
        'Net_Worth_Current_Month_-1_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-13",
        'Net_Worth_Current_Month_-2_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-14",
        'Net_Worth_Current_Month_-3_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-15",
        'Net_Worth_Current_Month_-4_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-16",
        'Net_Worth_Current_Month_-5_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-17",
        'Net_Worth_Current_Month_-6_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-18",
        'Net_Worth_Current_Month_-7_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-19",
        'Net_Worth_Current_Month_-8_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-20",
        'Net_Worth_Current_Month_-9_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-21",
        'Net_Worth_Current_Month_-10_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-22",
        'Net_Worth_Current_Month_-11_LY': "category IN ('Fixed assets', 'Current assets', 'Current liabilities', 'Long term liabilities') AND `offset`<=-23",

        # Rolling 12 month Profit for the previous 13 months.
        'chart_profit_month-0': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-1 AND `offset`<=0",
        'chart_profit_month-1': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-2 AND `offset`<=-1",
        'chart_profit_month-2': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-3 AND `offset`<=-2",
        'chart_profit_month-3': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-4 AND `offset`<=-3",
        'chart_profit_month-4': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-5 AND `offset`<=-4",
        'chart_profit_month-5': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-6 AND `offset`<=-5",
        'chart_profit_month-6': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-7 AND `offset`<=-6",
        'chart_profit_month-7': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-8 AND `offset`<=-7",
        'chart_profit_month-8': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-9 AND `offset`<=-8",
        'chart_profit_month-9': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-10 AND `offset`<=-9",
        'chart_profit_month-10': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-11 AND `offset`<=-10",
        'chart_profit_month-11': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-12 AND `offset`<=-11",
        'chart_profit_month-12': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-13 AND `offset`<=-12",
        'chart_profit_month-13': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-14 AND `offset`<=-13",
        'chart_profit_month-14': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-15 AND `offset`<=-14",
        'chart_profit_month-15': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-16 AND `offset`<=-15",
        'chart_profit_month-16': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-17 AND `offset`<=-16",
        'chart_profit_month-17': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-18 AND `offset`<=-17",
        'chart_profit_month-18': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-19 AND `offset`<=-18",
        'chart_profit_month-19': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-20 AND `offset`<=-19",
        'chart_profit_month-20': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-21 AND `offset`<=-20",
        'chart_profit_month-21': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-22 AND `offset`<=-21",
        'chart_profit_month-22': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-23 AND `offset`<=-22",
        'chart_profit_month-23': "category IN ('Sales', 'Cost of Sales', 'Overheads') AND `offset`>-24 AND `offset`<=-23",
    }

    metric_values={}
    
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    for metric_name, where_clause in metric_definitions.items():
        #sql=f'SELECT SUM(net_amount) AS metric_value FROM `client_transaction` WHERE client_id={client_id} AND {where_clause}'
        sql=f" \
            SELECT \
                SUM(transaction.net_amount) AS metric_value \
            FROM \
                client_transaction transaction \
                LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                {where_clause} AND \
                {nominal_name_exclude} AND \
                {nominal_type_exclude}"
        # //Faezeh
        print("RUNNING QUERY FOR:", metric_name)
        print("CLIENT ID =", client_id)
        print("SQL =", sql)

        cursor.execute(sql)
        row=cursor.fetchone()
        if 'COS' in metric_name or \
           'Overheads' in metric_name or \
           'Net_Worth' in metric_name or \
           'chart_overheads' in metric_name or \
           'chart_cost_of_sales_month' in metric_name or \
           'chart_assets' in metric_name or \
           'chart_liabilities' in metric_name:
            if row['metric_value'] is not None:
                metric_values[metric_name]=-1*row['metric_value']
            else:
                metric_values[metric_name]=Decimal(0.0)
        else:
            if row['metric_value'] is not None:
                metric_values[metric_name]=row['metric_value']
            else:
                metric_values[metric_name]=Decimal(0.0)

    #sql=f" \
    #    SELECT \
    #        MIN(transaction.offset) AS metric_value \
    #    FROM \
    #        client_transaction transaction \
    #        LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
    #    WHERE \
    #        transaction.client_id={client_id} AND \
    #        transaction.category='Sales' AND \
    #        {nominal_name_exclude} AND \
    #        {nominal_type_exclude}"
    #cursor.execute(sql)
    #row=cursor.fetchone()
    #metric_values['chart_minimum_rolling_offset_sales']=row['metric_value']

    # Income (not just sales).

    metric_definitions={
        # Rolling 12 month Revenue for the previous 13 months. Grr!
        'chart_revenue_month-0': "category='Sales' AND `offset`>=-11 AND `offset`<=0",
        'chart_revenue_month-1': "category='Sales' AND `offset`>=-12 AND `offset`<=-1",
        'chart_revenue_month-2': "category='Sales' AND `offset`>=-13 AND `offset`<=-2",
        'chart_revenue_month-3': "category='Sales' AND `offset`>=-14 AND `offset`<=-3",
        'chart_revenue_month-4': "category='Sales' AND `offset`>=-15 AND `offset`<=-4",
        'chart_revenue_month-5': "category='Sales' AND `offset`>=-16 AND `offset`<=-5",
        'chart_revenue_month-6': "category='Sales' AND `offset`>=-17 AND `offset`<=-6",
        'chart_revenue_month-7': "category='Sales' AND `offset`>=-18 AND `offset`<=-7",
        'chart_revenue_month-8': "category='Sales' AND `offset`>=-19 AND `offset`<=-8",
        'chart_revenue_month-9': "category='Sales' AND `offset`>=-20 AND `offset`<=-9",
        'chart_revenue_month-10': "category='Sales' AND `offset`>=-21 AND `offset`<=-10",
        'chart_revenue_month-11': "category='Sales' AND `offset`>=-22 AND `offset`<=-11",
        'chart_revenue_month-12': "category='Sales' AND `offset`>=-23 AND `offset`<=-12",

        # Moved this lot to here. Grr!
        'Sales_Month_TY': "category='Sales' AND `offset`=0",
        'Sales_Month_LY': "category='Sales' AND `offset`=-12",
        'Sales_Last_3_Months_TY': "category='Sales' AND `offset`>=-2 AND `offset`<=0",
        'Sales_Last_3_Months_LY': "category='Sales' AND `offset`>=-14 AND `offset`<=-12",
        'Sales_Last_6_Months_TY': "category='Sales' AND `offset`>=-5 AND `offset`<=0",
        'Sales_Last_6_Months_LY': "category='Sales' AND `offset`>=-17 AND `offset`<=-12",
        'Sales_Last_9_Months_TY': "category='Sales' AND `offset`>=-8 AND `offset`<=0",
        'Sales_Last_9_Months_LY': "category='Sales' AND `offset`>=-20 AND `offset`<=-12",
        'Sales_Last_12_Months_TY': "category='Sales' AND `offset`>=-11 AND `offset`<=0",
        'Sales_Last_12_Months_LY': "category='Sales' AND `offset`>=-23 AND `offset`<=-12",

        # Rolling 12 month Income for the previous 13 months (to ultimately calculate Net Profit).
        'chart_income_month-0': "category='Sales' AND `offset`>=-11 AND `offset`<=0",
        'chart_income_month-1': "category='Sales' AND `offset`>=-12 AND `offset`<=-1",
        'chart_income_month-2': "category='Sales' AND `offset`>=-13 AND `offset`<=-2",
        'chart_income_month-3': "category='Sales' AND `offset`>=-14 AND `offset`<=-3",
        'chart_income_month-4': "category='Sales' AND `offset`>=-15 AND `offset`<=-4",
        'chart_income_month-5': "category='Sales' AND `offset`>=-16 AND `offset`<=-5",
        'chart_income_month-6': "category='Sales' AND `offset`>=-17 AND `offset`<=-6",
        'chart_income_month-7': "category='Sales' AND `offset`>=-18 AND `offset`<=-7",
        'chart_income_month-8': "category='Sales' AND `offset`>=-19 AND `offset`<=-8",
        'chart_income_month-9': "category='Sales' AND `offset`>=-20 AND `offset`<=-9",
        'chart_income_month-10': "category='Sales' AND `offset`>=-21 AND `offset`<=-10",
        'chart_income_month-11': "category='Sales' AND `offset`>=-22 AND `offset`<=-11",
        'chart_income_month-12': "category='Sales' AND `offset`>=-23 AND `offset`<=-12",

        # Use this in preference to Revenue for EBITDA section used to be Revenue section()
        'Income_Month_TY': "category='Sales' AND `offset`=0",
        'Income_Month_LY': "category='Sales' AND `offset`=-12",
        'Income_Last_3_Months_TY': "category='Sales' AND `offset`>=-2 AND `offset`<=0",
        'Income_Last_3_Months_LY': "category='Sales' AND `offset`>=-14 AND `offset`<=-12",
        'Income_Last_6_Months_TY': "category='Sales' AND `offset`>=-5 AND `offset`<=0",
        'Income_Last_6_Months_LY': "category='Sales' AND `offset`>=-17 AND `offset`<=-12",
        'Income_Last_9_Months_TY': "category='Sales' AND `offset`>=-8 AND `offset`<=0",
        'Income_Last_9_Months_LY': "category='Sales' AND `offset`>=-20 AND `offset`<=-12",
        'Income_Last_12_Months_TY': "category='Sales' AND `offset`>=-11 AND `offset`<=0",
        'Income_Last_12_Months_LY': "category='Sales' AND `offset`>=-23 AND `offset`<=-12",
    }

    for metric_name, where_clause in metric_definitions.items():
        sql=f" \
            SELECT \
                SUM(transaction.net_amount) AS metric_value \
            FROM \
                client_transaction transaction \
                LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                {where_clause} AND \
                {nominal_name_exclude}"
        # //Faezeh
        print("📌 CHECKING vfd_client FOR ID:", client_id)
        print("SQL =", sql)
 
        cursor.execute(sql)
        row=cursor.fetchone()

        if row['metric_value'] is not None:
            metric_values[metric_name]=row['metric_value']
        else:
            metric_values[metric_name]=Decimal(0.0)


    # Rolling offset sales
    sql=f" \
        SELECT \
            MIN(transaction.offset) AS metric_value \
        FROM \
            client_transaction transaction \
            LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
        WHERE \
            transaction.client_id={client_id} AND \
            transaction.category='Sales'"
            # AND \
            #{nominal_name_exclude} AND \
            #{nominal_type_exclude}"
    cursor.execute(sql)
    row=cursor.fetchone()
    metric_values['chart_minimum_rolling_offset_sales']=row['metric_value']





    # Revenue Drivers.
    # ptype NOT IN ('MJ', 'CN', 'OVERPAYMENTS')
    ptype_num_trans_exclude=" \
        transaction.source NOT IN ('manual-journal', 'credit-note', 'overpayment') AND \
        transaction.api_source_type_name NOT IN ('MJ', 'CN', 'OVERPAYMENTS')"
    sql=f" \
        SELECT \
            COUNT(*) AS metric_value \
        FROM \
            client_transaction transaction \
            LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
        WHERE \
            transaction.client_id={client_id} AND \
            transaction.category='Sales' AND \
            transaction.offset<=0 AND \
            transaction.offset>=-11 AND \
            {ptype_num_trans_exclude} AND \
            {nominal_name_exclude} AND \
            {nominal_type_exclude}"
    cursor.execute(sql)
    row=cursor.fetchone()
    metric_values['chart_total_sales_transactions-0']=row['metric_value']

    sql=f" \
        SELECT \
            COUNT(DISTINCT(invoice.number)) AS metric_value \
        FROM \
            client_transaction AS transaction \
            LEFT JOIN vfd_client_account AS account ON (account.id=transaction.account_id) \
            LEFT JOIN vfd_client_journal AS journal ON (journal.id=transaction.journal_id) \
            LEFT JOIN vfd_client_invoice AS invoice ON (invoice.id=journal.source_id) \
        WHERE \
            transaction.client_id={client_id} AND \
            transaction.category='Sales' AND \
            transaction.offset<=0 AND \
            transaction.offset>=-11 AND \
            {ptype_num_trans_exclude} AND \
            (transaction.source='invoice' OR (transaction.source='data' AND transaction.api_source_type_name='INV')) AND \
            {nominal_name_exclude} AND \
            {nominal_type_exclude}"
    cursor.execute(sql)
    row=cursor.fetchone()
    if row['metric_value']>0:
        metric_values['chart_total_sales_invoices-0']=row['metric_value']
    else:
        sql=f" \
            SELECT \
                COUNT(DISTINCT(journal.reference)) AS metric_value \
            FROM \
                client_transaction AS transaction \
                LEFT JOIN vfd_client_account AS account ON (account.id=transaction.account_id) \
                LEFT JOIN vfd_client_journal AS journal ON (journal.id=transaction.journal_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                transaction.category='Sales' AND \
                transaction.offset<=0 AND \
                transaction.offset>=-11 AND \
                {ptype_num_trans_exclude} AND \
                (transaction.source='invoice' OR (transaction.source='data' AND transaction.api_source_type_name='INV')) AND \
                {nominal_name_exclude} AND \
                {nominal_type_exclude}"
        cursor.execute(sql)
        row=cursor.fetchone()
        metric_values['chart_total_sales_invoices-0']=row['metric_value']

    sql=f" \
        SELECT \
            COUNT(*) AS metric_value \
        FROM \
            client_transaction transaction \
            LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
        WHERE \
            transaction.client_id={client_id} AND \
            transaction.category='Sales' AND \
            transaction.offset<=-12 AND \
            transaction.offset>=-23 AND \
            {ptype_num_trans_exclude} AND \
            {nominal_name_exclude} AND \
            {nominal_type_exclude}"
    cursor.execute(sql)
    row=cursor.fetchone()
    metric_values['chart_total_sales_transactions-12']=row['metric_value']

    sql=f" \
        SELECT \
            COUNT(DISTINCT(invoice.number)) AS metric_value \
        FROM \
            client_transaction AS transaction \
            LEFT JOIN vfd_client_account AS account ON (account.id=transaction.account_id) \
            LEFT JOIN vfd_client_journal AS journal ON (journal.id=transaction.journal_id) \
            LEFT JOIN vfd_client_invoice AS invoice ON (invoice.id=journal.source_id) \
        WHERE \
            transaction.client_id={client_id} AND \
            transaction.category='Sales' AND \
            transaction.offset<=-12 AND \
            transaction.offset>=-23 AND \
            {ptype_num_trans_exclude} AND \
            (transaction.source='invoice' OR (transaction.source='data' AND transaction.api_source_type_name='INV')) AND \
            {nominal_name_exclude} AND \
            {nominal_type_exclude}"
    cursor.execute(sql)
    row=cursor.fetchone()
    if row['metric_value']>0:
        metric_values['chart_total_sales_invoices-12']=row['metric_value']
    else:
        sql=f" \
            SELECT \
                COUNT(DISTINCT(journal.reference)) AS metric_value \
            FROM \
                client_transaction AS transaction \
                LEFT JOIN vfd_client_account AS account ON (account.id=transaction.account_id) \
                LEFT JOIN vfd_client_journal AS journal ON (journal.id=transaction.journal_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                transaction.category='Sales' AND \
                transaction.offset<=-12 AND \
                transaction.offset>=-23 AND \
                {ptype_num_trans_exclude} AND \
                (transaction.source='invoice' OR (transaction.source='data' AND transaction.api_source_type_name='INV')) AND \
                {nominal_name_exclude} AND \
                {nominal_type_exclude}"
        cursor.execute(sql)
        row=cursor.fetchone()
        metric_values['chart_total_sales_invoices-12']=row['metric_value']


    # ptype NOT IN ('MJ', 'Unknown', 'Ukn')
    #ptype_num_client_exclude="source NOT IN ('bank-transaction', 'credit-note', 'invoice', 'manual-journal', 'overpayment', 'payment', 'data', 'starting-balance')"
    #    transaction.source NOT IN ('bank-transaction', 'credit-note', 'invoice', 'manual-journal', 'overpayment', 'payment', 'starting-balance') AND \
    #    transaction.source NOT IN ('bank-transaction', 'credit-note', 'manual-journal', 'overpayment', 'payment', 'starting-balance') AND \
    #    transaction.source!='Other Income' AND \
    #    transaction.api_source_type_name NOT IN ('MJ', 'Unknown', 'Ukn')"
    ptype_num_client_exclude=" \
        account.type NOT LIKE '%OTHERINCOME%' AND \
        transaction.source NOT IN ('manual-journal', 'credit-note', 'overpayment') AND \
        transaction.api_source_type_name NOT IN ('MJ', 'CN', 'OVERPAYMENTS')"

    segmentation_definitions={
        # Customer Segmentation.
        'Customer_Segmentation_TY_Existing': "contact.customer_ty!=0 AND contact.customer_ly!=0 AND transaction.offset>=-11 AND transaction.offset<=0",
        'Customer_Segmentation_TY_New': "contact.customer_ty!=0 AND contact.customer_ly=0 AND transaction.offset>=-11 AND transaction.offset<=0",
        'Customer_Segmentation_LY_vs_TY_Retained': "contact.customer_ly!=0 AND contact.customer_ty!=0 AND transaction.offset>=-23 AND transaction.offset<=12",
        'Customer_Segmentation_LY_vs_TY_Lost': "contact.customer_ly!=0 AND contact.customer_ty=0 AND transaction.offset>=-23 AND transaction.offset<=12",
        'Customer_Segmentation_LY_vs_PY_Existing': "contact.customer_ly!=0 AND contact.customer_py!=0 AND transaction.offset>=-23 AND transaction.offset<=12",
        'Customer_Segmentation_LY_vs_PY_New': "contact.customer_ly!=0 AND contact.customer_py=0 AND transaction.offset>=-23 AND transaction.offset<=12",
        'Customer_Segmentation_PY_vs_LY_Retained': "contact.customer_py!=0 AND contact.customer_ly!=0 AND transaction.offset>=-35 AND transaction.offset<=24",
        'Customer_Segmentation_PY_vs_LY_Lost': "contact.customer_py!=0 AND contact.customer_ly=0 AND transaction.offset>=-35 AND transaction.offset<=24",
        'Customer_Count_TY': "contact.customer_ty!=0 AND transaction.offset>=-11 AND transaction.offset<=0",
        'Customer_Count_LY': "contact.customer_ly!=0 AND transaction.offset>=-23 AND transaction.offset<=12",
        'Customer_Count_PY': "contact.customer_py!=0 AND transaction.offset>=-35 AND transaction.offset<=24",

        # Supplier Segmentation.
        'Supplier_Segmentation_TY_Existing': "contact.supplier_ty!=0 AND contact.supplier_ly!=0",
        'Supplier_Segmentation_TY_New': "contact.supplier_ty!=0 AND contact.supplier_ly=0",
        'Supplier_Segmentation_LY_vs_TY_Retained': "contact.supplier_ly!=0 AND contact.supplier_ty!=0",
        'Supplier_Segmentation_LY_vs_TY_Lost': "contact.supplier_ly!=0 AND contact.supplier_ty=0",
        'Supplier_Segmentation_LY_vs_PY_Existing': "contact.supplier_ly!=0 AND contact.supplier_py!=0",
        'Supplier_Segmentation_LY_vs_PY_New': "contact.supplier_ly!=0 AND contact.supplier_py=0",
        'Supplier_Segmentation_PY_vs_LY_Retained': "contact.supplier_py!=0 AND contact.supplier_ly!=0",
        'Supplier_Segmentation_PY_vs_LY_Lost': "contact.supplier_py!=0 AND contact.supplier_ly=0",
    }

    #for metric_name, where_clause in segmentation_definitions.items():
    #    sql=f" \
    #        SELECT DISTINCT \
    #            contact.name AS contact_name \
    #        FROM \
    #            client_transaction transaction \
    #            LEFT JOIN vfd_client_contact contact ON (contact.id = transaction.contact_id) \
    #        WHERE \
    #            transaction.client_id={client_id} AND \
    #            {where_clause} \
    #    "
    #    cursor.execute(sql)
    #    results = cursor.fetchall()
    #    metric_values[metric_name]=cursor.rowcount
    for metric_name, where_clause in segmentation_definitions.items():
        sql=f" \
            SELECT \
                COUNT(DISTINCT contact.name) AS metric_value \
            FROM \
                client_transaction transaction \
                LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
                LEFT JOIN vfd_client_contact contact ON (contact.id=transaction.contact_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                transaction.category='Sales' AND \
                {ptype_num_client_exclude} AND \
                {where_clause} \
        "
        # {nominal_name_exclude} AND \
        # {nominal_type_exclude} AND \
        cursor.execute(sql)
        row=cursor.fetchone()
        metric_values[metric_name]=row['metric_value']

    account_types={
        'accounts_receivable': 'Accounts Receivable',
        'accounts_payable': 'Accounts Payable',
    }
    account_names={
        'accounts_receivable': [
            '%A/R%',
            '%Accounts Receivable%',
            '%Debtor Control%',
            '%Debtors%',
            '%Sales ledger%',
            '%Recouvrables%',
            html.unescape('%Contr&ocirc;le du d&eacute;biteur%'),
            '%Grand livre des ventes%',
        ],
        'accounts_payable': [
            #'%Payables Identification%',
            '%A/P%',
            '%Accounts Payable%',
            #'%AMEX%',
            #'%C.I.S.%',
            #'%CIS%',
            #'%Corporation Tax Liability%',
            #'%Corporation tax payable%',
            '%Creditors%',
            '%Creditors Control%',
            #'%Creditors Control Account%',
            #'%Earnings Orders Payable%',
            #'%Inland Revenue - PAYEE%',
            #'%Mastercard%',
            #'%National Insurance%',
            #'%Nest%',
            #'%Net Wages%',
            #'%NIC Payable%',
            #'%P.A.Y.E.%',
            #'%PAYE & NIC%',
            #'%PAYE and National Insurance%',
            #'%PAYE and NI%',
            #'%PAYE Control Account%',
            #'%PAYE Payable%',
            #'%PAYE/NI%',
            #'%PAYEE NIC & TAX%',
            #'%Payroll Liabilities%',
            #'%Pension control%',
            #'%Pension Liability%',
            #'%Pension Payable%',
            #'%Pensions Payable%',
            #'%Pensions unpaid%',
            '%Purchase ledger',
            #'%Purchase ledger control%',
            #'%Unpaid Expense Claims%',
            #'%VISA%',
            #'%Wages Control Account%',
            #'%Wages Payable - Payroll%',
            '%Dettes Exigibles%',
            html.unescape('%Contr&ocirc;le des cr&eacute;anciers%'),
            '%Registre des achats%',
        ]
    }

    for offset in ['-0', '-12']:
        for pr in ['accounts_receivable', 'accounts_payable']:
            account_name_clause=''
            for account_name in account_names[pr]:
                account_name_clause+=f" OR account.name LIKE '{account_name}'"
            sql=f" \
                SELECT \
                    SUM(transaction.net_amount) AS metric_value \
                FROM \
                    client_transaction transaction \
                    LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
                WHERE \
                    transaction.client_id={client_id} AND \
                    transaction.offset<={offset} AND \
                    transaction.category IN ('Current assets', 'Current liabilities') AND \
                    account.name NOT LIKE '%Other%' AND ( \
                        account.type='{account_types[pr]}' \
                        {account_name_clause} \
                    )"
            cursor.execute(sql)
            row=cursor.fetchone()
            if row['metric_value'] is not None:
                metric_values[f'chart_{pr}{offset}']=row['metric_value']
            else:
                metric_values[f'chart_{pr}{offset}']=Decimal(0.0)

    for offset in range(0, 24):
        sql=f" \
            SELECT \
                SUM(transaction.net_amount) AS metric_value \
            FROM \
                client_transaction transaction \
                LEFT JOIN vfd_client_account account ON (account.id=transaction.account_id) \
            WHERE \
                transaction.client_id={client_id} AND \
                transaction.offset<={-1*offset} AND \
                transaction.category IN ('Current assets', 'Current liabilities') AND ( \
                    account.type LIKE '%Bank%' OR \
                    account.type LIKE '%Cash%' OR \
                    account.name LIKE '%Bank%' OR \
                    account.name LIKE '%Cash%' OR \
                    account.name LIKE '%Current Account%' OR \
                    account.name LIKE '%Deposit Account%' OR \
                    account.name LIKE '%Money Market Account%' \
                ) "
        cursor.execute(sql)
        row=cursor.fetchone()
        if row['metric_value'] is not None:
            metric_values[f'chart_cash_balance_month-{offset}']=-1*row['metric_value']
        else:
            metric_values[f'chart_cash_balance_month-{offset}']=Decimal(0.0)

    sql=f" \
        SELECT \
            accounting_date \
        FROM \
            vfd_client \
        WHERE \
            id={client_id} \
        "
    cursor.execute(sql)
    row=cursor.fetchone()
    metric_values['accounting_date']=row['accounting_date']

    connection.close()
    return metric_values

def get_derived_metrics(metric_values):
    # Gross Margin.
    metric_values['GM_Month_TY']=metric_values['Sales_Month_TY']-metric_values['COS_Month_TY']
    metric_values['GM_Month_LY']=metric_values['Sales_Month_LY']-metric_values['COS_Month_LY']
    metric_values['GM_Last_3_Months_TY']=metric_values['Sales_Last_3_Months_TY']-metric_values['COS_Last_3_Months_TY']
    metric_values['GM_Last_3_Months_LY']=metric_values['Sales_Last_3_Months_LY']-metric_values['COS_Last_3_Months_LY']
    metric_values['GM_Last_6_Months_TY']=metric_values['Sales_Last_6_Months_TY']-metric_values['COS_Last_6_Months_TY']
    metric_values['GM_Last_6_Months_LY']=metric_values['Sales_Last_6_Months_LY']-metric_values['COS_Last_6_Months_LY']
    metric_values['GM_Last_9_Months_TY']=metric_values['Sales_Last_9_Months_TY']-metric_values['COS_Last_9_Months_TY']
    metric_values['GM_Last_9_Months_LY']=metric_values['Sales_Last_9_Months_LY']-metric_values['COS_Last_9_Months_LY']
    metric_values['GM_Last_12_Months_TY']=metric_values['Sales_Last_12_Months_TY']-metric_values['COS_Last_12_Months_TY']
    metric_values['GM_Last_12_Months_LY']=metric_values['Sales_Last_12_Months_LY']-metric_values['COS_Last_12_Months_LY']

    metric_values['GM%_Month_TY']=special_divide(metric_values['GM_Month_TY'], metric_values['Sales_Month_TY'])*100
    metric_values['GM%_Month_LY']=special_divide(metric_values['GM_Month_LY'], metric_values['Sales_Month_LY'])*100
    metric_values['GM%_Last_3_Months_TY']=special_divide(metric_values['GM_Last_3_Months_TY'], metric_values['Sales_Last_3_Months_TY'])*100
    metric_values['GM%_Last_3_Months_LY']=special_divide(metric_values['GM_Last_3_Months_LY'], metric_values['Sales_Last_3_Months_LY'])*100
    metric_values['GM%_Last_6_Months_TY']=special_divide(metric_values['GM_Last_6_Months_TY'], metric_values['Sales_Last_6_Months_TY'])*100
    metric_values['GM%_Last_6_Months_LY']=special_divide(metric_values['GM_Last_6_Months_LY'], metric_values['Sales_Last_6_Months_LY'])*100
    metric_values['GM%_Last_9_Months_TY']=special_divide(metric_values['GM_Last_9_Months_TY'], metric_values['Sales_Last_9_Months_TY'])*100
    metric_values['GM%_Last_9_Months_LY']=special_divide(metric_values['GM_Last_9_Months_LY'], metric_values['Sales_Last_9_Months_LY'])*100
    metric_values['GM%_Last_12_Months_TY']=special_divide(metric_values['GM_Last_12_Months_TY'], metric_values['Sales_Last_12_Months_TY'])*100
    metric_values['GM%_Last_12_Months_LY']=special_divide(metric_values['GM_Last_12_Months_LY'], metric_values['Sales_Last_12_Months_LY'])*100

    # Gross Margin for EBITDA.
    metric_values['GM_EBITDA_Month_TY']=metric_values['Income_Month_TY']-metric_values['COS_Month_TY']
    metric_values['GM_EBITDA_Month_LY']=metric_values['Income_Month_LY']-metric_values['COS_Month_LY']
    metric_values['GM_EBITDA_Last_3_Months_TY']=metric_values['Income_Last_3_Months_TY']-metric_values['COS_Last_3_Months_TY']
    metric_values['GM_EBITDA_Last_3_Months_LY']=metric_values['Income_Last_3_Months_LY']-metric_values['COS_Last_3_Months_LY']
    metric_values['GM_EBITDA_Last_6_Months_TY']=metric_values['Income_Last_6_Months_TY']-metric_values['COS_Last_6_Months_TY']
    metric_values['GM_EBITDA_Last_6_Months_LY']=metric_values['Income_Last_6_Months_LY']-metric_values['COS_Last_6_Months_LY']
    metric_values['GM_EBITDA_Last_9_Months_TY']=metric_values['Income_Last_9_Months_TY']-metric_values['COS_Last_9_Months_TY']
    metric_values['GM_EBITDA_Last_9_Months_LY']=metric_values['Income_Last_9_Months_LY']-metric_values['COS_Last_9_Months_LY']
    metric_values['GM_EBITDA_Last_12_Months_TY']=metric_values['Income_Last_12_Months_TY']-metric_values['COS_Last_12_Months_TY']
    metric_values['GM_EBITDA_Last_12_Months_LY']=metric_values['Income_Last_12_Months_LY']-metric_values['COS_Last_12_Months_LY']

    metric_values['GM_EBITDA%_Month_TY']=special_divide(metric_values['GM_EBITDA_Month_TY'], metric_values['Income_Month_TY'])*100
    metric_values['GM_EBITDA%_Month_LY']=special_divide(metric_values['GM_EBITDA_Month_LY'], metric_values['Income_Month_LY'])*100
    metric_values['GM_EBITDA%_Last_3_Months_TY']=special_divide(metric_values['GM_EBITDA_Last_3_Months_TY'], metric_values['Income_Last_3_Months_TY'])*100
    metric_values['GM_EBITDA%_Last_3_Months_LY']=special_divide(metric_values['GM_EBITDA_Last_3_Months_LY'], metric_values['Income_Last_3_Months_LY'])*100
    metric_values['GM_EBITDA%_Last_6_Months_TY']=special_divide(metric_values['GM_EBITDA_Last_6_Months_TY'], metric_values['Income_Last_6_Months_TY'])*100
    metric_values['GM_EBITDA%_Last_6_Months_LY']=special_divide(metric_values['GM_EBITDA_Last_6_Months_LY'], metric_values['Income_Last_6_Months_LY'])*100
    metric_values['GM_EBITDA%_Last_9_Months_TY']=special_divide(metric_values['GM_EBITDA_Last_9_Months_TY'], metric_values['Income_Last_9_Months_TY'])*100
    metric_values['GM_EBITDA%_Last_9_Months_LY']=special_divide(metric_values['GM_EBITDA_Last_9_Months_LY'], metric_values['Income_Last_9_Months_LY'])*100
    metric_values['GM_EBITDA%_Last_12_Months_TY']=special_divide(metric_values['GM_EBITDA_Last_12_Months_TY'], metric_values['Income_Last_12_Months_TY'])*100
    metric_values['GM_EBITDA%_Last_12_Months_LY']=special_divide(metric_values['GM_EBITDA_Last_12_Months_LY'], metric_values['Income_Last_12_Months_LY'])*100





    # Overheads.
    metric_values['Overheads%_Month_TY']=special_divide(metric_values['Overheads_Month_TY'], metric_values['Sales_Month_TY'])*100
    metric_values['Overheads%_Month_LY']=special_divide(metric_values['Overheads_Month_LY'], metric_values['Sales_Month_LY'])*100

    metric_values['Overheads%_Last_3_Months_TY']=special_divide(metric_values['Overheads_Last_3_Months_TY'], metric_values['Sales_Last_3_Months_TY'])*100
    metric_values['Overheads%_Last_3_Months_LY']=special_divide(metric_values['Overheads_Last_3_Months_LY'], metric_values['Sales_Last_3_Months_LY'])*100

    metric_values['Overheads%_Last_6_Months_TY']=special_divide(metric_values['Overheads_Last_6_Months_TY'], metric_values['Sales_Last_6_Months_TY'])*100
    metric_values['Overheads%_Last_6_Months_LY']=special_divide(metric_values['Overheads_Last_6_Months_LY'], metric_values['Sales_Last_6_Months_LY'])*100

    metric_values['Overheads%_Last_9_Months_TY']=special_divide(metric_values['Overheads_Last_9_Months_TY'], metric_values['Sales_Last_9_Months_TY'])*100
    metric_values['Overheads%_Last_9_Months_LY']=special_divide(metric_values['Overheads_Last_9_Months_LY'], metric_values['Sales_Last_9_Months_LY'])*100

    metric_values['Overheads%_Last_12_Months_TY']=special_divide(metric_values['Overheads_Last_12_Months_TY'], metric_values['Sales_Last_12_Months_TY'])*100
    metric_values['Overheads%_Last_12_Months_LY']=special_divide(metric_values['Overheads_Last_12_Months_LY'], metric_values['Sales_Last_12_Months_LY'])*100

    # Net Profit.
    metric_values['Net_Profit_Month_TY']=metric_values['GM_Month_TY']-metric_values['Overheads_Month_TY']
    metric_values['Net_Profit_Month_LY']=metric_values['GM_Month_LY']-metric_values['Overheads_Month_LY']
    metric_values['Net_Profit_Last_3_Months_TY']=metric_values['GM_Last_3_Months_TY']-metric_values['Overheads_Last_3_Months_TY']
    metric_values['Net_Profit_Last_3_Months_LY']=metric_values['GM_Last_3_Months_LY']-metric_values['Overheads_Last_3_Months_LY']
    metric_values['Net_Profit_Last_6_Months_TY']=metric_values['GM_Last_6_Months_TY']-metric_values['Overheads_Last_6_Months_TY']
    metric_values['Net_Profit_Last_6_Months_LY']=metric_values['GM_Last_6_Months_LY']-metric_values['Overheads_Last_6_Months_LY']
    metric_values['Net_Profit_Last_9_Months_TY']=metric_values['GM_Last_9_Months_TY']-metric_values['Overheads_Last_9_Months_TY']
    metric_values['Net_Profit_Last_9_Months_LY']=metric_values['GM_Last_9_Months_LY']-metric_values['Overheads_Last_9_Months_LY']
    metric_values['Net_Profit_Last_12_Months_TY']=metric_values['GM_Last_12_Months_TY']-metric_values['Overheads_Last_12_Months_TY']
    metric_values['Net_Profit_Last_12_Months_LY']=metric_values['GM_Last_12_Months_LY']-metric_values['Overheads_Last_12_Months_LY']

    metric_values['Net_Profit%_Month_TY']=special_divide(metric_values['Net_Profit_Month_TY'], metric_values['Sales_Month_TY'])*100
    metric_values['Net_Profit%_Month_LY']=special_divide(metric_values['Net_Profit_Month_LY'], metric_values['Sales_Month_LY'])*100

    metric_values['Net_Profit%_Last_3_Months_TY']=special_divide(metric_values['Net_Profit_Last_3_Months_TY'], metric_values['Sales_Last_3_Months_TY'])*100
    metric_values['Net_Profit%_Last_3_Months_LY']=special_divide(metric_values['Net_Profit_Last_3_Months_LY'], metric_values['Sales_Last_3_Months_LY'])*100

    metric_values['Net_Profit%_Last_6_Months_TY']=special_divide(metric_values['Net_Profit_Last_6_Months_TY'], metric_values['Sales_Last_6_Months_TY'])*100
    metric_values['Net_Profit%_Last_6_Months_LY']=special_divide(metric_values['Net_Profit_Last_6_Months_LY'], metric_values['Sales_Last_6_Months_LY'])*100

    metric_values['Net_Profit%_Last_9_Months_TY']=special_divide(metric_values['Net_Profit_Last_9_Months_TY'], metric_values['Sales_Last_9_Months_TY'])*100
    metric_values['Net_Profit%_Last_9_Months_LY']=special_divide(metric_values['Net_Profit_Last_9_Months_LY'], metric_values['Sales_Last_9_Months_LY'])*100

    metric_values['Net_Profit%_Last_12_Months_TY']=special_divide(metric_values['Net_Profit_Last_12_Months_TY'], metric_values['Sales_Last_12_Months_TY'])*100
    metric_values['Net_Profit%_Last_12_Months_LY']=special_divide(metric_values['Net_Profit_Last_12_Months_LY'], metric_values['Sales_Last_12_Months_LY'])*100

    # EBITDA.
    metric_values['EBITDA_Month_TY']=metric_values['GM_EBITDA_Month_TY']-metric_values['Overheads_Month_TY']
    metric_values['EBITDA_Month_LY']=metric_values['GM_EBITDA_Month_LY']-metric_values['Overheads_Month_LY']
    metric_values['EBITDA_Last_3_Months_TY']=metric_values['GM_EBITDA_Last_3_Months_TY']-metric_values['Overheads_Last_3_Months_TY']
    metric_values['EBITDA_Last_3_Months_LY']=metric_values['GM_EBITDA_Last_3_Months_LY']-metric_values['Overheads_Last_3_Months_LY']
    metric_values['EBITDA_Last_6_Months_TY']=metric_values['GM_EBITDA_Last_6_Months_TY']-metric_values['Overheads_Last_6_Months_TY']
    metric_values['EBITDA_Last_6_Months_LY']=metric_values['GM_EBITDA_Last_6_Months_LY']-metric_values['Overheads_Last_6_Months_LY']
    metric_values['EBITDA_Last_9_Months_TY']=metric_values['GM_EBITDA_Last_9_Months_TY']-metric_values['Overheads_Last_9_Months_TY']
    metric_values['EBITDA_Last_9_Months_LY']=metric_values['GM_EBITDA_Last_9_Months_LY']-metric_values['Overheads_Last_9_Months_LY']
    metric_values['EBITDA_Last_12_Months_TY']=metric_values['GM_EBITDA_Last_12_Months_TY']-metric_values['Overheads_Last_12_Months_TY']
    metric_values['EBITDA_Last_12_Months_LY']=metric_values['GM_EBITDA_Last_12_Months_LY']-metric_values['Overheads_Last_12_Months_LY']

    metric_values['EBITDA%_Month_TY']=special_divide(metric_values['EBITDA_Month_TY'], metric_values['Sales_Month_TY'])*100
    metric_values['EBITDA%_Month_LY']=special_divide(metric_values['EBITDA_Month_LY'], metric_values['Sales_Month_LY'])*100
    metric_values['EBITDA%_Last_3_Months_TY']=special_divide(metric_values['EBITDA_Last_3_Months_TY'], metric_values['Sales_Last_3_Months_TY'])*100
    metric_values['EBITDA%_Last_3_Months_LY']=special_divide(metric_values['EBITDA_Last_3_Months_LY'], metric_values['Sales_Last_3_Months_LY'])*100
    metric_values['EBITDA%_Last_6_Months_TY']=special_divide(metric_values['EBITDA_Last_6_Months_TY'], metric_values['Sales_Last_6_Months_TY'])*100
    metric_values['EBITDA%_Last_6_Months_LY']=special_divide(metric_values['EBITDA_Last_6_Months_LY'], metric_values['Sales_Last_6_Months_LY'])*100
    metric_values['EBITDA%_Last_9_Months_TY']=special_divide(metric_values['EBITDA_Last_9_Months_TY'], metric_values['Sales_Last_9_Months_TY'])*100
    metric_values['EBITDA%_Last_9_Months_LY']=special_divide(metric_values['EBITDA_Last_9_Months_LY'], metric_values['Sales_Last_9_Months_LY'])*100
    metric_values['EBITDA%_Last_12_Months_TY']=special_divide(metric_values['EBITDA_Last_12_Months_TY'], metric_values['Sales_Last_12_Months_TY'])*100
    metric_values['EBITDA%_Last_12_Months_LY']=special_divide(metric_values['EBITDA_Last_12_Months_LY'], metric_values['Sales_Last_12_Months_LY'])*100

    # Net Worth.
    metric_values['Net_Worth_TY_3_Month_Ave']=mean(
        [
            metric_values['Net_Worth_Current_Month_TY'],
            metric_values['Net_Worth_Current_Month_-1_TY'],
            metric_values['Net_Worth_Current_Month_-2_TY'],
        ]
    )
    metric_values['Net_Worth_TY_12_Month_Ave']=mean(
        [
            metric_values['Net_Worth_Current_Month_TY'],
            metric_values['Net_Worth_Current_Month_-1_TY'],
            metric_values['Net_Worth_Current_Month_-2_TY'],
            metric_values['Net_Worth_Current_Month_-3_TY'],
            metric_values['Net_Worth_Current_Month_-4_TY'],
            metric_values['Net_Worth_Current_Month_-5_TY'],
            metric_values['Net_Worth_Current_Month_-6_TY'],
            metric_values['Net_Worth_Current_Month_-7_TY'],
            metric_values['Net_Worth_Current_Month_-8_TY'],
            metric_values['Net_Worth_Current_Month_-9_TY'],
            metric_values['Net_Worth_Current_Month_-10_TY'],
            metric_values['Net_Worth_Current_Month_-11_TY'],
        ]
    )
    metric_values['Net_Worth_LY_3_Month_Ave']=mean(
        [
            metric_values['Net_Worth_Current_Month_LY'],
            metric_values['Net_Worth_Current_Month_-1_LY'],
            metric_values['Net_Worth_Current_Month_-2_LY'],
        ]
    )
    metric_values['Net_Worth_LY_12_Month_Ave']=mean(
        [
            metric_values['Net_Worth_Current_Month_LY'],
            metric_values['Net_Worth_Current_Month_-1_LY'],
            metric_values['Net_Worth_Current_Month_-2_LY'],
            metric_values['Net_Worth_Current_Month_-3_LY'],
            metric_values['Net_Worth_Current_Month_-4_LY'],
            metric_values['Net_Worth_Current_Month_-5_LY'],
            metric_values['Net_Worth_Current_Month_-6_LY'],
            metric_values['Net_Worth_Current_Month_-7_LY'],
            metric_values['Net_Worth_Current_Month_-8_LY'],
            metric_values['Net_Worth_Current_Month_-9_LY'],
            metric_values['Net_Worth_Current_Month_-10_LY'],
            metric_values['Net_Worth_Current_Month_-11_LY'],
        ]
    )
    metric_values['Profit_Movement_TYL12M']=metric_values['Net_Profit_Last_12_Months_TY']-metric_values['Net_Profit_Last_12_Months_LY']
    metric_values['Sales_Profit_Movement_TYL12M']=(metric_values['Sales_Last_12_Months_TY']-metric_values['Sales_Last_12_Months_LY'])*metric_values['GM%_Last_12_Months_LY']/100
    # metric_values['GM%_Profit_Movement_TYL12M']=(metric_values['GM%_Last_12_Months_TY']-metric_values['GM%_Last_12_Months_LY'])*metric_values['Sales_Last_12_Months_TY']/100
    metric_values['GM%_Profit_Movement_TYL12M']=(metric_values['GM%_Last_12_Months_TY']-metric_values['GM%_Last_12_Months_LY'])/100*metric_values['Sales_Last_12_Months_TY']
    
    metric_values['Overheads_Profit_Movement_TYL12M']=metric_values['Overheads_Last_12_Months_TY']-metric_values['Overheads_Last_12_Months_LY']

    metric_values['Sales_Var_vs_LY_Month_TY']=metric_values['Sales_Month_TY']-metric_values['Sales_Month_LY']
    metric_values['Sales_Var%_vs_LY_Month_TY']=special_divide(metric_values['Sales_Var_vs_LY_Month_TY'], metric_values['Sales_Month_LY'])*100

    metric_values['Sales_Var_vs_LY_Last_3_Months_TY']=metric_values['Sales_Last_3_Months_TY']-metric_values['Sales_Last_3_Months_LY']
    metric_values['Sales_Var%_vs_LY_Last_3_Months_TY']=special_divide(metric_values['Sales_Var_vs_LY_Last_3_Months_TY'], metric_values['Sales_Last_3_Months_LY'])*100

    metric_values['Sales_Var_vs_LY_Last_6_Months_TY']=metric_values['Sales_Last_6_Months_TY']-metric_values['Sales_Last_6_Months_LY']
    metric_values['Sales_Var%_vs_LY_Last_6_Months_TY']=special_divide(metric_values['Sales_Var_vs_LY_Last_6_Months_TY'], metric_values['Sales_Last_6_Months_LY'])*100

    metric_values['Sales_Var_vs_LY_Last_9_Months_TY']=metric_values['Sales_Last_9_Months_TY']-metric_values['Sales_Last_9_Months_LY']
    metric_values['Sales_Var%_vs_LY_Last_9_Months_TY']=special_divide(metric_values['Sales_Var_vs_LY_Last_9_Months_TY'], metric_values['Sales_Last_9_Months_LY'])*100

    metric_values['Sales_Var_vs_LY_Last_12_Months_TY']=metric_values['Sales_Last_12_Months_TY']-metric_values['Sales_Last_12_Months_LY']
    metric_values['Sales_Var%_vs_LY_Last_12_Months_TY']=special_divide(metric_values['Sales_Var_vs_LY_Last_12_Months_TY'], metric_values['Sales_Last_12_Months_LY'])*100

    metric_values['GM_Var_vs_LY_Month_TY']=metric_values['GM_Month_TY']-metric_values['GM_Month_LY']
    metric_values['GM_Var%_vs_LY_Month_TY']=special_divide(metric_values['GM_Var_vs_LY_Month_TY'], metric_values['GM_Month_LY'])*100
    metric_values['GM%_Var_vs_LY_Month_TY']=metric_values['GM%_Month_TY']-metric_values['GM%_Month_LY']

    metric_values['GM_Var_vs_LY_Last_3_Months_TY']=metric_values['GM_Last_3_Months_TY']-metric_values['GM_Last_3_Months_LY']
    metric_values['GM_Var%_vs_LY_Last_3_Months_TY']=special_divide(metric_values['GM_Var_vs_LY_Last_3_Months_TY'], metric_values['GM_Last_3_Months_LY'])*100
    metric_values['GM%_Var_vs_LY_Last_3_Months_TY']=metric_values['GM%_Last_3_Months_TY']-metric_values['GM%_Last_3_Months_LY']

    metric_values['GM_Var_vs_LY_Last_6_Months_TY']=metric_values['GM_Last_6_Months_TY']-metric_values['GM_Last_6_Months_LY']
    metric_values['GM_Var%_vs_LY_ Last_6_Months_TY']=special_divide(metric_values['GM_Var_vs_LY_Last_6_Months_TY'], metric_values['GM_Last_6_Months_LY'])*100
    metric_values['GM%_Var_vs_LY_Last_6_Months_TY']=metric_values['GM%_Last_6_Months_TY']-metric_values['GM%_Last_6_Months_LY']

    metric_values['GM_Var_vs_LY_Last_9_Months_TY']=metric_values['GM_Last_9_Months_TY']-metric_values['GM_Last_9_Months_LY']
    metric_values['GM_Var%_vs_LY_Last_9_Months_TY']=special_divide(metric_values['GM_Var_vs_LY_Last_9_Months_TY'], metric_values['GM_Last_9_Months_LY'])*100
    metric_values['GM%_Var_vs_LY_Last_9_Months_TY']=metric_values['GM%_Last_9_Months_TY']-metric_values['GM%_Last_9_Months_LY']

    metric_values['GM_Var_vs_LY_Last_12_Months_TY']=metric_values['GM_Last_12_Months_TY']-metric_values['GM_Last_12_Months_LY']
    metric_values['GM_Var%_vs_LY_Last_12_Months_TY']=special_divide(metric_values['GM_Var_vs_LY_Last_12_Months_TY'], metric_values['GM_Last_12_Months_LY'])*100
    metric_values['GM%_Var_vs_LY_Last_12_Months_TY']=metric_values['GM%_Last_12_Months_TY']-metric_values['GM%_Last_12_Months_LY']

    metric_values['Overheads_Var_vs_LY_Month_TY']=metric_values['Overheads_Month_TY']-metric_values['Overheads_Month_LY']
    metric_values['Overheads_Var%_vs_LY_Month_TY']=special_divide(metric_values['Overheads_Var_vs_LY_Month_TY'], metric_values['Overheads_Month_LY'])*100
    metric_values['Overheads%_Var_vs_LY_Month_TY']=metric_values['Overheads%_Month_TY']-metric_values['Overheads%_Month_LY']

    metric_values['Overheads_Var_vs_LY_Last_3_Months_TY']=metric_values['Overheads_Last_3_Months_TY']-metric_values['Overheads_Last_3_Months_LY']
    metric_values['Overheads_Var%_vs_LY_Last_3_Months_TY']=special_divide(metric_values['Overheads_Var_vs_LY_Last_3_Months_TY'], metric_values['Overheads_Last_3_Months_LY'])*100
    metric_values['Overheads%_Var_vs_LY_Last_3_Months_TY']=metric_values['Overheads%_Last_3_Months_TY']-metric_values['Overheads%_Last_3_Months_LY']

    metric_values['Overheads_Var_vs_LY_Last_6_Months_TY']=metric_values['Overheads_Last_6_Months_TY']-metric_values['Overheads_Last_6_Months_LY']
    metric_values['Overheads_Var%_vs_LY_Last_6_Months_TY']=special_divide(metric_values['Overheads_Var_vs_LY_Last_6_Months_TY'], metric_values['Overheads_Last_6_Months_LY'])*100
    metric_values['Overheads%_Var_vs_LY_Last_6_Months_TY']=metric_values['Overheads%_Last_6_Months_TY']-metric_values['Overheads%_Last_6_Months_LY']

    metric_values['Overheads_Var_vs_LY_Last_9_Months_TY']=metric_values['Overheads_Last_9_Months_TY']-metric_values['Overheads_Last_9_Months_LY']
    metric_values['Overheads_Var%_vs_LY_Last_9_Months_TY']=special_divide(metric_values['Overheads_Var_vs_LY_Last_9_Months_TY'], metric_values['Overheads_Last_9_Months_LY'])*100
    metric_values['Overheads%_Var_vs_LY_Last_9_Months_TY']=metric_values['Overheads%_Last_9_Months_TY']-metric_values['Overheads_Last_12_Months_LY']

    metric_values['Overheads_Var_vs_LY_Last_12_Months_TY']=metric_values['Overheads_Last_12_Months_TY']-metric_values['Overheads_Last_12_Months_LY']
    metric_values['Overheads_Var%_vs_LY_Last_12_Months_TY']=special_divide(metric_values['Overheads_Var_vs_LY_Last_12_Months_TY'], metric_values['Overheads_Last_12_Months_LY'])*100
    metric_values['Overheads%_Var_vs_LY_Last_12_Months_TY']=metric_values['Overheads%_Last_12_Months_TY']-metric_values['Overheads%_Last_12_Months_LY']



    # Net Profit.
    metric_values['Net_Profit_Var_vs_LY_Month_TY']=metric_values['Net_Profit_Month_TY']-metric_values['Net_Profit_Month_LY']
    metric_values['Net_Profit_Var%_vs_LY_Month_TY']=special_divide(metric_values['Net_Profit_Var_vs_LY_Month_TY'], metric_values['Net_Profit_Month_LY'])*100
    metric_values['Net_Profit%_Var_vs_LY_Month_TY']=metric_values['Net_Profit%_Month_TY']-metric_values['Net_Profit%_Month_LY']

    metric_values['Net_Profit_Var_vs_LY_Last_3_Months_TY']=metric_values['Net_Profit_Last_3_Months_TY']-metric_values['Net_Profit_Last_3_Months_LY']
    metric_values['Net_Profit_Var%_vs_LY_Last_3_Months_TY']=special_divide(metric_values['Net_Profit_Var_vs_LY_Last_3_Months_TY'], metric_values['Net_Profit_Last_3_Months_LY'])*100
    metric_values['Net_Profit%_Var_vs_LY_Last_3_Months_TY']=metric_values['Net_Profit%_Last_3_Months_TY']-metric_values['Net_Profit%_Last_3_Months_LY']

    metric_values['Net_Profit_Var_vs_LY_Last_6_Months_TY']=metric_values['Net_Profit_Last_6_Months_TY']-metric_values['Net_Profit_Last_6_Months_LY']
    metric_values['Net_Profit_Var%_vs_LY_Last_6_Months_TY']=special_divide(metric_values['Net_Profit_Var_vs_LY_Last_6_Months_TY'], metric_values['Net_Profit_Last_6_Months_LY'])*100
    metric_values['Net_Profit%_Var_vs_LY_Last_6_Months_TY']=metric_values['Net_Profit%_Last_6_Months_TY']-metric_values['Net_Profit%_Last_6_Months_LY']

    metric_values['Net_Profit_Var_vs_LY_Last_9_Months_TY']=metric_values['Net_Profit_Last_9_Months_TY']-metric_values['Net_Profit_Last_9_Months_LY']
    metric_values['Net_Profit_Var%_vs_LY_Last_9_Months_TY']=special_divide(metric_values['Net_Profit_Var_vs_LY_Last_9_Months_TY'], metric_values['Net_Profit_Last_9_Months_LY'])*100
    metric_values['Net_Profit%_Var_vs_LY_Last_9_Months_TY']=metric_values['Net_Profit%_Last_9_Months_TY']-metric_values['Net_Profit%_Last_9_Months_LY']

    metric_values['Net_Profit_Var_vs_LY_Last_12_Months_TY']=metric_values['Net_Profit_Last_12_Months_TY']-metric_values['Net_Profit_Last_12_Months_LY']
    metric_values['Net_Profit_Var%_vs_LY_Last_12_Months_TY']=special_divide(metric_values['Net_Profit_Var_vs_LY_Last_12_Months_TY'], metric_values['Net_Profit_Last_12_Months_LY'])*100
    metric_values['Net_Profit%_Var_vs_LY_Last_12_Months_TY']=metric_values['Net_Profit%_Last_12_Months_TY']-metric_values['Net_Profit%_Last_12_Months_LY']

    # EBITDA.
    metric_values['EBITDA_Var_vs_LY_Month_TY']=metric_values['EBITDA_Month_TY']-metric_values['EBITDA_Month_LY']
    metric_values['EBITDA_Var%_vs_LY_Month_TY']=special_divide(metric_values['EBITDA_Var_vs_LY_Month_TY'], metric_values['EBITDA_Month_LY'])*100
    metric_values['EBITDA%_Var_vs_LY_Month_TY']=metric_values['EBITDA%_Month_TY']-metric_values['EBITDA%_Month_LY']

    metric_values['EBITDA_Var_vs_LY_Last_3_Months_TY']=metric_values['EBITDA_Last_3_Months_TY']-metric_values['EBITDA_Last_3_Months_LY']
    metric_values['EBITDA_Var%_vs_LY_Last_3_Months_TY']=special_divide(metric_values['EBITDA_Var_vs_LY_Last_3_Months_TY'], metric_values['EBITDA_Last_3_Months_LY'])*100
    metric_values['EBITDA%_Var_vs_LY_Last_3_Months_TY']=metric_values['EBITDA%_Last_3_Months_TY']-metric_values['EBITDA%_Last_3_Months_LY']

    metric_values['EBITDA_Var_vs_LY_Last_6_Months_TY']=metric_values['EBITDA_Last_6_Months_TY']-metric_values['EBITDA_Last_6_Months_LY']
    metric_values['EBITDA_Var%_vs_LY_Last_6_Months_TY']=special_divide(metric_values['EBITDA_Var_vs_LY_Last_6_Months_TY'], metric_values['EBITDA_Last_6_Months_LY'])*100
    metric_values['EBITDA%_Var_vs_LY_Last_6_Months_TY']=metric_values['EBITDA%_Last_6_Months_TY']-metric_values['EBITDA%_Last_6_Months_LY']

    metric_values['EBITDA_Var_vs_LY_Last_9_Months_TY']=metric_values['EBITDA_Last_9_Months_TY']-metric_values['EBITDA_Last_9_Months_LY']
    metric_values['EBITDA_Var%_vs_LY_Last_9_Months_TY']=special_divide(metric_values['EBITDA_Var_vs_LY_Last_9_Months_TY'], metric_values['EBITDA_Last_9_Months_LY'])*100
    metric_values['EBITDA%_Var_vs_LY_Last_9_Months_TY']=metric_values['EBITDA%_Last_9_Months_TY']-metric_values['EBITDA%_Last_9_Months_LY']

    metric_values['EBITDA_Var_vs_LY_Last_12_Months_TY']=metric_values['EBITDA_Last_12_Months_TY']-metric_values['EBITDA_Last_12_Months_LY']
    metric_values['EBITDA_Var%_vs_LY_Last_12_Months_TY']=special_divide(metric_values['EBITDA_Var_vs_LY_Last_12_Months_TY'], metric_values['EBITDA_Last_12_Months_LY'])*100
    metric_values['EBITDA%_Var_vs_LY_Last_12_Months_TY']=metric_values['EBITDA%_Last_12_Months_TY']-metric_values['EBITDA%_Last_12_Months_LY']








    metric_values['Net_Worth_Var_vs_LY_Month_TY']=metric_values['Net_Worth_Current_Month_TY']-metric_values['Net_Worth_Current_Month_LY']
    metric_values['Net_Worth_Var%_vs_LY_Month_TY']=special_divide(metric_values['Net_Worth_Var_vs_LY_Month_TY'], metric_values['Net_Worth_Current_Month_LY'])*100

    metric_values['Net_Worth_Var_vs_LY_3_Month_Ave_TY']=metric_values['Net_Worth_TY_3_Month_Ave']-metric_values['Net_Worth_LY_3_Month_Ave']
    metric_values['Net_Worth_Var%_vs_LY_3_Month_Ave_TY']=special_divide(metric_values['Net_Worth_Var_vs_LY_3_Month_Ave_TY'], metric_values['Net_Worth_LY_3_Month_Ave'])*100

    metric_values['Net_Worth_Var_vs_LY_12_Month_Ave_TY']=metric_values['Net_Worth_TY_12_Month_Ave']-metric_values['Net_Worth_LY_12_Month_Ave']
    metric_values['Net_Worth_Var%_vs_LY_12_Month_Ave_TY']=special_divide(metric_values['Net_Worth_Var_vs_LY_12_Month_Ave_TY'], metric_values['Net_Worth_LY_12_Month_Ave'])*100

    # Some derived values to fill in the Revenue section.
    metric_values['chart_revenue_this_month']=metric_values['Sales_Month_TY']
    metric_values['chart_revenue_this_quarter']=metric_values['Sales_Last_3_Months_TY']
    metric_values['chart_revenue_this_year']=metric_values['Sales_Last_12_Months_TY']
    metric_values['chart_revenue_this_month_vs_last_year']=metric_values['Sales_Var_vs_LY_Month_TY']
    metric_values['chart_revenue_this_quarter_vs_last_year']=metric_values['Sales_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_revenue_this_year_vs_last_year']=metric_values['Sales_Var_vs_LY_Last_12_Months_TY']
    metric_values['chart_revenue_this_month_vs_last_year%']=metric_values['Sales_Var%_vs_LY_Month_TY']
    metric_values['chart_revenue_this_quarter_vs_last_year%']=metric_values['Sales_Var%_vs_LY_Last_3_Months_TY']
    metric_values['chart_revenue_this_year_vs_last_year%']=metric_values['Sales_Var%_vs_LY_Last_12_Months_TY']
    metric_values['chart_revenue_3_1_months']=metric_values['Sales_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_revenue_6_4_months']=metric_values['Sales_Var_vs_LY_Last_6_Months_TY']-metric_values['Sales_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_revenue_9_7_months']=metric_values['Sales_Var_vs_LY_Last_9_Months_TY']-metric_values['Sales_Var_vs_LY_Last_6_Months_TY']
    metric_values['chart_revenue_12_10_months']=metric_values['Sales_Var_vs_LY_Last_12_Months_TY']-metric_values['Sales_Var_vs_LY_Last_9_Months_TY']

    # Some derived values to fill in the Gross Margin section.
    metric_values['chart_gross_margin_month-0']=metric_values['chart_revenue_month-0']-metric_values['chart_cost_of_sales_month-0']
    metric_values['chart_gross_margin_month-1']=metric_values['chart_revenue_month-1']-metric_values['chart_cost_of_sales_month-1']
    metric_values['chart_gross_margin_month-2']=metric_values['chart_revenue_month-2']-metric_values['chart_cost_of_sales_month-2']
    metric_values['chart_gross_margin_month-3']=metric_values['chart_revenue_month-3']-metric_values['chart_cost_of_sales_month-3']
    metric_values['chart_gross_margin_month-4']=metric_values['chart_revenue_month-4']-metric_values['chart_cost_of_sales_month-4']
    metric_values['chart_gross_margin_month-5']=metric_values['chart_revenue_month-5']-metric_values['chart_cost_of_sales_month-5']
    metric_values['chart_gross_margin_month-6']=metric_values['chart_revenue_month-6']-metric_values['chart_cost_of_sales_month-6']
    metric_values['chart_gross_margin_month-7']=metric_values['chart_revenue_month-7']-metric_values['chart_cost_of_sales_month-7']
    metric_values['chart_gross_margin_month-8']=metric_values['chart_revenue_month-8']-metric_values['chart_cost_of_sales_month-8']
    metric_values['chart_gross_margin_month-9']=metric_values['chart_revenue_month-9']-metric_values['chart_cost_of_sales_month-9']
    metric_values['chart_gross_margin_month-10']=metric_values['chart_revenue_month-10']-metric_values['chart_cost_of_sales_month-10']
    metric_values['chart_gross_margin_month-11']=metric_values['chart_revenue_month-11']-metric_values['chart_cost_of_sales_month-11']
    metric_values['chart_gross_margin_month-12']=metric_values['chart_revenue_month-12']-metric_values['chart_cost_of_sales_month-12']

    metric_values['chart_gross_margin_pc_month-0']=special_divide(metric_values['chart_revenue_month-0']-metric_values['chart_cost_of_sales_month-0'], metric_values['chart_revenue_month-0'])*100
    metric_values['chart_gross_margin_pc_month-1']=special_divide(metric_values['chart_revenue_month-1']-metric_values['chart_cost_of_sales_month-1'], metric_values['chart_revenue_month-1'])*100
    metric_values['chart_gross_margin_pc_month-2']=special_divide(metric_values['chart_revenue_month-2']-metric_values['chart_cost_of_sales_month-2'], metric_values['chart_revenue_month-2'])*100
    metric_values['chart_gross_margin_pc_month-3']=special_divide(metric_values['chart_revenue_month-3']-metric_values['chart_cost_of_sales_month-3'], metric_values['chart_revenue_month-3'])*100
    metric_values['chart_gross_margin_pc_month-4']=special_divide(metric_values['chart_revenue_month-4']-metric_values['chart_cost_of_sales_month-4'], metric_values['chart_revenue_month-4'])*100
    metric_values['chart_gross_margin_pc_month-5']=special_divide(metric_values['chart_revenue_month-5']-metric_values['chart_cost_of_sales_month-5'], metric_values['chart_revenue_month-5'])*100
    metric_values['chart_gross_margin_pc_month-6']=special_divide(metric_values['chart_revenue_month-6']-metric_values['chart_cost_of_sales_month-6'], metric_values['chart_revenue_month-6'])*100
    metric_values['chart_gross_margin_pc_month-7']=special_divide(metric_values['chart_revenue_month-7']-metric_values['chart_cost_of_sales_month-7'], metric_values['chart_revenue_month-7'])*100
    metric_values['chart_gross_margin_pc_month-8']=special_divide(metric_values['chart_revenue_month-8']-metric_values['chart_cost_of_sales_month-8'], metric_values['chart_revenue_month-8'])*100
    metric_values['chart_gross_margin_pc_month-9']=special_divide(metric_values['chart_revenue_month-9']-metric_values['chart_cost_of_sales_month-9'], metric_values['chart_revenue_month-9'])*100
    metric_values['chart_gross_margin_pc_month-10']=special_divide(metric_values['chart_revenue_month-10']-metric_values['chart_cost_of_sales_month-10'], metric_values['chart_revenue_month-10'])*100
    metric_values['chart_gross_margin_pc_month-11']=special_divide(metric_values['chart_revenue_month-11']-metric_values['chart_cost_of_sales_month-11'], metric_values['chart_revenue_month-11'])*100
    metric_values['chart_gross_margin_pc_month-12']=special_divide(metric_values['chart_revenue_month-12']-metric_values['chart_cost_of_sales_month-12'], metric_values['chart_revenue_month-12'])*100

    #metric_values['chart_gross_margin_month-13']=metric_values['chart_revenue_month-13']-metric_values['chart_cost_of_sales_month-13']
    #metric_values['chart_gross_margin_month-14']=metric_values['chart_revenue_month-14']-metric_values['chart_cost_of_sales_month-14']
    #metric_values['chart_gross_margin_month-15']=metric_values['chart_revenue_month-15']-metric_values['chart_cost_of_sales_month-15']
    #metric_values['chart_gross_margin_month-16']=metric_values['chart_revenue_month-16']-metric_values['chart_cost_of_sales_month-16']
    #metric_values['chart_gross_margin_month-17']=metric_values['chart_revenue_month-17']-metric_values['chart_cost_of_sales_month-17']
    #metric_values['chart_gross_margin_month-18']=metric_values['chart_revenue_month-18']-metric_values['chart_cost_of_sales_month-18']
    #metric_values['chart_gross_margin_month-19']=metric_values['chart_revenue_month-19']-metric_values['chart_cost_of_sales_month-19']
    #metric_values['chart_gross_margin_month-20']=metric_values['chart_revenue_month-20']-metric_values['chart_cost_of_sales_month-20']
    #metric_values['chart_gross_margin_month-21']=metric_values['chart_revenue_month-21']-metric_values['chart_cost_of_sales_month-21']
    #metric_values['chart_gross_margin_month-22']=metric_values['chart_revenue_month-22']-metric_values['chart_cost_of_sales_month-22']
    #metric_values['chart_gross_margin_month-23']=metric_values['chart_revenue_month-23']-metric_values['chart_cost_of_sales_month-23']
    #metric_values['chart_gross_margin_month-24']=metric_values['chart_revenue_month-24']-metric_values['chart_cost_of_sales_month-24']

    metric_values['chart_gross_margin_pc_3_1_months']=metric_values['GM%_Var_vs_LY_Last_3_Months_TY']
    #metric_values['chart_gross_margin_pc_6_4_months']=metric_values['GM%_Var_vs_LY_Last_6_Months_TY']-metric_values['GM%_Var_vs_LY_Last_3_Months_TY']
    #metric_values['chart_gross_margin_pc_9_7_months']=metric_values['GM%_Var_vs_LY_Last_9_Months_TY']-metric_values['GM%_Var_vs_LY_Last_6_Months_TY']
    #metric_values['chart_gross_margin_pc_12_10_months']=metric_values['GM%_Var_vs_LY_Last_12_Months_TY']-metric_values['GM%_Var_vs_LY_Last_9_Months_TY']

    metric_values['Sales_Last_6_4_Months_TY']=metric_values['Sales_Last_6_Months_TY']-metric_values['Sales_Last_3_Months_TY']
    metric_values['Sales_Last_6_4_Months_LY']=metric_values['Sales_Last_6_Months_LY']-metric_values['Sales_Last_3_Months_LY']
    metric_values['COS_Last_6_4_Months_TY']=metric_values['COS_Last_6_Months_TY']-metric_values['COS_Last_3_Months_TY']
    metric_values['COS_Last_6_4_Months_LY']=metric_values['COS_Last_6_Months_LY']-metric_values['COS_Last_3_Months_LY']
    part1=special_divide(metric_values['Sales_Last_6_4_Months_TY']-metric_values['COS_Last_6_4_Months_TY'], metric_values['Sales_Last_6_4_Months_TY'])*100
    part2=special_divide(metric_values['Sales_Last_6_4_Months_LY']-metric_values['COS_Last_6_4_Months_LY'], metric_values['Sales_Last_6_4_Months_LY'])*100
    metric_values['chart_gross_margin_pc_6_4_months']=part1-part2

    metric_values['Sales_Last_9_7_Months_TY']=metric_values['Sales_Last_9_Months_TY']-metric_values['Sales_Last_6_Months_TY']
    metric_values['Sales_Last_9_7_Months_LY']=metric_values['Sales_Last_9_Months_LY']-metric_values['Sales_Last_6_Months_LY']
    metric_values['COS_Last_9_7_Months_TY']=metric_values['COS_Last_9_Months_TY']-metric_values['COS_Last_6_Months_TY']
    metric_values['COS_Last_9_7_Months_LY']=metric_values['COS_Last_9_Months_LY']-metric_values['COS_Last_6_Months_LY']
    #metric_values['chart_gross_margin_pc_9_7_months']= \
    #    (metric_values['Sales_Last_9_7_Months_TY']-metric_values['COS_Last_9_7_Months_TY'])/metric_values['Sales_Last_9_7_Months_TY']*100- \
    #    (metric_values['Sales_Last_9_7_Months_LY']-metric_values['COS_Last_9_7_Months_LY'])/metric_values['Sales_Last_9_7_Months_LY']*100
    part1=special_divide(metric_values['Sales_Last_9_7_Months_TY']-metric_values['COS_Last_9_7_Months_TY'], metric_values['Sales_Last_9_7_Months_TY'])*100
    part2=special_divide(metric_values['Sales_Last_9_7_Months_LY']-metric_values['COS_Last_9_7_Months_LY'], metric_values['Sales_Last_9_7_Months_LY'])*100
    metric_values['chart_gross_margin_pc_9_7_months']=part1-part2

    metric_values['Sales_Last_12_10_Months_TY']=metric_values['Sales_Last_12_Months_TY']-metric_values['Sales_Last_9_Months_TY']
    metric_values['Sales_Last_12_10_Months_LY']=metric_values['Sales_Last_12_Months_LY']-metric_values['Sales_Last_9_Months_LY']
    metric_values['COS_Last_12_10_Months_TY']=metric_values['COS_Last_12_Months_TY']-metric_values['COS_Last_9_Months_TY']
    metric_values['COS_Last_12_10_Months_LY']=metric_values['COS_Last_12_Months_LY']-metric_values['COS_Last_9_Months_LY']
    #metric_values['chart_gross_margin_pc_12_10_months']= \
    #    (metric_values['Sales_Last_12_10_Months_TY']-metric_values['COS_Last_12_10_Months_TY'])/metric_values['Sales_Last_12_10_Months_TY']*100- \
    #    (metric_values['Sales_Last_12_10_Months_LY']-metric_values['COS_Last_12_10_Months_LY'])/metric_values['Sales_Last_12_10_Months_LY']*100
    part1=special_divide(metric_values['Sales_Last_12_10_Months_TY']-metric_values['COS_Last_12_10_Months_TY'], metric_values['Sales_Last_12_10_Months_TY'])*100
    part2=special_divide(metric_values['Sales_Last_12_10_Months_LY']-metric_values['COS_Last_12_10_Months_LY'], metric_values['Sales_Last_12_10_Months_LY'])*100
    metric_values['chart_gross_margin_pc_12_10_months']=part1-part2

    # Some derived values to fill in the Overheads section.
    metric_values['chart_overheads_this_month']=metric_values['Overheads_Month_TY']
    metric_values['chart_overheads_this_quarter']=metric_values['Overheads_Last_3_Months_TY']
    metric_values['chart_overheads_this_year']=metric_values['Overheads_Last_12_Months_TY']
    # Multiply by -1 because overheads going down is a good thing!
    metric_values['chart_overheads_this_month_vs_last_year']=-1*metric_values['Overheads_Var_vs_LY_Month_TY']
    metric_values['chart_overheads_this_quarter_vs_last_year']=-1*metric_values['Overheads_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_overheads_this_year_vs_last_year']=-1*metric_values['Overheads_Var_vs_LY_Last_12_Months_TY']
    metric_values['chart_overheads_this_month_vs_last_year%']=-1*metric_values['Overheads_Var%_vs_LY_Month_TY']
    metric_values['chart_overheads_this_quarter_vs_last_year%']=-1*metric_values['Overheads_Var%_vs_LY_Last_3_Months_TY']
    metric_values['chart_overheads_this_year_vs_last_year%']=-1*metric_values['Overheads_Var%_vs_LY_Last_12_Months_TY']
    metric_values['chart_overheads_3_1_months']=metric_values['Overheads_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_overheads_6_4_months']=metric_values['Overheads_Var_vs_LY_Last_6_Months_TY']-metric_values['Overheads_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_overheads_9_7_months']=metric_values['Overheads_Var_vs_LY_Last_9_Months_TY']-metric_values['Overheads_Var_vs_LY_Last_6_Months_TY']
    metric_values['chart_overheads_12_10_months']=metric_values['Overheads_Var_vs_LY_Last_12_Months_TY']-metric_values['Overheads_Var_vs_LY_Last_9_Months_TY']

    # Some derived values to fill in the Net Profit section.
    metric_values['chart_net_profit_this_month']=metric_values['Net_Profit_Month_TY']
    metric_values['chart_net_profit_this_quarter']=metric_values['Net_Profit_Last_3_Months_TY']
    metric_values['chart_net_profit_this_year']=metric_values['Net_Profit_Last_12_Months_TY']
    metric_values['chart_net_profit_this_month_vs_last_year']=metric_values['Net_Profit_Var_vs_LY_Month_TY']
    metric_values['chart_net_profit_this_quarter_vs_last_year']=metric_values['Net_Profit_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_net_profit_this_year_vs_last_year']=metric_values['Net_Profit_Var_vs_LY_Last_12_Months_TY']
    metric_values['chart_net_profit_this_month_vs_last_year%']=metric_values['Net_Profit_Var%_vs_LY_Month_TY']
    metric_values['chart_net_profit_this_quarter_vs_last_year%']=metric_values['Net_Profit_Var%_vs_LY_Last_3_Months_TY']
    metric_values['chart_net_profit_this_year_vs_last_year%']=metric_values['Net_Profit_Var%_vs_LY_Last_12_Months_TY']
    metric_values['chart_net_profit_3_1_months']=metric_values['Net_Profit_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_net_profit_6_4_months']=metric_values['Net_Profit_Var_vs_LY_Last_6_Months_TY']-metric_values['Net_Profit_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_net_profit_9_7_months']=metric_values['Net_Profit_Var_vs_LY_Last_9_Months_TY']-metric_values['Net_Profit_Var_vs_LY_Last_6_Months_TY']
    metric_values['chart_net_profit_12_10_months']=metric_values['Net_Profit_Var_vs_LY_Last_12_Months_TY']-metric_values['Net_Profit_Var_vs_LY_Last_9_Months_TY']
    metric_values['chart_net_profit_month-0']=metric_values['chart_gross_margin_month-0']-metric_values['chart_overheads_month-0']
    metric_values['chart_net_profit_month-1']=metric_values['chart_gross_margin_month-1']-metric_values['chart_overheads_month-1']
    metric_values['chart_net_profit_month-2']=metric_values['chart_gross_margin_month-2']-metric_values['chart_overheads_month-2']
    metric_values['chart_net_profit_month-3']=metric_values['chart_gross_margin_month-3']-metric_values['chart_overheads_month-3']
    metric_values['chart_net_profit_month-4']=metric_values['chart_gross_margin_month-4']-metric_values['chart_overheads_month-4']
    metric_values['chart_net_profit_month-5']=metric_values['chart_gross_margin_month-5']-metric_values['chart_overheads_month-5']
    metric_values['chart_net_profit_month-6']=metric_values['chart_gross_margin_month-6']-metric_values['chart_overheads_month-6']
    metric_values['chart_net_profit_month-7']=metric_values['chart_gross_margin_month-7']-metric_values['chart_overheads_month-7']
    metric_values['chart_net_profit_month-8']=metric_values['chart_gross_margin_month-8']-metric_values['chart_overheads_month-8']
    metric_values['chart_net_profit_month-9']=metric_values['chart_gross_margin_month-9']-metric_values['chart_overheads_month-9']
    metric_values['chart_net_profit_month-10']=metric_values['chart_gross_margin_month-10']-metric_values['chart_overheads_month-10']
    metric_values['chart_net_profit_month-11']=metric_values['chart_gross_margin_month-11']-metric_values['chart_overheads_month-11']
    metric_values['chart_net_profit_month-12']=metric_values['chart_gross_margin_month-12']-metric_values['chart_overheads_month-12']

    # Some derived values to fill in the EBITDA section.
    metric_values['chart_ebitda_this_month']=metric_values['EBITDA_Month_TY']
    metric_values['chart_ebitda_this_quarter']=metric_values['EBITDA_Last_3_Months_TY']
    metric_values['chart_ebitda_this_year']=metric_values['EBITDA_Last_12_Months_TY']
    metric_values['chart_ebitda_this_month_vs_last_year']=metric_values['EBITDA_Var_vs_LY_Month_TY']
    metric_values['chart_ebitda_this_quarter_vs_last_year']=metric_values['EBITDA_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_ebitda_this_year_vs_last_year']=metric_values['EBITDA_Var_vs_LY_Last_12_Months_TY']
    metric_values['chart_ebitda_this_month_vs_last_year%']=metric_values['EBITDA_Var%_vs_LY_Month_TY']
    metric_values['chart_ebitda_this_quarter_vs_last_year%']=metric_values['EBITDA_Var%_vs_LY_Last_3_Months_TY']
    metric_values['chart_ebitda_this_year_vs_last_year%']=metric_values['EBITDA_Var%_vs_LY_Last_12_Months_TY']
    metric_values['chart_ebitda_3_1_months']=metric_values['EBITDA_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_ebitda_6_4_months']=metric_values['EBITDA_Var_vs_LY_Last_6_Months_TY']-metric_values['EBITDA_Var_vs_LY_Last_3_Months_TY']
    metric_values['chart_ebitda_9_7_months']=metric_values['EBITDA_Var_vs_LY_Last_9_Months_TY']-metric_values['EBITDA_Var_vs_LY_Last_6_Months_TY']
    metric_values['chart_ebitda_12_10_months']=metric_values['EBITDA_Var_vs_LY_Last_12_Months_TY']-metric_values['EBITDA_Var_vs_LY_Last_9_Months_TY']
    metric_values['chart_ebitda_month-0']=metric_values['chart_gross_margin_month-0']-metric_values['chart_overheads_month-0']
    metric_values['chart_ebitda_month-1']=metric_values['chart_gross_margin_month-1']-metric_values['chart_overheads_month-1']
    metric_values['chart_ebitda_month-2']=metric_values['chart_gross_margin_month-2']-metric_values['chart_overheads_month-2']
    metric_values['chart_ebitda_month-3']=metric_values['chart_gross_margin_month-3']-metric_values['chart_overheads_month-3']
    metric_values['chart_ebitda_month-4']=metric_values['chart_gross_margin_month-4']-metric_values['chart_overheads_month-4']
    metric_values['chart_ebitda_month-5']=metric_values['chart_gross_margin_month-5']-metric_values['chart_overheads_month-5']
    metric_values['chart_ebitda_month-6']=metric_values['chart_gross_margin_month-6']-metric_values['chart_overheads_month-6']
    metric_values['chart_ebitda_month-7']=metric_values['chart_gross_margin_month-7']-metric_values['chart_overheads_month-7']
    metric_values['chart_ebitda_month-8']=metric_values['chart_gross_margin_month-8']-metric_values['chart_overheads_month-8']
    metric_values['chart_ebitda_month-9']=metric_values['chart_gross_margin_month-9']-metric_values['chart_overheads_month-9']
    metric_values['chart_ebitda_month-10']=metric_values['chart_gross_margin_month-10']-metric_values['chart_overheads_month-10']
    metric_values['chart_ebitda_month-11']=metric_values['chart_gross_margin_month-11']-metric_values['chart_overheads_month-11']
    metric_values['chart_ebitda_month-12']=metric_values['chart_gross_margin_month-12']-metric_values['chart_overheads_month-12']


    # Some derived values to fill in the Net Worth section.
    metric_values['chart_net_worth_this_month']=metric_values['Net_Worth_Current_Month_TY']
    metric_values['chart_net_worth_this_quarter']=metric_values['Net_Worth_TY_3_Month_Ave']
    metric_values['chart_net_worth_this_year']=metric_values['Net_Worth_TY_12_Month_Ave']
    metric_values['chart_net_worth_this_month_vs_last_year']=metric_values['Net_Worth_Var_vs_LY_Month_TY']
    metric_values['chart_net_worth_this_quarter_vs_last_year']=metric_values['Net_Worth_Var_vs_LY_3_Month_Ave_TY']
    metric_values['chart_net_worth_this_year_vs_last_year']=metric_values['Net_Worth_Var_vs_LY_12_Month_Ave_TY']
    metric_values['chart_net_worth_this_month_vs_last_year%']=metric_values['Net_Worth_Var%_vs_LY_Month_TY']
    metric_values['chart_net_worth_this_quarter_vs_last_year%']=metric_values['Net_Worth_Var%_vs_LY_3_Month_Ave_TY']
    metric_values['chart_net_worth_this_year_vs_last_year%']=metric_values['Net_Worth_Var%_vs_LY_12_Month_Ave_TY']

    metric_values['chart_net_worth_month-0']=metric_values['Net_Worth_Current_Month_TY']
    metric_values['chart_net_worth_month-1']=metric_values['Net_Worth_Current_Month_-1_TY']
    metric_values['chart_net_worth_month-2']=metric_values['Net_Worth_Current_Month_-2_TY']
    metric_values['chart_net_worth_month-3']=metric_values['Net_Worth_Current_Month_-3_TY']
    metric_values['chart_net_worth_month-4']=metric_values['Net_Worth_Current_Month_-4_TY']
    metric_values['chart_net_worth_month-5']=metric_values['Net_Worth_Current_Month_-5_TY']
    metric_values['chart_net_worth_month-6']=metric_values['Net_Worth_Current_Month_-6_TY']
    metric_values['chart_net_worth_month-7']=metric_values['Net_Worth_Current_Month_-7_TY']
    metric_values['chart_net_worth_month-8']=metric_values['Net_Worth_Current_Month_-8_TY']
    metric_values['chart_net_worth_month-9']=metric_values['Net_Worth_Current_Month_-9_TY']
    metric_values['chart_net_worth_month-10']=metric_values['Net_Worth_Current_Month_-10_TY']
    metric_values['chart_net_worth_month-11']=metric_values['Net_Worth_Current_Month_-11_TY']
    metric_values['chart_net_worth_month-12']=metric_values['Net_Worth_Current_Month_LY']

    metric_values['chart_assets']=metric_values['chart_assets_month-0']-metric_values['chart_assets_month-12']
    metric_values['chart_liabilities']=metric_values['chart_liabilities_month-0']-metric_values['chart_liabilities_month-12']

    # Revenue Drivers.
    metric_values['chart_average_value_per_transaction-0']=special_divide(metric_values['chart_revenue_month-0'], metric_values['chart_total_sales_transactions-0'])
    metric_values['chart_average_value_per_transaction-12']=special_divide(metric_values['chart_revenue_month-12'], metric_values['chart_total_sales_transactions-12'])
    metric_values['chart_average_value_per_invoice-0']=special_divide(metric_values['chart_revenue_month-0'], metric_values['chart_total_sales_invoices-0'])
    metric_values['chart_average_value_per_invoice-12']=special_divide(metric_values['chart_revenue_month-12'], metric_values['chart_total_sales_invoices-12'])

    metric_values['chart_impact_on_revenue_transaction_value']=(metric_values['chart_average_value_per_transaction-0']-metric_values['chart_average_value_per_transaction-12'])*metric_values['chart_total_sales_transactions-12']
    metric_values['chart_impact_on_revenue_transaction_number']=metric_values['chart_average_value_per_transaction-0']*(metric_values['chart_total_sales_transactions-0']-metric_values['chart_total_sales_transactions-12'])
    metric_values['chart_impact_on_revenue_invoice_value']=(metric_values['chart_average_value_per_invoice-0']-metric_values['chart_average_value_per_invoice-12'])*metric_values['chart_total_sales_invoices-12']
    metric_values['chart_impact_on_revenue_invoice_number']=metric_values['chart_average_value_per_invoice-0']*(metric_values['chart_total_sales_invoices-0']-metric_values['chart_total_sales_invoices-12'])

    if metric_values['Customer_Segmentation_LY_vs_TY_Retained']>0 and metric_values['Customer_Segmentation_LY_vs_TY_Lost']>0:
        metric_values['chart_retention_rate_LY_vs_TY']=metric_values['Customer_Segmentation_LY_vs_TY_Retained']/ \
            (metric_values['Customer_Segmentation_LY_vs_TY_Retained']+metric_values['Customer_Segmentation_LY_vs_TY_Lost'])*100
    else:
        metric_values['chart_retention_rate_LY_vs_TY']=Decimal(100.0)

    if metric_values['Customer_Segmentation_PY_vs_LY_Retained']>0 and metric_values['Customer_Segmentation_PY_vs_LY_Lost']>0:
        metric_values['chart_retention_rate_PY_vs_LY']=metric_values['Customer_Segmentation_PY_vs_LY_Retained']/ \
            (metric_values['Customer_Segmentation_PY_vs_LY_Retained']+metric_values['Customer_Segmentation_PY_vs_LY_Lost'])*100
    else:
        metric_values['chart_retention_rate_PY_vs_LY']=Decimal(100.0)

    # Customer drivers.
    mean_revenue_per_customer_TY=special_divide(metric_values['Sales_Last_12_Months_TY'], metric_values['Customer_Count_TY'])
    mean_revenue_per_customer_LY=special_divide(metric_values['Sales_Last_12_Months_LY'], metric_values['Customer_Count_LY'])


    metric_values['chart_revenue_customers_acquired']= \
        mean_revenue_per_customer_TY* \
        (metric_values['Customer_Segmentation_TY_New']-metric_values['Customer_Segmentation_LY_vs_PY_New'])

    #metric_values['chart_revenue_customers_retained']= \
    #    mean_revenue_per_customer_TY* \
    #    metric_values['Customer_Count_LY']* \
    #    Decimal(metric_values['chart_retention_rate_LY_vs_TY'])-Decimal(metric_values['chart_retention_rate_PY_vs_LY'])/ \
    #    100
    if metric_values['Customer_Segmentation_TY_New']>0 and metric_values['Customer_Segmentation_TY_Existing']>0:
        metric_values['chart_revenue_customers_retained']= \
            (Decimal(metric_values['chart_retention_rate_LY_vs_TY']/100)-Decimal(metric_values['chart_retention_rate_PY_vs_LY']/100))* \
            (metric_values['Customer_Segmentation_LY_vs_PY_New']+(metric_values['Customer_Segmentation_LY_vs_PY_Existing']))* \
            ((metric_values['chart_total_sales_transactions-0']*metric_values['chart_average_value_per_transaction-0'])/ \
            (metric_values['Customer_Segmentation_TY_New']+metric_values['Customer_Segmentation_TY_Existing']))
    else:
        metric_values['chart_revenue_customers_retained']=Decimal(0.0)

    profit_month_ty=0
    profit_month_ly=0
    # This may need attention (ROB).
    for i in range(0, 24):
        if i>=0 and i<=11 and metric_values['chart_profit_month-'+str(i)]>0:
            profit_month_ty+=1
        if i>=12 and i<=23 and metric_values['chart_profit_month-'+str(i)]>0:
            profit_month_ly+=1
    metric_values['chart_num_profit_months_ty']=profit_month_ty
    metric_values['chart_num_profit_months_ly']=profit_month_ly

    # Multiply by -1 because!
    metric_values['chart_current_ratio_TY']=-1*special_divide(metric_values['chart_current_assets_month-0'], metric_values['chart_current_liabilities_month-0'])
    metric_values['chart_current_ratio_LY']=-1*special_divide(metric_values['chart_current_assets_month-12'], metric_values['chart_current_liabilities_month-12'])

    # Multiply by -1 because!
    metric_values['chart_debtor_days_TY']=-1*special_divide(metric_values['chart_accounts_receivable-0'], metric_values['Sales_Last_12_Months_TY'])*Decimal(365.0)
    metric_values['chart_debtor_days_LY']=-1*special_divide(metric_values['chart_accounts_receivable-12'], metric_values['Sales_Last_12_Months_LY'])*Decimal(365.0)
    metric_values['chart_creditor_days_TY']=-1*special_divide(metric_values['chart_accounts_payable-0'], (metric_values['Overheads_Last_12_Months_TY']+metric_values['COS_Last_12_Months_TY']))*Decimal(365.0)
    metric_values['chart_creditor_days_LY']=-1*special_divide(metric_values['chart_accounts_payable-12'], (metric_values['Overheads_Last_12_Months_LY']+metric_values['COS_Last_12_Months_LY']))*Decimal(365.0)

    #metric_values['chart_receivables']=(Accounts Payable/(Expenditure*365)
    #Expenditure = line_name = Cost of Sales or Overheads

    return metric_values
