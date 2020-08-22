import time, datetime, os, sys, requests, configparser, re, subprocess
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    slash = "\\"
else:
    slash = "/"

from queue import Queue
from streamlink import Streamlink
from threading import Thread

# Socket连接超时20秒，自动断开。
import socket
socket.setdefaulttimeout(20)

# 分析配置文件
Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")

# 获得视频保存目录
save_directory = Config.get('paths', 'save_directory')

# 获得模特列表
wishlist = Config.get('paths', 'wishlist')

# 获得间隔时间
interval = int(Config.get('settings', 'checkInterval'))

# 获得性别数组
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")

# 获得目录结构
directory_structure = Config.get('paths', 'directory_structure').lower()

# 获得当前时间函数
def now():
    return '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ']'

recording = []
wanted = []

# 开始记录函数
def startRecording(model):
    # 处理队列
    global processingQueue
    try:
        result = requests.get('https://chaturbate.com/api/chatvideocontext/{}/'.format(model)).json()
        session = Streamlink()
        session.set_option('http-headers', "referer=https://www.chaturbate.com/{}".format(model))
        streams = session.streams("hlsvariant://{}".format(result['hls_source'].rsplit('?')[0]))
        stream = streams["best"]
        fd = stream.open()
        now = datetime.datetime.now()
        filePath = directory_structure.format(path=save_directory, model=model,
                                              gender=result['broadcaster_gender'],
                                              seconds=now.strftime("%S"),
                                              minutes=now.strftime("%M"), hour=now.strftime("%H"),
                                              day=now.strftime("%d"),
                                              month=now.strftime("%m"), year=now.strftime("%Y"))
        directory = filePath.rsplit(slash, 1)[0]+slash
        if not os.path.exists(directory):
            os.makedirs(directory)
        if model in recording: return
        with open(filePath, 'wb') as f:
            recording.append(model)
            while model in wanted:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    f.close()
                    break

    except: 
        pass
    finally:
        if model in recording:
            recording.remove(model)

# 获得在线模特列表
def getOnlineModels():
    online = []
    global wanted
    s = requests.session()
    for gender in genders:
        try:
            data = {'categories': gender, 'num': 127}
            # 修复BUG，为每个请求设置超时，避免卡死。
            result = requests.post("https://roomlister.stream.highwebmedia.com/session/start/", data=data, timeout=20).json()
            length = len(result['rooms'])
            online.extend([m['username'].lower() for m in result['rooms']])
            data['key'] = result['key']
            while length == 127:
                result = requests.post("https://roomlister.stream.highwebmedia.com/session/next/", data=data, timeout=20).json()
                length = len(result['rooms'])
                data['key'] = result['key']
                online.extend([m['username'].lower() for m in result['rooms']])
        except:
            pass
    f = open(wishlist, 'r')
    wanted =  list(set(f.readlines()))
    wanted = [m.strip('\n').split('chaturbate.com/')[-1].lower().strip().replace('/', '') for m in wanted]
    #wantedModels = list(set(wanted).intersection(online).difference(recording))
    '''new method for building list - testing issue #19 yet again'''
    wantedModels = [m for m in (list(set(wanted))) if m in online and m not in recording]
    ''' test a_meow Model Start '''
    #thread = Thread(target=startRecording, args=('a_meow',))
    #thread.start()
    ''' test a_meow Model End '''
    for theModel in wantedModels:
        thread = Thread(target=startRecording, args=(theModel,))
        thread.start()
    f.close()

# 主函数
if __name__ == '__main__':
    s = requests.session()
    result = s.get('https://chaturbate.com/')

    AllowedGenders = ['female', 'male', 'trans', 'couple']
    for gender in genders:
        if gender.lower() not in AllowedGenders:
            print(gender, "is not an acceptable gender. Options are as follows: female, male, trans, and couple.")
            print("Please correct your config file.")
            exit()
    genders = [a.lower()[0] for a in genders]
    print()

    sys.stdout.write("\033[F")
    while True:
        sys.stdout.write("\033[K")
        print( now(),"{} model(s) are being recorded. Getting list of online models now".format(len(recording)))
        sys.stdout.write("\033[K")
        print("The following models are being recorded: {}".format(recording), end="\r")
        getOnlineModels()
        sys.stdout.write("\033[F")
        for i in range(interval, 0, -1):
            sys.stdout.write("\033[K")
            print(now(), "{} model(s) are being recorded. Next check in {} seconds".format(len(recording), i))
            sys.stdout.write("\033[K")
            print("The following models are being recorded: {}".format(recording), end="\r")
            time.sleep(1)
            sys.stdout.write("\033[F")
