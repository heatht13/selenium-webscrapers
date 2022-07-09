from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import dateparser
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import time
import sys
import signal

def preprocess(filePath):
   """takes path to csv file and returns a dataframe optimized for web scraping"""
   print(f"Preprocessing input file at location {filePath}...")
   data =pd.read_csv(filePath)
   dates = list(data['timestamp'])
   containers = list(data['containers'])
   containersAdj = []
   for pos in range(len(dates)):
      parsed = dateparser.parse(dates[pos])
      dates[pos] = datetime.date.strftime(parsed, "%m/%d/%Y")
   for pos in range(len(containers)):
      if ',' in containers[pos]:
         contSplit = containers[pos].split(", ")
         containersAdj.append(contSplit[0])
         for i in range(1, len(contSplit)):
            containersAdj.append(contSplit[i])
            dates.insert( pos+i, dates[pos])
      else:
         containersAdj.append(containers[pos])
   prepared = pd.DataFrame(list(zip(dates, containersAdj)), columns = ['timestamp', 'containers'])

   print(f"Found {len(prepared)} containers in file...")

   return prepared


def scrape(data):
   """takes dataframe and uses data to scrape source locations off http://fc-inbound-transshipment-portal-prod-na.iad.proxy.amazon.com/SearchTransfer"""
   print("Scraping containers from web...")
   fatalSearch = []
   noTrailer = []
   destNotOak4 = []
   trailer = {}
   warehouse = {}
   
   try:
      headless = Options()
      headless.headless = True
      driver = webdriver.Firefox(executable_path="C:\\Users\\thomhat\\Anaconda3\\pkgs\\geckodriver-0.29.0-hdb13177_0\\Scripts\\geckodriver", options=headless)
      url = "http://fc-inbound-transshipment-portal-prod-na.iad.proxy.amazon.com/SearchTransfer"
      driver.get(url)

      endDate = 99/99/9999
      dateRange = datetime.timedelta(days=23)
      for counter in range(len(data)):
         if(counter==len(data) or counter%100==0):
            print(f"{counter} containers scraped...")
         if(data.at[counter, 'timestamp'] != endDate):
            endDate = data.at[counter, 'timestamp']
            endOb = datetime.datetime.strptime(endDate, "%m/%d/%Y").date()
            startOb = endOb-dateRange
            startDate = datetime.date.strftime(startOb, "%m/%d/%Y")
            end = driver.find_element_by_name("endDate")
            end.clear()
            end.send_keys(endDate)      
            start = driver.find_element_by_name("startDate")
            start.clear()
            start.send_keys(startDate)
         try:
            search = driver.find_element_by_name("searchText")
         except NoSuchElementException as exception:
            fatalSearch.append(data.at[counter, 'containers'])
            continue
         except StaleElementReferenceException as exception:
            fatalSearch.append(data.at[counter, 'containers'])
            continue
         search.clear()
         search.send_keys(data.at[counter, 'containers'])
         search.submit()
         time.sleep(3)
         xPathRoot = r"/html/body/div[1]/div/div/table"
         try:
            home = driver.find_element_by_xpath(xPathRoot)
            body = home.find_element_by_tag_name('tbody')
         except NoSuchElementException as exception:
            noTrailer.append(data.at[counter, 'containers'])
            continue
         try:
            dest = body.find_element_by_xpath("//tr/td[contains(.,'OAK4')]")
            key = dest.find_element_by_xpath("//../td[4]/span").text
            trailer[data.at[counter, 'containers']] = key
            if key in warehouse:
               warehouse[key] += 1
            else:
               warehouse[key] = 1
         except NoSuchElementException as exception:
            destNotOak4.append(data.at[counter, 'containers'])
            continue
   except KeyboardInterrupt as exception:
      fatalSearch = pd.DataFrame(fatalSearch, columns = ["Fatal Search"])
      noTrailer = pd.DataFrame(noTrailer, columns = ["No Trailer"])
      destNotOak4 = pd.DataFrame(destNotOak4, columns = ["Destination Not OAK4"])
      trailer = pd.DataFrame(trailer, index = [0]).T
      warehouse = pd.DataFrame(warehouse, index = [0]).T
 
      fatalSearch.to_csv(r"C:\Users\thomhat\Documents\output\fatalSearchout.csv")
      noTrailer.to_csv(r"C:\Users\thomhat\Documents\output\noTrailerout.csv")
      destNotOak4.to_csv(fr"C:\Users\thomhat\Documents\output\destNotOak4out.csv")
      trailer.to_csv(r"C:\Users\thomhat\Documents\output\trailerout.csv")
      warehouse.to_csv(r"C:\Users\thomhat\Documents\output\warehouseout.csv")
      print("Completed work has been saved")
      sys.exit(0)
   driver.quit()

   return (fatalSearch, noTrailer, destNotOak4, trailer, warehouse)

