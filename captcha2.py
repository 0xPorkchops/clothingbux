from selenium import webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--remote-debugging-port:9222')
browser = webdriver.Chrome(chrome_options=chrome_options)
