from selenium import webdriver
from selenium.webdriver.common.keys import Keys 

from collections import OrderedDict
import os
import re
import requests
import ast 
import time
import random
import winsound

loopCatalog = True
'''important variables
1. Current ROBUX (UNNECESSARY)
2. Item table values/demand (Only go for Normal Demand+) D
3. Custom made RAP Item table (normal - high demand), custom values to prevent projections D
4. Names of users of sent trades (to prevent spamming)
'''

'''Trading algorithm
-ONLY SEND WINS:
-UPGRADING: Send <= value, no matter rap or value 
-DOWNGRADING: Get 250+ each trade, downgrade slightly 
'''

'''Bot procedure
1. Parse data from rolimons 
2. Open Roblox and log in (manual)
3. Browse through rolimons and send trades 
4. Open user in new tab, check if can trade, open trade in current tab
5. Find trade 
6. Send trade, close tab
7. Record username of player
'''
    
class Bot:
    def __init__(self, accountID, username, password): 
        '''Initiates bot, declares variables, limits spam trades'''
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("browser.privatebrowsing.autostart", False)
        self.videoMode = False #send 50 trades quick and take break
        self.upgradeMode = True
        self.driver = webdriver.Firefox(firefox_profile=firefox_profile)        
        self.actions = webdriver.ActionChains(self.driver)
        self.tradesSent = 0
        self.startTime = time.time()
        self.ID = accountID
        self.username = username
        self.password = password
        self.homePage = "https://www.roblox.com/home"
        self.currentTrade = []
        self.sentUsers = []
        self.blockedUsers = []
        self.notForTrade = ["Bunny Brigade", "Headrow"]
        self.targetItems = []
        self.blacklist = ["Bucket"]
        self.lastWait = time.time()
        self.waitTime = 30
        #Open file to see the time of last reset
        lastCheck = open("lastCheck.txt", "r")
        lastTime = lastCheck.readline().strip()
        lastCheck.close()
        if time.time() - float(lastTime) >= 86400: #See if 1 day has passed since reset
            lastCheck = open("lastCheck.txt", "w")
            lastCheck.write(str(time.time()))
            lastCheck.close()
            dailyUsers = open("dailyUsers.txt", "w") #Reset file
        else:
            #Since 1 day hasn't passed, get all sent trades 
            dailyUsers = open("dailyUsers.txt", "r")
            self.sentUsers = [user.strip() for user in dailyUsers]
        dailyUsers.close()
        blockedUsers = open("blockedUsers.txt", "r")
        self.blockedUsers = [user.strip() for user in blockedUsers]
        blockedUsers.close()
        
    def setup(self, allItems, valueItems, rapData):
        '''Declares tables and data of items, logs in to account'''
        self.allItems = allItems
        self.valueItems = valueItems
        self.dictValueItems = OrderedDict(valueItems)
        self.rapData = rapData
        driver = self.driver
        driver.get("https://www.roblox.com/login")   
        inputUsername = driver.find_element_by_xpath("//input[@name='username']")
        inputUsername.clear()
        for char in self.username:
            inputUsername.send_keys(char)
            time.sleep(random.random())
        #Input password into element, types in password at random intervals and click enter
        inputPassword = driver.find_element_by_xpath("//input[@name='password']")
        inputPassword.clear()
        for char in self.password:
            inputPassword.send_keys(char)
            time.sleep(random.random())        
        inputPassword.send_keys(Keys.RETURN)
        time.sleep(10)             
        #In case of bot security check
        if self.driver.current_url != "https://www.roblox.com/home?nl=true":
            winsound.PlaySound('sound.wav', winsound.SND_FILENAME)
            input("Bot Check! Input anything when finished: ")
        
        #input("Log in to your account. Type anything to continue: ") 
       
    def browseUsers(self):
        '''Go to the rolimons site, browse through users who have recently acquired normal demand + items. Send them trades'''
        for item, data in self.valueItems:
            if data["demand"] == None or data["trend"] == None: continue
            if data["demand"] >= 2 and data["trend"] >= 2: #NOTE: THIS IS TEMPORARY, FIND A MORE EFFICIENT WAY OF DECIDING WHICH PAGE TO START AT.
                #blacklisted items
                temp = []
                if item in temp: continue
                self.driver.get("https://www.rolimons.com/item/" + data["id"])
                currentWindow = self.driver.current_window_handle
                time.sleep(7)
                ownerSince = self.driver.find_element_by_xpath("//th[@aria-label='Owned Since: activate to sort column ascending']")
                #Scroll down so button can be clicked
                self.driver.execute_script("window.scrollTo(0, 950);")
                #Click twice to sort from newest to oldest
                ownerSince.click()
                ownerSince.click()
                #Show 50 players per page
                self.driver.find_element_by_name("bc_owners_table_length").click()
                self.driver.find_element_by_xpath("//option[@value='50']").click()
                #Get links to every trade page 
                currentPage = self.driver.find_elements_by_link_text("Trade")
                #Filter links so there are no duplicates and they are not in the list of blocked users/daily sent users
                links = list(dict.fromkeys([x.get_attribute('href') for x in currentPage if x.get_attribute('href') not in self.sentUsers and x.get_attribute('href') not in self.blockedUsers]))  
                for link in links:
                    if link in self.sentUsers: continue
                    #Reset item lists
                    myItems = []
                    theirItems = []                    
                    count = 0
                    failed = False
                    #Open new tab and go to trade link
                    self.driver.execute_script('''window.open("about:blank");''')
                    # Get new window/tab ID
                    newWindow = [window for window in self.driver.window_handles if window != currentWindow][0]          
                    # Switch to new window/tab
                    self.driver.switch_to.window(newWindow)                    
                    self.driver.get(link)
                    time.sleep(5)
                    #Check if trading is possible with user
                    if self.driver.current_url == self.homePage: #5/7/19 Failed to decode response from marionette not fixed (error only happened once)
                        self.blockedUsers.append(link)
                        self.closeWindow(currentWindow)   
                        blockedUsers = open("blockedUsers.txt", "a")
                        blockedUsers.write(link + "\n")
                        blockedUsers.close()                        
                        continue
                    #LOOP THIS AS MANY TIMES AS I CAN CLICK THE RIGHT ARROW!
                    temp = True
                    while temp:  
                        try:
                            myItemsElement = self.driver.find_element_by_xpath("//div[@ownedbyuser='True']")
                            myPageItems = myItemsElement.find_elements_by_class_name("InventoryItemContainerInner") 
                            for x in myPageItems:
                                itemName = x.find_element_by_class_name("InventoryItemLink").text
                                currentRap = x.find_element_by_class_name("ItemInfoData")
                                if itemName and itemName not in self.notForTrade: 
                                    myItems.append([itemName, float(currentRap.get_attribute('innerHTML'))])                            
                            if "paging_next disabled" in myItemsElement.get_attribute("outerHTML"):
                                temp = False
                            else: 
                                myItemsElement.find_element_by_class_name("paging_next").click()
                        except Exception as e:
                            print(e)
                            failed = True
                            break                   
                    #LOOP THIS AS MANY TIMES AS I CAN CLICK THE RIGHT ARROW!
                    temp = True
                    while temp:
                        try:
                            theirItemsElement = self.driver.find_element_by_xpath("//div[@ownedbyuser='False']")
                            theirPageItems = theirItemsElement.find_elements_by_class_name("InventoryItemLink") #Try InventoryItemName
                            for x in theirPageItems:
                                if x.text and (not self.targetItems or x.text in self.targetItems):
                                    theirItems.append(x.text)                                         
                            if "paging_next disabled" in theirItemsElement.get_attribute("outerHTML"):
                                temp = False
                            else: 
                                theirItemsElement.find_element_by_class_name("paging_next").click()                    
                                count += 1
                                if count >= 10: 
                                    time.sleep(1)
                                    failed = True
                                    self.blockedUsers.append(link)
                                    blockedUsers = open("blockedUsers.txt", "a")
                                    blockedUsers.write(link + "\n")
                                    blockedUsers.close()                                                    
                                    break
                        except:
                            failed = True
                            break
                    self.currentTrade.clear()
                    if not failed and (self.downgrade(myItems, theirItems) or self.upgrade(myItems, theirItems)):
                        if self.makeTrade() != False and self.checkTrade(): #makeTrade() will only return false if an error occurs, otherwise returns nothing
                            self.tradesSent += 1
                            print("Trades Sent:", self.tradesSent)
                            if not self.tradesSent % 10: #every 10 trades
                                currentTime = time.time()
                                timeTaken = currentTime - self.lastWait
                                self.waitTime += (720 - timeTaken)/10
                                if self.waitTime < 0: 
                                    self.waitTime = 0
                                self.lastWait = currentTime
                            if self.videoMode:
                                self.waitTime = 0
                                #if not self.tradesSent % 50: time.sleep(3600) #Wait 1 hour
                            self.driver.find_element_by_class_name("SendTrade").click()   
                            #Wait 0.5 seconds
                            time.sleep(0.5)
                            self.driver.find_element_by_id("roblox-confirm-btn").click()              
                            self.sentUsers.append(link)
                            dailyUsers = open("dailyUsers.txt", "a")
                            dailyUsers.write(link + "\n")
                            dailyUsers.close()
                        else:
                            self.closeWindow(currentWindow)
                            continue
                    else:
                        self.closeWindow(currentWindow)
                        continue                        
                    self.closeWindow(currentWindow)    
                    time.sleep(self.waitTime)
                    #If 6 hours have passed, restart the program (restart RAM used)
                    #if time.time() - self.startTime >= 21600: 
                        #print("6 HOURS PASSED, RESTARTING")
                        #self.driver.quit()
                        #return

    def closeWindow(self, currentWindow):    
        '''Close current window and go back to main window'''
        time.sleep(1)
        # Close new window/tab
        self.driver.close()
        # Switch to initial window/tab
        self.driver.switch_to.window(currentWindow)
                    
    def makeTrade(self):
        '''On the trade tab, make a trade with user'''
        #Loop through my item list, find on page, if not left scroll until the item is found. When found, scroll back to last page with right arrow.
        #Repeat with their items
        try:
            myItems = [x[0] for x in self.currentTrade[2]]
            theirItems = [x[0] for x in self.currentTrade[1]]
            print("My items for trade:", myItems)
            print("Their items for trade:", theirItems)
            temp = True
            while temp:
                myItemsElement = self.driver.find_element_by_xpath("//div[@ownedbyuser='True']")
                myPageItems = myItemsElement.find_elements_by_class_name("InventoryItemContainerInner") 
                for x in myPageItems:
                    itemName = x.find_element_by_class_name("InventoryItemLink").text 
                    if itemName in myItems:
                        x.find_element_by_class_name("ItemImg").click()
                        myItems.remove(itemName)
                        #Move mouse to different element
                        self.driver.find_element_by_class_name("AddRobuxBox").click()
                        #self.actions.move_by_offset(700, 500)
                        time.sleep(0.5)
                if "paging_previous disabled" in myItemsElement.get_attribute("outerHTML"):
                    temp = False
                else: 
                    myItemsElement.find_element_by_class_name("paging_previous").click()   
            temp = True
            while temp:
                theirItemsElement = self.driver.find_element_by_xpath("//div[@ownedbyuser='False']")
                theirPageItems = theirItemsElement.find_elements_by_class_name("InventoryItemContainerInner") 
                for x in theirPageItems:
                    itemName = x.find_element_by_class_name("InventoryItemLink").text
                    if itemName in theirItems:
                        x.find_element_by_class_name("ItemImg").click()
                        theirItems.remove(itemName)
                        self.driver.find_element_by_class_name("OfferHeader").click()
                        #self.actions.move_by_offset(700, 500)
                        time.sleep(0.5)
                if "paging_previous disabled" in theirItemsElement.get_attribute("outerHTML"):
                    temp = False
                else: 
                    theirItemsElement.find_element_by_class_name("paging_previous").click()       
        except:
            return False
        
    def checkTrade(self):
        '''Check to see if trade is legitimate - verify items'''
        myOffer = self.driver.find_element_by_xpath("//div[@list-id='OfferList0']")
        myOfferItems = myOffer.find_elements_by_class_name("InventoryItemContainerOuter")
        theirOffer = self.driver.find_element_by_xpath("//div[@list-id='OfferList1']")
        theirOfferItems = theirOffer.find_elements_by_class_name("InventoryItemContainerOuter")        
        if len(self.currentTrade[2]) == len(myOfferItems) and len(self.currentTrade[1]) == len(theirOfferItems):
            return True
        else:
            return False
        
    def getRapData(self):
        '''Gathers data from the ROBLOX Catalog, returns a list containing lists of items on the respective page based on bestselling in the past week.'''
        self.driver.get("https://www.roblox.com/catalog/?Category=2&Subcategory=2&SortType=2&SortAggregation=3&Direction=2")
        time.sleep(5)
        items = []
        for x in range(5):
            #HTML of current page
            catalogHtml = self.driver.page_source
            #Parses all titles
            pageItems = re.findall(r'title="(.*?)"',catalogHtml)
            #Removes all garbage after parsing
            garbage = ['Relevance', 'Most Favorited', 'Bestselling', 'Recently Updated', 'Price (High to Low)', 'Price (Low to High)', 'All Time', 'Past Week', 'Past Day']
            for y in garbage:
                pageItems.remove(y)
            #Add to rap list
            items.append(pageItems)
            #Next page
            nextButton = self.driver.find_element_by_class_name('pager-next')
            nextButton.click()
            time.sleep(3)
        #Collects 6th page data
        catalogHtml = self.driver.page_source
        pageItems = re.findall(r'title="(.*?)"',catalogHtml)
        for y in garbage:
            pageItems.remove(y)        
        items.append(pageItems)
        return items
    
    #Algorithm from: https://stackoverflow.com/questions/34517540/find-all-combinations-of-a-list-of-numbers-with-a-given-sum
    def findDG(self, numbers, target, count, partial=[]):
        '''Recursive function used to find downgrade given items'''
        if count > 4: return 
        s = sum([x[1] for x in partial])
        # check if the partial sum is equals to target
        if target[1] - 50 <= s <= target[1] + 500: 
            sinCount = 0
            if target == 7350: 
                for item in partial: 
                    if target[1] == 3500: 
                        sinCount += 1
                        if sinCount == 2: return
            if self.currentTrade:
                if abs(s-target[1]) < self.currentTrade[0]:
                    self.currentTrade.clear()
                    self.currentTrade.extend((abs(s-target[1]), partial, [[target[0], target[1]]] ))
            else:
                self.currentTrade.extend((abs(s-target[1]), partial, [[target[0], target[1]]] ))
        if s > target[1] + 500:
            return
    
        for i in range(len(numbers)):
            n = numbers[i]
            remaining = numbers[i+1:]
            self.findDG(remaining, target, count + 1, partial + [n]) 
    
    #Algorithm from: https://stackoverflow.com/questions/34517540/find-all-combinations-of-a-list-of-numbers-with-a-given-sum
    def findUG(self, numbers, target, count, rapUpgrade, partial=[]):
        '''Recursive function used to find upgrade given items'''
        if count > 4: return 
        s = sum([x[1] for x in partial])
        # check if the partial sum is equals to target
        if target[1] - 225 <= s <= target[1] + 75: 
            #Make sure not to pay for value item with all rap Items
            oneValue = False
            for item in partial:
                if self.dictValueItems.get(item[0]):
                    oneValue = True
            if not oneValue and not rapUpgrade: return
            if self.currentTrade:
                if abs(s-target[1]) < self.currentTrade[0]:
                    self.currentTrade.clear()
                    self.currentTrade.extend((abs(s-target[1]), [[target[0], target[1]]], partial))
            else:
                self.currentTrade.extend((abs(s-target[1]), [[target[0], target[1]]], partial))
        if s > target[1] + 100:
            return
    
        for i in range(len(numbers)):
            n = numbers[i]
            remaining = numbers[i+1:]
            self.findUG(remaining, target, count + 1, rapUpgrade, partial + [n]) 
            
    def downgrade(self, botItems, playerItems):
        ''' Takes in items of both users and returns best possible downgrade'''
        #DG Algorithm: (value - 5000)/1000 * 75 + 250 #UPDATE: CHANGED 75 TO 50 
        if self.upgradeMode: return False
        valueItems = self.dictValueItems
        rapData = self.rapData
        tradeableItems = []
        #Checks if items are valued 
        for item in playerItems:
            if item in self.blacklist: continue
            try:
                if valueItems.get(item) != None and valueItems[item]["demand"] >= 2 and valueItems[item]["trend"] >= 2:
                    #if not any([valueItems[item]["value"] in item for item in tradeableItems]): #Checks if an item of this value is already in the list
                    #Check if 2 items of that value are already in the list
                    count = 0
                    for itemx in tradeableItems:
                        if valueItems[item]["value"] in itemx:
                            count += 1
                    if count < 2:
                        tradeableItems.append([item, valueItems[item]["value"]]) 
                if rapData.get(item) != None and rapData[item]["appearances"] >= 5 and rapData[item]["demand"] >= 1:
                    tradeableItems.append([item, rapData[item]["value"]])       
            except Exception as e:
                print(e)
                return False
        
        if tradeableItems:
            #Sort by value
            tradeableItems = sorted((tradeableItems), key=lambda x: x[1])
            for item in botItems:
                item = item[0]
                if valueItems.get(item) == None: continue
                findItems = []
                myValue = valueItems[item]["value"]
                if myValue >= 5000:
                    overpay = (myValue - 5000) * 0.05 + 250
                else:
                    overpay = -250
                desiredValue = myValue + overpay 
                findItems = list(filter(lambda x: x[1] < myValue, tradeableItems))
                if findItems: #Find values that add up to my desiredValue (or close)
                    self.findDG(findItems, [item, desiredValue], 0)
        return self.currentTrade
                    
    def upgrade(self, botItems, playerItems):
        ''' Takes in items of both users and returns best possible upgrade'''
        #UG Algorithm: find = value
        valueItems = self.dictValueItems
        rapData = self.rapData        
        myItems = []
        myRapItems = []
        tradeableItems = []
        myRapValue = 0 
        #Checks if items are valued 
        try:
            for item in playerItems:
                if item in self.blacklist: continue
                if valueItems.get(item) != None and valueItems[item]["demand"] >= 2 and valueItems[item]["trend"] >= 2:
                    tradeableItems.append([item, valueItems[item]["value"]]) 
            for item in botItems:
                if valueItems.get(item[0]) != None:
                    myItems.append([item[0], valueItems[item[0]]["value"]])
                elif rapData.get(item[0]) != None:
                    if rapData[item[0]]["value"] > item[1]: 
                        myRapValue += rapData[item[0]]["value"]
                        myRapItems.append([item[0], rapData[item[0]]["value"]])
                        myItems.append([item[0], rapData[item[0]]["value"] * 1.1])#Note: * 1.1 is used because rap items are valued more     
                    else:
                        myRapValue += item[1]
                        myRapItems.append([item[0], item[1]])
                        myItems.append([item[0], item[1] *1.1])
                elif self.allItems.get(item[0]) != None: #All other items (sometimes for manually accepted trades that aren't in rap or value table)
                    if self.allItems[item[0]][22] > item[1]:
                        myRapValue += self.allItems[item[0]][22]
                        myRapItems.append([item[0], self.allItems[item[0]][22]])
                        myItems.append([item[0], self.allItems[item[0]][22] * 1.1]) 
                    else:
                        myRapValue += item[1]
                        myRapItems.append([item[0], item[1]])
                        myItems.append([item[0], item[1] * 1.1])                         
                
        except Exception as e:
            print(e)
            return False
                
        if tradeableItems:
            #Sort by value
            tradeableItems = sorted((tradeableItems), key=lambda x: x[1])
            myItems = sorted((myItems), key=lambda x: x[1])
            #Search for a rap upgrade
            if myRapValue >= 2450: 
                for item in tradeableItems:
                    item = item[0]
                    findItems = []
                    theirValue = valueItems[item]["value"] * 0.8
                    findItems = list(filter(lambda x: x[1] < theirValue, myRapItems))
                    if findItems: #Find values that add up to my desiredValue (or close)
                        self.findUG(findItems, [item, theirValue], 0, True)   
                        if self.currentTrade: return self.currentTrade
                        
            for item in tradeableItems:
                item = item[0]
                findItems = []
                theirValue = valueItems[item]["value"]
                if theirValue == 3500: theirValue = 2650 #DO NOT OVERPAY FOR SIN OR BUCKET
                findItems = list(filter(lambda x: x[1] < theirValue, myItems))
                if theirValue >= 20000: theirValue += 425
                if findItems: #Find values that add up to my desiredValue (or close)
                    self.findUG(findItems, [item, theirValue], 0, False)    
                    
        return self.currentTrade

