from requests import post, get
from time import time, sleep
from concurrent.futures import ThreadPoolExecutor
from colorama import init
from threading import Thread, Event
import websocket
import base64
import random
import string
import ctypes
import json
import os

MAX_TASKS = 200;
MAX_THREADS = 50

running = True

class colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
class setInterval :
    def __init__(self,interval,action):
        self.startTime=time()
        self.interval=interval
        self.action=action
        self.stopEvent=Event()
        thread=Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime=time()+self.interval
        while not self.stopEvent.wait(nextTime-time()):
            nextTime+=self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()

GAP = " " * 8

def red(text):
    os.system("")
    faded = ""
    for line in text.splitlines():
        green = 250
        for character in line:
            green -= 5
            if green < 0:
                green = 0
            faded += (f"\033[38;2;255;{green};0m{character}\033[0m")
        faded += "\n"
    return GAP + faded

def blue(text):
    os.system("")
    faded = ""
    for line in text.splitlines():
        green = 0
        for character in line:
            green += 3
            if green > 255:
                green = 255
            faded += (f"\033[38;2;0;{green};255m{character}\033[0m")
        faded += "\n"
    return GAP + faded

def water(text):
    os.system("")
    faded = ""
    green = 10
    for line in text.splitlines():
        faded += (f"\033[38;2;0;{green};255m{line}\033[0m\n")
        if not green == 255:
            green += 15
            if green > 255:
                green = 255
    return faded

def purple(text):
    os.system("")
    faded = ""
    down = False

    for line in text.splitlines():
        red = 40
        for character in line:
            if down:
                red -= 3
            else:
                red += 3
            if red > 254:
                red = 255
                down = True
            elif red < 1:
                red = 30
                down = False
            faded += (f"\033[38;2;{red};0;220m{character}\033[0m")
    return GAP + faded

ascii_art = f"""


                        /$$      /$$ /$$      /$$  /$$$$$$        /$$$$$$$   /$$$$$$  /$$$$$$$$
                        | $$  /$ | $$| $$  /$ | $$ /$$__  $$      | $$__  $$ /$$__  $$|__  $$__/
                        | $$ /$$$| $$| $$ /$$$| $$| $$  \ $$      | $$  \ $$| $$  \ $$   | $$   
                        | $$/$$ $$ $$| $$/$$ $$ $$| $$  | $$      | $$$$$$$ | $$  | $$   | $$   
                        | $$$$_  $$$$| $$$$_  $$$$| $$  | $$      | $$__  $$| $$  | $$   | $$   
                        | $$$/ \  $$$| $$$/ \  $$$| $$  | $$      | $$  \ $$| $$  | $$   | $$   
                        | $$/   \  $$| $$/   \  $$|  $$$$$$/      | $$$$$$$/|  $$$$$$/   | $$   
                        |__/     \__/|__/     \__/ \______/       |_______/  \______/    |__/   
                        
                        
                        
                        {purple("[>] Open source at github.com/epsilonr/wworaidbot")}
                        
                        
"""

def read_file(path: str):
    
    try:
        f = open(path, "r")
        data = f.read()
        f.close()
        
        if data:
            return data
        else:
            raise Exception()
    except:
        pass

    return None

def generate_id(length: int = 16):
    return ''.join(random.choice(string.digits) for _ in range(length))

def generate_key():
    p = bytearray(random.getrandbits(8) for _ in range(16))
    return base64.b64encode(bytes(p)).decode('utf-8')

def qev(b: bool):
    if b:
        return " (has password)"
    else:
        return ""

def get_games(firebase_token: str, lang: str = "tr"):
    
    proxy = {
    "http": "http://66.33.210.189:17567",
    "https": "http://66.33.210.189:17567"
    }
    
    # custom?lang={lang}
    res = get(url=f"https://api-game.wolvesville.com/api/public/game/custom", headers={
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {firebase_token}"
    })

    open_games = res.json()["openGames"]

    buffer = []
    
    print(purple("~ Active Games:") + "\n")
    
    i = 0
    for game in open_games:
        if(not game['hostName']):
            continue

        i += 1
        print(red(f"    [{i}] => {game['hostName']} => {game['name']}{qev(game['hasPassword'])} [{game['playerCount']} Player(s)]"))
        buffer.append([game['gameId'], game['hasPassword']])
    
    return buffer

def get_token(t: str, v: str):

    try:
        res = post("https://api-auth.wolvesville.com/players/signInWithEmailAndPassword", json={"email": t, "password": v})
    
        if (res.status_code == 200):            
            return res.json()["idToken"]
        else:
            if (res.json()["message"] == "auth/too-many-requests"):
                print(red("[>] You probably got IP banned, no worries this ban is temporary."))
            else:
                print(red("[>] Wrong username or password."))
                print(red("[>] Terminating..."))
            sleep(3)
            exit()

    except Exception as e:
        print(red("[>] An error occured, terminating..."))
        sleep(3)
        exit()

