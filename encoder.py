# encoder.py
# this file is part of usbrubberduckyencoder-python
#
# converts DuckyScript into usable hexfiles
#
# written by and copyright (C) Erica Garcia [athenaorerica] <me@athenas.space> 2019
# licensed under the MIT license <http://mit.athenas.space>

import sys, os, argparse
layoutProps = {}
keyboardProps = {}

version = "0.2.1"
debug = False

def main(args):
    global debug
    debug = args.debug
    if debug: print(args)
    inputfile = args.inputfile
    outputfile = args.outputfile
    layoutfile = args.layoutfile
    scriptStr = ""
    if ".rtf" in inputfile.name:
        print("rtfs aren't supported yet. why are you using RTF anyway?")
        raise NotImplementedError
    else:
        try:
            print("Loading DuckyScript...",end="",flush=True)
            scriptStr = inputfile.read()
            print("\t[ OK ]")
            inputfile.close()
            if debug: print(scriptStr)
        except:
            print("\t[ FAIL ]")
            raise
    loadProperties(layoutfile)
    print("Encoding...\t", end="",flush=True)
    encodeToFile(scriptStr, (outputfile))

def loadProperties(lang):
    try:
        print("Loading keyboard...",end="",flush=True)
        with open(os.path.dirname(os.path.abspath(__file__)) + "/resources/keyboard.properties", 'r') as file:
            for line in file:
                strStrp = line.strip()
                if strStrp.startswith("//"): continue
                if strStrp == "": continue
                lsplTmp = strStrp.split("=")
                lspl = []
                for ls in lsplTmp:
                    lspl.append(ls.strip())
                keyboardProps.update({lspl[0]: lspl[1]})
            print("\t[ OK ]")
        if len(keyboardProps) == 0: raise Exception("keyprops empty")
    except:
        print("\t[ FAIL ]")
        raise
    try:
        print("Loading language...", end="",flush=True)
        with open(os.path.dirname(os.path.abspath(__file__)) + "/resources/{0}.properties".format(lang), 'r') as file:
            for line in file:
                if line.startswith("//"): continue
                strStrp = line.strip()
                if strStrp == "": continue
                lsplTmp = strStrp.split("=")
                lspl = []
                for ls in lsplTmp:
                    lspl.append(ls.strip())
                layoutProps.update({lspl[0]: lspl[1]})
            print("\t[ OK ]")
        if len(layoutProps) == 0: raise Exception("langfile empty")
    except:
        print("\t[ FAIL ]")
        raise

def strInstrToByte(instruction): #must return byte
    instruction = instruction.strip()
    if "KEY_{0}".format(instruction) in keyboardProps:
        newB = strToByte(keyboardProps["KEY_{0}".format(instruction)])
    elif instruction == "ESCAPE":
        newB = strInstrToByte("ESC")
    elif instruction == "DEL":
        newB = strInstrToByte("DELETE")
    elif instruction == "BREAK":
        newB = strInstrToByte("PAUSE")
    elif instruction == "CONTROL":
        newB = strInstrToByte("CTRL")
    elif instruction == "DOWNARROW":
        newB = strInstrToByte("DOWN")
    elif instruction == "UPARROW":
        newB = strInstrToByte("UP")
    elif instruction == "LEFTARROW":
        newB = strInstrToByte("LEFT")
    elif instruction == "RIGHTARROW":
        newB = strInstrToByte("RIGHT")
    elif instruction == "MENU":
        newB = strInstrToByte("APP")
    elif instruction == "WINDOWS":
        newB = strInstrToByte("GUI")
    elif instruction == "PLAY" or instruction == "PAUSE":
        newB = strInstrToByte("MEDIA_PLAY_PAUSE")
    elif instruction == "STOP":
        newB = strInstrToByte("MEDIA_STOP")
    elif instruction == "MUTE":
        newB = strInstrToByte("MEDIA_MUTE")
    elif instruction == "VOLUMEUP":
        newB = strInstrToByte("MEDIA_VOLUME_INC")
    elif instruction == "VOLUMEDOWN":
        newB = strInstrToByte("MEDIA_VOLUME_DEC")
    elif instruction == "SCROLLLOCK":
        newB = strInstrToByte("SCROLL_LOCK")
    elif instruction == "NUMLOCK":
        newB = strInstrToByte("NUM_LOCK")
    elif instruction == "CAPSLOCK":
        newB = strInstrToByte("CAPS_LOCK")
    else:
        newB = int_to_bytes(charToBytes(instruction[0])[0])
    return newB

