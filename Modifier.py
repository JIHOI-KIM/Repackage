import os
import subprocess
import shutil
import time
import re

originPath = None
case1Path = None
case2Path = None
workbench = None

def checkLib() :
    print("Check required libraries...")
    here = os.getcwd()
    libdir = here+"\lib"
    if not os.path.isdir(libdir) :
        print("|... Cannot Find library directory [%s]" % libdir)
        return False
    
    Deps = []
    Deps.append("ModSmali.py")
    Deps.append("libdummy.so")
    Deps.append("TenFinder.py")
    
    for dep in Deps :
        path = libdir + "\\" + dep
        if not os.path.exists(path) :
            print("|... Cannot Find library [%s] in lib folder." % dep)
            return False
            
    return True
        
def checkFolder(inFolder, outFolder) :
    print("Check required Folders...")
    here = os.getcwd()
    inDir = here+"\\"+inFolder
    outDir = here+"\\"+outFolder
    
    if not os.path.isdir(inDir) :
        print("|... Cannot Find input APKs' Directory [%s]" % indir)
        return None
    if not os.path.isdir(outDir) :
        print("|... Cannot Find output APKs' Directory [%s]" % outdir)
        return None
   
    outList = os.listdir(outDir)
    if not len(outList) == 0 :
        print("|... Output Directory [%s] is not clean" % outDir)
        return None

    inList = os.listdir(inDir)
    if len(inList) == 0 :
        print("|... Nothing exist in Input Directory [%s]" %inDir)
        return None
        
    bench = here+"\workbench"
    if os.path.isdir(bench) :
        benchList = os.listdir(bench)
        if not len(benchList) == 0 :
            print("|... Workbench exist, but not clean. [%s]" %bench)
            return None
        else :
            print("|...Workbench already exist(empty). [%s] " %bench)
        
    else :
        os.mkdir(bench)
        print("|... Create Workbench directory [%s]" %bench)
  
    return bench
    
def checkTools() :
    print("Check required utilities ...")
    Tools = []
    Tools.append("apktool")
    Tools.append("apksigner")
    Tools.append("zipalign")
    
    for cmd in Tools :
        proc = subprocess.Popen(cmd, stdin = subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
        if(proc.poll() == None) :
            proc.communicate(b'\n')
        proc.wait()
        proc.terminate()
        
        if proc.returncode == 1 :
            print("|... Cannot find [%s] or Error on running ( return 1 )")
            return False
        else :
            print("|... Find [%s] !"%cmd)
        
    return True

def targetList (inFolder) :
    print("Listing Target Apks...")
    here = os.getcwd()
    targetsDir = here+"\\"+inFolder
    targets = os.listdir(targetsDir)
    
    for item in targets :
        if not item.endswith(".apk") :
            print("|... Non Application item in %s (%s)" % (inFolder, item))
            return None
    
    print("|... Find %d apk files" % len(targets))
    return targets

def Unpackage (targets, inFolder, workDir) :
    print("Unpackage %s Targets " %len(targets))
    indir = os.getcwd() +"\\" + inFolder +"\\"

    failed = []
    for apk in targets :
        outdir = workDir+"\\"+apk[:-4]
        infile = indir + apk
        print("|... Calling [apktool d] for [%s]" % apk)
        cmd = "apktool d "+infile+" -o "+outdir
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr = subprocess.DEVNULL, shell= True)
        proc.communicate(b"\n")
        proc.wait()
            
        if len(os.listdir(outdir)) == 0 :
            print("|... Cannot perfrom unpackaging on [%s]" % apk)
            failed.append(apk)
            os.rmdir(outdir)
        
        print("|... Unpackage for [%s] End" % apk)

    print("|... Removing Failed case (Return %d)" %len(failed))
    for fail in failed :
        print("|... Failed to Unpackage [%s]"% fail)
        targets.remove(fail)

    if len(targets) == 0:
        print("|... No target Lefts.")
        return None

    return targets
    
def ModSmali (targets, workDir) :
    print("Modify Smali files...")
    cmd_base = "Python3 lib\\ModSmali.py "
    work_base = workDir + "\\"
    fails = []

    for apk in targets :
    
        if apk.endswith("_sub.apk") :
            print("|... [%s] is treated as sub apk file." % apk)
            continue
            
        apkFolder = apk[:-4]
        print("----------------------")
        proc = subprocess.Popen(cmd_base+work_base+apkFolder)
        proc.wait()
        print("----------------------")
        
        if not (proc.returncode == 0) :
            print("| Cannot [ModSmali.py] %s"%apkFolder)
            fails.append(apk)
        else :
            print("| [ModSmali.py] %s Complete"%apkFolder)
            
    for fail in fails :
        targets.remove(fail)
    if len(targets) == 0 :
        print("| No target Lefts.")
        return None
      
    print("[ModSmali.py] %d files" % len(targets))
    return targets

def LibraryInjection (targets, workDir) :
    print("Inject Library to %d targets" % len(targets))
    
    injectLib = os.getcwd()+"\\lib\\libdummy.so"
    fails = []
    
    for target in targets :
    
        subApk = re.sub("\.apk","_sub\.apk", target)
        if subApk in targets :
            print("|... Target have sub apk [%s] - Skip Injection", subApk)
            continue
        
        targetDir = workDir+"\\"+target[:-4]
        
        if not "lib" in os.listdir(targetDir) :
            print("| Cannot Find \"lib\" folder in %s",target[:-4])
            fails.append(target)
            
        else :
            libDir = targetDir+"\\lib"
            arm7Dir = None
            if not os.path.isdir(libDir) :
                print("| Cannot Find \"lib\" folder in %s",target[:-4])
                fails.append(target)
            else : 
                if not "armeabi-v7a" in os.listdir(libDir) :
                    print("| Cannot Find \"armeabi-v7a\" in lib folder")
                    fails.append(target)
                else :
                    arm7Dir = libDir+"\\armeabi-v7a"
                    if not os.path.isdir(arm7Dir) :
                        print("| Cannot Find \"armeabi-v7a\" in lib folder")
                        arm7Dir = None
                        fails.append(target)
                        
            if not arm7Dir == None :
                try :
                    shutil.copy(injectLib, arm7Dir+"\\libdummy.so")
                    print("| Copy Dummy Library into [%s]" % arm7Dir)
                except Exception as e :
                    print("| Cannot Copy dummy library into [%s]" % arm7Dir)
                    fails.append(target)    
    return None


def main() :
    inFolder = "inApk"
    outFolder = "outApk" 

    while True :
        result = checkLib()
        if not result :
            break
        workDir = checkFolder(inFolder, outFolder)
        if workDir == None :
            break
        result = checkTools()
        if not result :
            break
        targets = targetList(inFolder)
        if targets == None :
            break
        targets = Unpackage(targets, inFolder, workDir)
        if targets == None or len(targets) == 0 :
            break
        targets = ModSmali(targets, workDir)
        if targets == None or len(targets) == 0 :
            break
        targets = LibraryInjection(targets, workDir)
        if targets == None or len(targets) == 0 :
            break
                 
        print("Job finished.") 
        return
    
    print("Job Terminated.")
    return
    
if __name__  == "__main__" :
    main()