def getItemTable():
    '''Opens rolimons and turns data into html, returns full itemTable'''
    itemTable = {}
    url = "https://www.rolimons.com/itemtable"
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    response = requests.get(url, headers = headers)
    html = str(response.content)
    #Parse data into a dictionary
    start = html.find('item_details = ') + 15
    end = html.find('highlight current page') - 16
    #Turn table into a 'string table', replace known outlier names
    table = html[start:end].replace("null", "None").replace("\"\\\\\"Like Clockwork\\\\\" Top Hat\"", "'\"Like Clockwork\" Top Hat'").replace('\\xc3\\xa9', 'é')
    temp = open("temp.txt", "w")
    temp.write(table)
    temp.close()
    allItems = ast.literal_eval(table)
    #Swaps name of key and id and deletes old item table
    for item, data in allItems.items():
        itemTable[data[0]] = data
        itemTable[data[0]][0] = item    
    return itemTable

def getValueTable(itemTable):
    '''Returns a table of value items based on the Rolimons itemtable'''
    valueItems= {}
    #Creates value table
    for item, data in itemTable.items():
        if data[16] != None: #Makes sure its valued
            valueItems[item.strip()] = {"id":data[0], "demand":data[17], "trend":data[18], "value":data[16]}
    #Sorts by value
    valueItems = sorted(valueItems.items(), key=lambda i: i[1]['value'])
    return valueItems

