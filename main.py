from requests import post, get
from time import time, sleep
from concurrent.futures import ThreadPoolExecutor
from colorama import init
from ctypes import windll
import websocket
import base64
import random
import string
import json

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
    
    # custom?lang={lang}
    res = get(url=f"https://api-game.wolvesville.com/api/public/game/custom", headers={
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {firebase_token}"
    })

    open_games = res.json()["openGames"]

    buffer = []
    
    print(colors.GREEN + "Active Games:\n" + colors.ENDC)
    
    i = 0
    for game in open_games:
        if(not game['hostName']):
            continue

        i += 1
        print( colors.GREEN + f"{i}. " + colors.ENDC + f"{game['hostName']} - {game['name']}{qev(game['hasPassword'])}, {game['playerCount']} player(s)")
        buffer.append([game['gameId'], game['hasPassword']])
    
    return buffer

def get_token(t: str, v: str):

    try:
        res = post("https://api-auth.wolvesville.com/players/signInWithEmailAndPassword", json={"email": t, "password": v})
    
        if (res.status_code == 200):            
            return res.json()["idToken"]
        else:
            if (res.json()["message"] == "auth/too-many-requests"):
                print("You probably got IP banned, no worries this ban is temporary.")
            sleep(3)
            exit()

    except Exception as e:
        print(e)
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
                    json_msg = json.dumps({"msg": f"Arc Dump: {generate_id()}"})
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
        print(f"\nThread ({task}): Connected to the game!\n")
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
    
if __name__ == "__main__":
    init()
    
    windll.kernel32.SetConsoleTitleW(f"WWO - Bot | Arc")
    
    firebase_token = read_file("token.txt")

    try:
        buffer = get_games(firebase_token=firebase_token, lang="")
        
        if len(buffer) <= 0:
            print(colors.RED + "There is no active game." + colors.ENDC)
            sleep(3)
            exit()
    except:
        print(colors.RED + "Token is invalid.\n" + colors.ENDC)
        print(colors.GREEN + "Enter your credentials:\n" + colors.ENDC)
        
        email = input(colors.GREEN + "Email: " + colors.ENDC)
        password = input(colors.GREEN + "Password: " + colors.ENDC)
        
        token = get_token(email, password)
        
        if not token:
            sleep(3)
            print(colors.RED + "Token is invalid!" + colors.ENDC)
            exit()
        
        with open("token.txt", "w") as f:
            f.write(token)
        
        firebase_token = token
        
        buffer = get_games(firebase_token=firebase_token, lang="")
        
        if len(buffer) <= 0:
            print(colors.RED + "There is no active game." + colors.ENDC)
            sleep(3)
            exit()

    password = "undefined"
    
    while True:
        try:
            ind = int(input("\nHangi oyunu seçmek istersin? ")) - 1
            if (ind <= -1 or ind > len(buffer) - 1):
                print(colors.RED + f"You must select a number between 1 and {len(buffer)}." + colors.ENDC)
                continue
        except:
            print(colors.RED + f"You must select a number between 1 and {len(buffer)}." + colors.ENDC)
            continue

        if(buffer[ind][1]):
            password = input("\nThis room has password, enter password: ")

        break

    tasks = [item for item in range(MAX_TASKS)]
    
    pool = ThreadPoolExecutor(max_workers=MAX_THREADS)
    
    for task in tasks:
        if(running):
            pool.submit(create_client, firebase_token, buffer[ind][0], password, task)
        
    pool.shutdown()
    
    # create_client(firebase_token=FIREBASE_TOKEN, game_id=buffer[ind][0], password=password)
