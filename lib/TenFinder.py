import os
import sys
import re
import random
from elftools.elf.elffile import ELFFile

def FindTextSection(fileName, elf, targetSection=".text") :
    print("FindTextSection [%s]..." % fileName);
    print("| Finding [%s] Section..." % targetSection)
    sectionNum = elf.num_sections()
    print("| Number of Section %d" % sectionNum)
    target = None
    for i in range(sectionNum) :
        sect = elf.get_section(i)
        if sect.name == targetSection :
            print("| ... Find [%s] Section!" % targetSection)
            length = sect['sh_size']
            offset = sect['sh_offset']
            print("| ... Section offset 0x%x~0x%x (0x%x)" % (offset, (offset+length), length))
            return offset, length
    print("| ... Cannot find [%s] Section." % targetSection)
    return -1, -1
    
def FindPattern(fileName, offset, length, pattern = "00002041") :
    print("FindPattern [%s]..." % fileName);
    if len(pattern) % 2 == 1 : pattern = "0"+pattern
    patternArray = []
    
    filePointer = open(fileName, 'rb')
    data = filePointer.read()
    filePointer.close()
    codeSection = data[offset:(offset+length)]
    codeHexString = codeSection.hex()
    
    matches = re.finditer(pattern, codeHexString)
    indices = [match.start() for match in matches]
    
    if len(indices) == 0 :
        print("| No such pattern %s in %s  Code Section" % (pattern,fileName))
        return None
    else :
        print("| Find %d pattern(%s) in %s Code Section" % (len(indices),pattern,fileName))
        List = list(map(lambda x : int((x/2)+offset), indices))
        return List

def ChangePattern(fileName, targetList, modNum = 5, pattern = "0000a041") :
    print("ChangePattern [%s]..." % fileName);
    outName = "modified_"+fileName
    filePointer = open(fileName, 'rb')
    data = bytearray(filePointer.read())
    filePointer.close()
    
    if len(targetList) < 5 : modNum = len(targetList)
    
    offList = random.sample(targetList, modNum)
    print("| Prepare modification... Target number %d" % len(offList))
    subPattern = bytearray.fromhex(pattern)
    
    for off in offList :
        print("| ... Change [0x%x]\tOriginal : 0x%s\t- Modified : 0x%s" % (off,data[off:off+4].hex(),subPattern.hex()))
        data[off:off+4] = subPattern

    print("| ... Creating File %s" % outName)
    filePointer = open(outName, 'wb')
    filePointer.write(data)
    filePointer.close()
    return


def Analyze(fileName) :
    print("Analyze [%s]..." % fileName);
    
    filePointer = open(fileName, 'rb')   
    elf = ELFFile(filePointer);
   
    while True :
        codeOffset, length = FindTextSection(fileName, elf)
        if codeOffset < 0 or length <0 :
            break
        patternList = FindPattern(fileName, codeOffset, length)
        if patternList == None or len(patternList) == 0 :
            break
        ChangePattern(fileName, patternList)
        
        break
            
    print("Analyze end")
    filePointer.close()
    return
    

def main() :
    usage = "Usage: %prog [target ELF]"
   
    if len(sys.argv) != 2 :
        print(usage)
        sys.exit()
    fileName = sys.argv[1]
       
    if not os.path.isfile(fileName) :
        print("Error : Wrong file name | " + usage)
        sys.exit()
        

    Analyze(fileName)
    
    
if __name__  == "__main__" :
    main()