import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import os
import base64
from pyvirtualdisplay import Display

display = Display(visible=0, size=(800, 600))
display.start()

fp = webdriver.FirefoxProfile()
fp.set_preference("browser.download.folderList", 2)
fp.set_preference("browser.download.dir", os.getcwd())
fp.set_preference("browser.download.downloadDir", os.getcwd())
fp.set_preference("browser.download.lastDir", os.getcwd())
fp.set_preference("browser.download.manager.showWhenStarting", True)
fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

driver= webdriver.Firefox(firefox_profile=fp)
#driver = webdriver.Firefox()
driver.get("https://www.google.com/webmasters/tools/sitemap-list?hl=en&siteUrl=http://www.criminology.com/")



emailid=driver.find_element_by_id("Email")
emailid.send_keys("email@gmail.com")

password = '<password>'

passw=driver.find_element_by_id("Passwd")
passw.send_keys(base64.b64decode(password))

signin=driver.find_element_by_id("signIn")
signin.click()

driver.implicitly_wait(10) # 10 seconds

#time.sleep(10)
button = driver.find_element_by_id("gwt-uid-163")
button.click()
button_ok = driver.find_element_by_css_selector("button[class='GOJ0WDDBBU GOJ0WDDBMU']")
button_ok.click()
driver.quit()
display.stop()
