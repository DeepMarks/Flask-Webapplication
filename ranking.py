import camelot
import csv
import requests

url1 = "https://racketlon.ch/images/stories/Wettkampf_2019/Ranking_SRF_M_"
year = 20
month = 1
for i in range(12):
    if month <= 9:
        url = url1 + str(year) + "_0" + str(month) + "_01" + ".pdf"
    else:
        url = url1 + str(year) + "_" + str(month) + "_01" + ".pdf"
    print(url)
    r = requests.get(url,timeout=1)
    try:
        r.raise_for_status()
    except:
        pass
    if r.status_code == 200:
        # readinf the PDF file that contain Table Data
        # you can find find the pdf file with complete code in below
        # read_pdf will save the pdf table into Pandas Dataframe
        table = camelot.read_pdf(url)
        number = i + 1
        table[0].to_csv("ranking" + str(number) + ".csv")

    i += 1
    month += 1