def postprocess(postscrape):
   """takes a tuple of sorted data returned from scrape(), prepares data for visualization, then saves 5  csv files to local Documents folder"""

   print("Postprocessing web scrape for data visualization...")
   print()

   #plot data
   xlabels = []
   yvalues = []
   warehouseList = list(postscrape[4].items())
   warehouseList.sort(reverse=True, key=second)
   for i in warehouseList[0:10]:
      xlabels.append(i[0])
      yvalues.append(i[1])
   plt.bar(xlabels, yvalues)
   plt.xlabel("FC")
   plt.ylabel("Number of Containers")
   plt.title("Dropped Containers From Top 10 FCs")
   for x, y in enumerate(yvalues):
      plt.text(y, x, str(y))
   #plt.show()
   plt.savefig(r"C:\Users\thomhat\Documents\output\Graph(1).jpeg")

   print("Sending web scrape data to csv files...")
   print()
   #convert to dataframes
   fatalSearch = pd.DataFrame(postscrape[0], columns = ["Fatal Search"])
   noTrailer = pd.DataFrame(postscrape[1], columns = ["No Trailer"])
   destNotOak4 = pd.DataFrame(postscrape[2], columns = ["Destination Not OAK4"])
   trailer = pd.DataFrame(postscrape[3], index = [0]).T
   warehouse = pd.DataFrame(warehouseList, columns = ["Warehouse", "PC99"])

   #convert to csv files
   fatalSearch.to_csv(r"C:\Users\thomhat\Documents\output\fatalSearchout.csv")
   noTrailer.to_csv(r"C:\Users\thomhat\Documents\output\noTrailerout.csv")
   destNotOak4.to_csv(fr"C:\Users\thomhat\Documents\output\destNotOak4out.csv")
   trailer.to_csv(r"C:\Users\thomhat\Documents\output\trailerout.csv")
   warehouse.to_csv(r"C:\Users\thomhat\Documents\output\warehouseout.csv")

   return 1

def second(element):
   return element[1]


if __name__ == '__main__':
   """Driver function to conduct data wrangling"""
   print("This tool categorizes PC99 units into their respective trailers and displays this data as a bar chart. If no trailer is found, this program will categorize the container according to the respective error it encountered when trying to find the trailer (Ex: destNotOak4.csv stores all containers which destination FC did not oatch OAK4). All data passed in will be saved for future reference.")
   print()
   print(r"Please provide the path to the PC99 csv file you would like to process. **This file must contain no more than 7 days worth of data. To avoid long wait times of over a day, it is recommended to pass no more than one day's worth of data. Due to this program's conversion of user input files, number of containers scraped in program will be signifcantly larger than that of the original file, roughly 1.5X. Take note that 100 containers takes 5 minutes on average to process. If you would like to exit the program ans save what's completed, please press CTRL+C. This must be done during while the program is web scraping.** Example input format: C:\Users\thomhat\Documents\PC99May21.csv")
   filePath = input("Enter path here: ")
   print()

   prescrape = preprocess(filePath) #optimize csv for web scraping, returns dataframe
   postscrape = scrape(prescrape) #scrapes site, returns tuple of 5 data metrics
   complete = postprocess(postscrape) #sends scrape data to csv files and plots

   if(complete == 1):
      print("Complete")
   else:
      print("Error in completion")
