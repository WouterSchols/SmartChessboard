from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=c:/Users/woute/AppData/Local/Google/Chrome/User Data/")
    #options.add_extension("c:/Users/woute/AppData/Local/Google/Chrome/User Data/Profile 1/Extensions/bghaancnengidpcefpkbbppinjmfnlhh/5.4.0_0/")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.chess.com/play/computer")
    input()
    elem = driver.find_element_by_name("piece wp square-52")
    elem.click()
    elem2 = driver.find_element_by_name("piece wp square-52")
    elem2.click()

    driver.close()
