import requests
import datetime
import os

def yyyymmdd(date):
    year = date.year
    month = date.month
    day = date.day

    return "%04d%02d%02d"%(year,month,day)

def yyyymm(date):
    year = date.year
    month = date.month

    return "%04d%02d"%(year,month)

def tryURL(url):
    r = requests.head(url)
    #print(r.status_code)
    if r.status_code != 200:
        #print(r.headers)
        return False
    else:
        return True


def getLatestURL(verbose = False):


    baseURL = "https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-003-1.0-degree/analysis"
    #baseURL = "https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-003-1.0-degree/forecast"


    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)

    if verbose: print("Checking for new weather data...")

    for i in range(10):
        day = today - i*oneday

        monthstr = yyyymm(day)
        daystr = yyyymmdd(day)

        dayURL = os.path.join(baseURL,monthstr,daystr)+"/"
        # print("")
        # print(daystr)

        if not tryURL(dayURL):
            # print("No data")
            continue

        if verbose: print("Page for %s exists! This is %d days old"%(day,i))

        for time in ["1800","1200","0600","0000"]:
            num = "000"
            base = "gfs_3_%s_%s_%s.grb2"%(daystr,time,num)
            fileURL = os.path.join(dayURL,base)
            # print("    %s"%fileURL)
            if tryURL(fileURL):
                if verbose: print('Latest timestamp is %s'%time)
                return fileURL
            else:
                continue
                # print("Does not exist")

    if verbose: print("No data found")
    return None


if __name__ == "__main__":
    URL = getLatestURL()
    print("URL = %s"%URL)