def updateRapData(tradeBot, new):
    '''Calls the bot to gather new Rapdata, updates existing rap data table'''
    if new:
        newCatalog = tradeBot.getRapData()
        rapItems = {}
        newRap = {} 
        tempValueItems = OrderedDict(valueItems)
        for page in range(len(newCatalog)):
            for item in newCatalog[page]:
                try:
                    if itemTable.get(item)[19] != None: continue #Checks if projected 
                    if tempValueItems.get(item.strip()) != None: continue #Checks if on value table 
                    newRap[item] = {"id":itemTable.get(item)[0], "demand":6-page, "value":itemTable.get(item)[22], "appearances":1, "runs":1}
                except TypeError:
                    if item == "Summertime 2009 R&amp;R&amp;R":
                        newItem = "Summertime 2009 R&R&R"
                        if itemTable.get(newItem)[19] != None: continue 
                        newRap[newItem] = {"id":itemTable.get(newItem)[0], "demand":6-page, "value":itemTable.get(newItem)[22], "appearances":1, "runs":1}
    #Looks for RAP Chart stored data, and update
    #If it does not exist, make newRAP the stored data table 
    exist = False
    try: 
        file = open("rapData.txt", "r")
        rapData = ast.literal_eval(file.readline())
        file.close()
        exist = True
    except FileNotFoundError:
        file = open("rapData.txt", "w")
        file.write(str(newRap))
        file.close()
        return False
        
    if exist and new:
        for item, data in rapData.items():
            data["runs"] += 1
            if newRap.get(item) == None:
                data["demand"] = data["demand"] / data["runs"]
        for item, data in newRap.items():
            storedData = rapData.get(item)
            if storedData == None:
                rapData[item] = data
            else:
                appearances = storedData["runs"]
                storedData["demand"] = (storedData["demand"] * (appearances-1) + data["demand"])/(appearances)
                storedData["value"] = (storedData["value"] * (appearances-1) + data["value"])/(appearances)
                storedData["appearances"] += 1
        file = open("rapData.txt", "w")
        file.write(str(rapData))
        file.close()
    return rapData

#0 = ID
#16 = Valued? (None = Not demanded, otherwise its value)
#17 = Demand (None = No Demand, 0 = Terrible, 1 = Low, 2 = Normal, 3 = High, 4 = Amazing)
#18 = Trend (None = No trend, 0 = Falling, 1 = Unstable, 2 = Stable, 3 = Raising)
#22 = Value (Value of item, if not valued, then rap)
itemTable = getItemTable()
#valueItems[name] = {id, demand, trend, value}
username = "ENTER USERNAME HERE"
password = "ENTER PASSWORD HERE"
valueItems = getValueTable(itemTable)
itemStart = 0
while True:
    tradeBot = Bot("1016519351", username, password)
    rapData = updateRapData(tradeBot, loopCatalog) #loopCatalog is the boolean value on the top
    if rapData: 
        tradeBot.setup(itemTable, valueItems, rapData)
        tradeBot.browseUsers()
    else:
        print("Not enough data, make loopCatalog true and run the bot atleast five times to gather data.")
