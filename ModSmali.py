import os
import sys
import re
import random
from xml.etree.ElementTree import parse as xmlParse
from elftools.elf.elffile import ELFFile

def FindManifest(folderName) :
    print("FindManifest [%s] ..." % folderName)
    maniPath = folderName+"\AndroidManifest.xml"
    if not os.path.isfile(maniPath) :
        print("| Cannot find Manifest file %s" % maniPath)
        return None
    print("| ... %s Found!" % maniPath)
    return maniPath

def FindMainAct(folderName, maniPath) :
    print("Find Main Activity [%s : %s]" % (folderName, maniPath))
    data = xmlParse(maniPath)
    root = data.getroot()
    app = root.find("application")
    if app == None :
        print("| ... Cannot find any application in manifest")
        return None
    print("| ... Find application... ")
    
    actList = app.findall("activity")
    if len(actList) == 0 :
        print("| ... Cannot find any activity in manifest")
        return None
    print("| ... Find %s activity... " % len(actList))
        
    intentDic = {}
    for act in actList :
        actName = None
        for itemSet in act.items() :
            if itemSet[0].endswith("name") :
                actName = itemSet[1]
        intFilter = act.findall("intent-filter")
        if not len(intFilter) == 0 :
            intentDic[actName] = intFilter
            
    if len(intentDic) == 0 :
        print("| ... Cannot find any activity with intent-filter")
        return None
    print("| ... Find %s activity with intent-filter... " % len(intentDic))       
            
    returnList = []
    for k, v in intentDic.items() :
        for intent in v :
            actions = intent.findall("action")
            for action in actions :
                for itemSet in action.items() :
                    if itemSet[0].endswith("name") :
                        if itemSet[1].endswith("MAIN") :
                            print("| ... Find action [%s] in activity [%s]" % (itemSet[1], k)) 
                            returnList.append((k, itemSet[1]))
    
    if not len(returnList) == 1 :
        print("| ... Find Multiple MAIN activity!")
        for tup in returnList :
            print("| -- %s", tup[0])
        return None
    else :
        return returnList[0][0]
        
        
def FindSmali(folderName, mainAct) :
    print("FindSmali [%s]" %(mainAct))
    steps = mainAct.split(".")
    mainFolders = os.listdir(folderName)
    smaliFolders =[]
    for folder in mainFolders :
        if os.path.isdir(folderName+"\\"+folder) :
           if(re.search("smali", folder)) :
               smaliFolders.append(folderName+"\\"+folder)
    if len(smaliFolders) == 0 :
        print("| ... Cannot find Smali-Related folder!")
        return None
    print("|... Find %d Smali-Related folders" % len(smaliFolders))
    
    stepCache = []
    files = []
    for str in smaliFolders :
        stepCache.append(str)
    
    for level in steps :
        count = 0
        levelCache = []
        
        for dir in stepCache :
            items = os.listdir(dir)
            for v in items :
                if os.path.isdir(dir+"\\"+v) :
                    if re.search(level, v) :
                        levelCache.append(dir+"\\"+v)
                if os.path.isfile(dir+"\\"+v) :
                    if re.search(level, v) :
                        files.append(dir+"\\"+v)
    
        stepCache = levelCache

    targetFiles = []
    for file in files :
        print(steps[-1], file)
        if re.search(steps[-1], file) :
            targetFiles.append(file)

    if len(targetFiles) == 0:
        print("|... Cannot find any related file!")
        return None
    print("|... Find %d Target smali file", len(targetFiles))
    
    for file in targetFiles :
        print("| - File [%s]" % file)
    
    
    return targetFiles

def FindEntrySmali(smaliList, mainAct) :
    print("FindEntrySmali [%s]" % mainAct)
    targetStr = "\.method protected onCreate\("
    result = []
    for file in smaliList :
        filePointer = open(file,"rt")
        data = filePointer.read()
        if re.search(targetStr, data) :
            print("| Find onCreate() in smali file [%s]" % file)
            result.append(file)
            
    if len(result) == 0 :
        print("| Cannot fine onCreate() method from files")
        return None
    if len(result) > 1 : 
        print("| Err : Multiple Definition of onCreate() method from files")
        return None
    
    return result[0]
    
def Analyze(folderName) :
    print("Analyze [%s] ..." %folderName)

    while True :
        maniPath = FindManifest(folderName)
        if maniPath == None or len(maniPath) == 0 :
            break
        mainAct = FindMainAct(folderName, maniPath)
        if mainAct == None :
            break
        smaliList = FindSmali(folderName, mainAct)
        if smaliList == None or len(smaliList) == 0 :
            break
        entrySmali = FindEntrySmali(smaliList, mainAct)  
        print(entrySmali)
            
        break
    
    print("Analyze end")
    return

def main() :
    usage = "Usage: %prog [target APK folder]"
   
    if len(sys.argv) != 2 :
        print(usage)
        sys.exit()
    folderName = sys.argv[1]
       
    if not os.path.isdir(folderName) :
        print("Error : Wrong folder name | " + usage)
        sys.exit()
        
    Analyze(folderName)
        
if __name__  == "__main__" :
    main()