def addBytes(file, byteTab):
    for i in range(0, len(byteTab)):
        file += byteTab[i].to_bytes(1,'big')
    if (len(byteTab) % 2) != 0:
        file += b'\x00'
    return file

def int_to_bytes(x): #must return byte
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def int_from_bytes(xbytes): #must return int
    return int.from_bytes(xbytes, 'big')

def strToByte(st): #must return byte
    return int_to_bytes(int(st,0))

def codeToBytes(st): #must return byte or bytearray
    if st in layoutProps:
        keys = layoutProps[st].split(",")
        byteTab = b''
        j = 0
        while j < len(keys):
            key = keys[j].strip()
            if key in keyboardProps:
                b = strToByte(keyboardProps[key].strip())
                byteTab += b
            elif key in layoutProps:
                b = strToByte(layoutProps[key].strip())
                byteTab += b
            else:
                print("Key not found: {0}".format(key))
                byteTab += b'\x00'
            j += 1
        return byteTab
    else:
        print("Char not found: {0}".format(st))
        byteTab = b'\x00'
        return byteTab

def charToCode(c): #must return str
    code = ""
    c = ord(c)
    ch = "{:02x}".format(c).upper()
    if c < 128:
        code = "ASCII_{0}".format(ch)
    elif c < 256:
        code = "ISO_8859_1_{0}".format(ch)
    else:
        code = "UNICODE_{0}".format(ch)
    return code

def charToBytes(c): #must return byte
    return codeToBytes(charToCode(c))

