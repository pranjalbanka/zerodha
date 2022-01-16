from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os
from os import listdir

import pyotp

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


totp1 = pyotp.TOTP("Insert Secret Key if TOTP is enabled, account 1")
totp2 = pyotp.TOTP("Insert Secret Key if TOTP is enabled, account 2")


accounts = {"username1":"password1","username2":"password2", "username3":"password3", "username4":"password4"}
pins = [str(totp1.now()),str(totp2.now()),'pin3','pin4']

#Get filenames of all files in a directory
def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

#Chrome options to download files to particular directory
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {
  "download.default_directory": r"/Users/pranjal/Desktop/zerodha/data",
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})


driver = webdriver.Chrome(chrome_options=options)

#counter
i=0

for id_user, password_user in accounts.items():
	# driver.get('chrome://settings/clearBrowserData')
	# driver.find_element_by_xpath('//settings-ui').send_keys(Keys.ENTER)

	driver.get("https://kite.zerodha.com/")

	userid = driver.find_element_by_id("userid")
	userid.send_keys(id_user)

	password = driver.find_element_by_id("password")
	password.send_keys(password_user)


	password.submit() 


	#locate and input the PIN/TOTP
	try: 
	    pin = WebDriverWait(driver, 10).until(EC.visibility_of_any_elements_located((By.XPATH, "//*[@id='totp'] | //*[@id='pin']")))
	except:
		print("could not locate pin/totp")
		driver.quit()

	pin[0].send_keys(pins[i])
	pin[0].submit() 


	#locate and click holdings
	try:
	    holdings = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[2]/div[1]/a[3]")))
	    holdings.click()
	except:
		print("could not locate holdings")
		driver.quit()

    #locate and click download button
	try:
	    download = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[2]/div[2]/div/div/section/div/div/div/span[3]/span")))
	    download.click()
	except:
	    print("could not locate downloads button")
	    driver.quit()

	#locate and click profile button
	try:
	    profile = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[2]/div[2]/div/a")))
	    profile.click()
	except:
		print("could not locate profile")
		driver.quit()

	#locate and click logout button
	try:
	    logout = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[1]/div/div[2]/div[2]/div/div/ul/li[9]/a")))
	    logout.click()
	except:
		print("could not locate logout button")
		driver.quit()

	#locate and click change user button
	try:
	    changeuser = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='container']/div[1]/a")))
	    changeuser.click()
	except:
		print("could not locate change user option")
		driver.quit()

	i=i+1

#quit chrome
driver.quit()


filenames = find_csv_filenames('/Users/pranjal/Desktop/zerodha/data')

#empty dataframe to merge all accounts data
merged = pd.DataFrame()

#append account data to merged
for file in filenames:
	csv = pd.read_csv('data/'+file)
	merged = pd.concat([merged,csv])

#drop some coulumns from the merged dataframe
merged = merged.drop(['Avg. cost','Net chg.','Day chg.'], axis = 1)

#combine same stocks in differet accounts together
aggregation_functions = {'Qty.': 'sum', 'LTP': 'first', 'Cur. val': 'sum', 'P&L': 'sum'}
df_new = merged.groupby(merged['Instrument']).aggregate(aggregation_functions)

#add some columns like average buy price, weightage
df_new['avg'] = ((df_new['Cur. val']-df_new['P&L'])/df_new['Qty.']).round(2)
df_new['weightage'] = (100*df_new['Cur. val']/df_new['Cur. val'].sum()).round(2)

#sort dataframe
df_new = df_new.sort_values(by='P&L', ascending=False)

#deleted downloaded data
for file in filenames:
	os.remove('data/'+file)

#plot with plotly
fig = make_subplots(rows=1, cols=2,specs=[[{"type": "bar"}, {"type": "pie"}]])
fig.add_trace(go.Bar(x=df_new.index, y=df_new['P&L']),row=1, col=1)
fig.add_trace(go.Pie(values=df_new['Cur. val'], labels=df_new.index),row=1, col=2)
fig.update_layout(title_text="PnL: "+str(df_new['P&L'].sum())+" pct change:"+str(round(100*df_new['P&L'].sum()/(df_new['Cur. val'].sum()-df_new['P&L'].sum()),2)))
fig.show()


#save dataframe to csv file
df_new.to_csv('portfolio.csv')