def create_client(firebase_token: str, game_id: str, password: str = "undefined", task: int = 1):

    
    def on_message(ws, message):
        
        # CHECK
        if (not running):
            ws.close()
            return
        
        # SIMULATE HEARTBEAT   
        if (message == "2"):
            ws.send("3")
            ws.send('42["player-heartbeat"]')

        if "lobby:chat-msg" in message:
            if ("!test") in message:                
                try:
                    json_msg = json.dumps({"msg": f"Message ID: {generate_id(length=16)}"})
                    escaped_json_msg = json_msg.replace('"', '\\"')
                                        
                    ws.send('42["lobby:chat-msg","' + escaped_json_msg + '"]')      
                except Exception as e:
                    print(e)
                    
            # if ("!baslat") in message:           
            #     try:
            #         ws.send('42["host-start-game"]')      
            #     except Exception as e:
            #         print(e)

            if not "Message ID" in message:
                try:
                    json_msg = json.dumps({"msg": f"https://github.com/epsilonr/wwobot Dump: {generate_id()}"})
                    escaped_json_msg = json_msg.replace('"', '\\"')
                                        
                    ws.send('42["lobby:chat-msg","' + escaped_json_msg + '"]')      
                except Exception as e:
                    print(e)
                
                # try:
                #     # json_msg = json.dumps({"playerId": "ee456ee4-3988-47ec-ba97-e226422cfdb7"})
                #     # escaped_json_msg = json_msg.replace('"', '\\"')

                #     ws.send('3')       
                #     ws.send('42["host-start-game"]')
                # except Exception as e:
                #     print(e)

        sleep(0.1)

    def on_error(ws, error):
        print(f"Error: {error}")

    def on_open(ws):
        print(red(f"\nThread ({task}): Connected to the game!\n"))
        ws.send("40")
            
    ws_header = {
        "Pragma": "no-cache",
        "Origin": "https://www.wolvesville.com",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.3",
        "Upgrade": "websocket",
        "Cache-Control": "no-cache",
        "Connection": "Upgrade",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Sec-WebSocket-Key": generate_key(),
        "Sec-WebSocket-Version": "13",
    }
    
    try:
        ws = websocket.WebSocketApp(f"wss://api-game.wolvesville.com/socket.io/?firebaseToken={firebase_token}&gameId={game_id}&gameMode=custom&password={password}&ids=1&EIO=4&transport=websocket", header=ws_header, on_message=on_message, on_error=on_error)
        ws.on_open=on_open
        ws.run_forever()
    except Exception as e:
        print(e)
    
def inter_check():
    if running:
        print("*")
    
if __name__ == "__main__":
    init()
    
    ctypes.windll.kernel32.SetConsoleTitleW("~ github.com/epsilonr/wwobot")

    #! Constants from WINAPI
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    LWA_ALPHA = 0x2

    GWL_STYLE = -16
    WS_THICKFRAME = 0x00040000
    WS_MAXIMIZEBOX = 0x00010000

    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    
    window_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    window_style = window_style & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, window_style)

    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 240, LWA_ALPHA)
    
    ctypes.windll.user32.ShowWindow(hwnd, 1)
    ctypes.windll.user32.UpdateWindow(hwnd)
    
    os.system("cls")
    
    print(water(ascii_art))
    
    firebase_token = read_file("token.txt")

    try:
        buffer = get_games(firebase_token=firebase_token, lang="")
        
        if len(buffer) <= 0:
            print(red(f"[>] There is no active game."))
            print(red(f"[>] Terminating..."))
            sleep(3)
            exit()
    except:
        print(red("[>] Token is invalid.\n"))
        print(red("[>] Enter your credentials.\n"))
        
        email = input(purple(f"[~] Email => ") + colors.CYAN)
        password = input(purple(f"[~] Password => ") + colors.CYAN)
        
        token = get_token(email, password)
        
        if not token:
            sleep(3)
            print(red("[>] Token is invalid."))
            print(red("[>] Try again later."))
            exit()
        
        with open("token.txt", "w") as f:
            f.write(token)
        
        firebase_token = token
        
        buffer = get_games(firebase_token=firebase_token, lang="")
        
        if len(buffer) <= 0:
            print(red(f"[>] There is no active game."))
            print(red(f"[>] Terminating..."))
            sleep(3)
            exit()

    password = "undefined"
    
    while True:
        try:
            ind = int(input(purple("[~] Which game do you want to select? ") + colors.RED)) - 1
            if (ind <= -1 or ind > len(buffer) - 1):
                print(red(f"[>] You must select a number between 1 - {len(buffer)}."))
                continue
        except:
            print(red(f"[>] You must select a number between 1 - {len(buffer)}."))
            continue

        if(buffer[ind][1]):
            password = input(blue("[>] This room has password, enter password: "))

        break

    inter = setInterval(1, inter_check)
    inter.cancel()

    tasks = [item for item in range(MAX_TASKS)]
    
    pool = ThreadPoolExecutor(max_workers=MAX_THREADS)
    
    for task in tasks:
        if(running):
            pool.submit(create_client, firebase_token, buffer[ind][0], password, task)
        
    #! DEBUG pool.shutdown()
    
    #! create_client(firebase_token=FIREBASE_TOKEN, game_id=buffer[ind][0], password=password)