def encodeToFile(inStr, fileDest):
    inStr = inStr.replace('\r','')
    instructions = inStr.split('\n')
    last_instruction = instructions
    file = b''
    defaultDelay = 0
    loop = 0
    for i in range(0, len(instructions)):
        try:
            delayOverride = False
            if instructions[i].strip().startswith("//") or instructions[i].strip().startswith("#") or instructions[i] == "\n" or instructions[i] == "": continue # the line was a comment
            instruction = instructions[i].strip().split(" ", 1)
            if i > 0:
                last_instruction = instructions[i-1].split(" ", 1)
                last_instruction[0] = last_instruction[0].strip()
                if len(last_instruction) == 2:
                    last_instruction[1] = last_instruction[1].strip()
                
            else:
                last_instruction = instructions[i].split(" ", 1)
                last_instruction[0] = last_instruction[0].strip()
                if len(last_instruction) == 2:
                    last_instruction[1] = last_instruction[1].strip()
            instruction[0] = instruction[0].strip().upper()

            if len(instruction) == 2:
                instruction[1] = instruction[1].strip()

            if instruction[0] == "REM": continue # line is a comment
            if instruction[0] == "REPEAT":
                loop = int(instruction[1].strip())
            else:
                loop = 1
            while loop > 0:
                if debug: print(str(instruction))
                if instruction[0] == "DEFAULT_DELAY" or instruction[0] == "DEFAULTDELAY":
                    defaultDelay = int(instruction[1].strip())
                    delayOverride = True
                elif instruction[0] == "DELAY":
                    delay = int(instruction[1].strip())
                    while delay > 0:
                        file += b'\x00'
                        if delay > 255:
                            file += b'\xff'
                            delay -= 255
                        else:
                            file += delay.to_bytes(1,'big')
                            delay = 0
                    delayOverride = True
                elif instruction[0] == "STRING":
                    for i in range(0, len(instruction[1])): # can probably be simplified to "for i in instruction[1]"
                        file = addBytes(file, charToBytes(instruction[1][i]))
                elif instruction[0] == "STRING_DELAY":
                    twoOptions = instruction[1].split(" ", 1)
                    delayMillis = int(twoOptions[0].strip())
                    userText = twoOptions[1].strip()
                    if debug: print(delayMillis)
                    if debug: print(userText)
                    for i in range(0, len(userText)):
                        c = userText[i]
                        file = addBytes(file, charToBytes(c))
                        for i in range(0, (delayMillis // 255)):
                            file += b'\xff'
                        file += (delayMillis % 255).to_bytes(1,'big')
                elif instruction[0] == "CONTROL" or instruction[0] == "CTRL":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += strToByte(keyboardProps["MODIFIERKEY_CTRL"])
                    else:
                        file += strToByte(keyboardProps["KEY_LEFT_CTRL"])
                        file += b'\x00'
                elif instruction[0] == "ALT":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += strToByte(keyboardProps["MODIFIERKEY_ALT"])
                    else:
                        file += strToByte(keyboardProps["KEY_LEFT_ALT"])
                        file += b'\x00'
                elif instruction[0] == "SHIFT":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += strToByte(keyboardProps["MODIFIERKEY_SHIFT"])
                    else:
                        file += strToByte(keyboardProps["KEY_LEFT_SHIFT"])
                        file += b'\x00'
                elif instruction[0] == "CTRL-ALT":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += (strToByte(keyboardProps["MODIFIERKEY_CTRL"]) | strToByte(keyboardProps["MODIFIERKEY_ALT"]))
                    else:
                        continue
                elif instruction[0] == "CTRL-SHIFT":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += (strToByte(keyboardProps["MODIFIERKEY_CTRL"]) | strToByte(keyboardProps["MODIFIERKEY_SHIFT"]))
                    else:
                        continue
                elif instruction[0] == "COMMAND-OPTION":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += (strToByte(keyboardProps["MODIFIERKEY_KEY_LEFT_GUI"]) | strToByte(keyboardProps["MODIFIERKEY_ALT"]))
                    else:
                        continue
                elif instruction[0] == "ALT-SHIFT":
                    if len(instruction) != 1:
                        file += strInstrToByte(instruction[1])
                        file += (strToByte(keyboardProps["MODIFIERKEY_LEFT_ALT"]) | strToByte(keyboardProps["MODIFIERKEY_SHIFT"]))
                    else:
                        file += strToByte(keyboardProps["KEY_LEFT_ALT"])
                        file += (strToByte(keyboardProps["MODIFIERKEY_LEFT_ALT"]) | strToByte(keyboardProps["MODIFIERKEY_SHIFT"]))
                elif instruction[0] == "ALT-TAB":
                    if len(instruction) == 1:
                        file += strToByte(keyboardProps["KEY_TAB"])
                        file += strToByte(keyboardProps["MODIFIERKEY_LEFT_ALT"])
                    else:
                        pass #this was marked as do something in the original Ducky encoder
                elif instruction[0] == "REM":
                    delayOverride = True #no default delay for comments
                    continue
                elif instruction[0] == "WINDOWS" or instruction[0] == "GUI":
                    if len(instruction) == 1:
                        file += strToByte(keyboardProps["MODIFIERKEY_LEFT_GUI"])
                        file += b'\x00'
                    else:
                        file += strInstrToByte(instruction[1])
                        file += strToByte(keyboardProps["MODIFIERKEY_LEFT_GUI"])
                elif instruction[0] == "COMMAND":
                    if len(instruction) == 1:
                        file += strToByte(keyboardProps["KEY_COMMAND"])
                        file += b'\x00'
                    else:
                        file += strInstrToByte(instruction[1])
                        file += strToByte(keyboardProps["MODIFIERKEY_LEFT_GUI"])
                else:
                    tmpB = strInstrToByte(instruction[0])
                    file += tmpB
                    file += b'\x00'
                loop -= 1
            if (not delayOverride) and (defaultDelay > 0):
                delayCounter = defaultDelay
                while delayCounter > 0:
                    file += b'\x00'
                    if delayCounter > 255:
                        file += b'\xff'
                        delayCounter -= 255
                    else:
                        file += delayCounter.to_bytes(1, 'big')
                        delayCounter = 0
        except IndexError:
            pass
        except:
            print("Error on line {0}".format(int(i+1)))
            raise
    try:
        fileDest.write(file)
        fileDest.flush()
        fileDest.close()
        print("\t[ OK ]")
    except:
        print("Failed to write hex file!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rubber Ducky Encoder (Python rewrite) v{0}\n".format(version))
    parser.add_argument('inputfile', nargs='?', default=sys.stdin, metavar="INPUTFILE", type=argparse.FileType('r',encoding='utf-8'))
    parser.add_argument('-o', metavar="OUTFILE", type=argparse.FileType('wb'), default='inject.bin',dest='outputfile')
    parser.add_argument('-l', metavar="LAYOUTFILE", type=str, default='us', dest='layoutfile')
    parser.add_argument('-d', action='store_true', dest='debug', help="enables debug mode")
    main(parser.parse_args())
