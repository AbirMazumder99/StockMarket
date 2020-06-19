import pandas as pd
import xlsxwriter
# import boto3

IEX_API_Key = ''    #Get API key IEX Cloud

tickers = ['MSFT','AAPL','AMZN','GOOG','FB','BRK.B',
        'JNJ','WMT','V','PG']   #10 largest companies in the US in terms of market cap

#IEX Cloud returns JSON Objects in response to HTTP request 
#Use IEX Cloud's batch API call functionality, which allows you to request data on more than one ticker at a time

#3 Placeholders
#TICKERS -> each of our tickers, ENDPOINTS -> each of the IEX Cloud endpoints, RANGE -> 1y 

#TICKERS
#Create an empty string called `ticker_string` that we'll add tickers and commas to
ticker_string = ','.join(tickers)

#Loop through every element of `tickers` and add them and a comma to ticker_string
for ticker in tickers:
    ticker_string += ticker
    ticker_string += ','
#Drop the last comma from `ticker_string`
ticker_string = ticker_string[:-1]

#IEX Cloud ENDPOINTS 
#Only need the price and stats endpoints to create our spreadsheet
endpoints = 'price,stats'
HTTP_request = f'https://cloud.iexapis.com/stable/stock/market/batch?symbols={ticker_string}&types={endpoints}&range=1y&token={IEX_API_Key}'

# ping the API and save its data 
raw_data = pd.read_json(HTTP_request)   #Display a table with tickers as x axis headers and endpoints as y axis headers

# Creates an empty pandas DataFrame with 0 rows and 4 columns
output_data = pd.DataFrame(pd.np.empty((0,4)))

for ticker in raw_data.columns:
	
    #Parse the company's name - not completed yet
    company_name = raw_data[ticker]['stats']['companyName']
    
    #Parse the company's stock price - not completed yet
    stock_price = raw_data[ticker]['price']

    
    #Parse the company's dividend yield - not completed yet
    dividend_yield = raw_data[ticker]['stats']['dividendYield']
    
    new_column = pd.Series([ticker, company_name, stock_price, dividend_yield])
    output_data = output_data.append(new_column, ignore_index = True)

output_data.columns = ['Ticker', 'Company Name', 'Stock Price', 'Dividend Yield']
output_data.set_index('Ticker', inplace=True)   #index of a pandas DataFrame is like a primary key of a SQL Database table
output_data['Dividend Yield'].fillna(0,inplace=True)    #Replace the missing values of the 'Dividend Yield' column with 0

# Export a nicely formatted excel file from pandas dataframe
writer = pd.ExcelWriter('stock_market_data.xlsx', engine='xlsxwriter')
output_data.to_excel(writer, sheet_name='Stock Market Data')


#Style Templates; Resembles CSS syntax
header_template = writer.book.add_format(
        {
            'font_color': '#ffffff',
            'bg_color': '#135485',
            'border': 1
        }
    )

string_template = writer.book.add_format(
        {
            'bg_color': '#DADADA',
            'border': 1
        }
    )

dollar_template = writer.book.add_format(
        {
            'num_format':'$0.00',
            'bg_color': '#DADADA',
            'border': 1
        }
    )

percent_template = writer.book.add_format(
        {
            'num_format':'0.0%',
            'bg_color': '#DADADA',
            'border': 1
        }
    )
#Style the excel file

#Format the header of the spreadsheet
writer.sheets['Stock Market Data'].conditional_format('A1:D1', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   header_template
                                }
                            )

#Format the 'Ticker' and 'Company Name' columns
writer.sheets['Stock Market Data'].conditional_format('A2:B11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   string_template
                                }
                            )

#Format the 'Stock Price' column
writer.sheets['Stock Market Data'].conditional_format('C2:C11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   dollar_template
                                }
                            )

#Format the 'Dividend Yield' column
writer.sheets['Stock Market Data'].conditional_format('D2:D11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   percent_template
                                }
                            )

#Specify all column widths to make a little wider
writer.sheets['Stock Market Data'].set_column('B:B', 32)
writer.sheets['Stock Market Data'].set_column('C:C', 18)
writer.sheets['Stock Market Data'].set_column('D:D', 20)

#Saves the xlsx file to our current working directory
writer.save()

#Instead of running this on our local machine
#We are gonna set up a virtual machine on AWS Elastic Composite Cloud
# Once AWS account is created, create an EC2 instance. This is simply a virtual server for running code on AWS infrastructure
#Once an instance is created, push Python Script onto the EC2 instance
#CLI: scp -i path/to/.pem_file path/to/file   username@host_address.amazonaws.com:/path_to_copy

#Need to import necessary Python packages into EC3.
#CLI: sudo yum install python3-pip/ pip3 install pandas/ pip3 install xlsxwriter

# Now we can run the python script - python3 stock_market_data.py

# The exel file will only be saved to the AWS virtual server
# which is not accessible to anybody else but us

#So we create a public bucket on AWS S3 where we can save the Excel file

# Navigate to Amazon S3/Create Bucket
# We install boto3 to push the document to our S3 bucket
# boto3 - AWS SDK for Python

#pip install boto3

#Python script connects to AWS
s3 = boto3.resource('s3')

#Uploads our file to S3
#Args: File Name on local machine, S3 bucket uploading to, DESIRED name of the file in the bucket, make the file publicly readable
s3.meta.client.upload_file('stock_market_data.xlsx', 'my-S3-bucket', 'stock_market_data.xlsx', ExtraArgs={'ACL':'public-read'})

#Now to schedule Python script to run periodically, we use a Command Line Utility called cron
# We first instruct our EC2 insance's cron daemon to run Fin.py
#So we createa file named Fin.cron
#In the file specify the following: 00 12 * * * python3 Fin.py
#
#Lastly, load Fin.cron on the crontab. Crontab is basically a file that contains batches of cron jobs
#To load Fin.cron, CLI: crontab Fin.cron
#This will now run at 12 pm everyday on our AWS EC2 virtual Machine