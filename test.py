import time, datetime, os, sys, requests, configparser, re, subprocess, traceback
from queue import Queue
from streamlink import Streamlink
from threading import Thread

# 分析配置文件
Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")

# 获得配置文件的参数值
save_directory = Config.get('paths', 'save_directory')
wishlist = Config.get('paths', 'wishlist')
interval = int(Config.get('settings', 'checkInterval'))
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")
directory_structure = Config.get('paths', 'directory_structure').lower()

# 获得当前时间函数
def now():
    return '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ']'

recording = []
wanted = []

# 开始记录函数
def startRecording(model):
    # 处理队列
    #global processingQueue
#    try:
        result = requests.get('https://chaturbate.com/api/chatvideocontext/{}/'.format(model)).json()


        session = Streamlink()
        session.set_option('http-headers', "referer=https://www.chaturbate.com/{}".format(model))
        ts= "hlsvariant://{}".format(result['hls_source'].rsplit('?')[0])
        print(ts)
        streams = session.streams(ts)
        stream = streams["best"]
        fd = stream.open()

#        now = datetime.datetime.now()
#        filePath = directory_structure.format(path=save_directory, model=model,
#                                              gender=result['broadcaster_gender'],
#                                              seconds=now.strftime("%S"),
#                                              minutes=now.strftime("%M"), hour=now.strftime("%H"),
#                                              day=now.strftime("%d"),
#                                              month=now.strftime("%m"), year=now.strftime("%Y"))
#        directory = filePath.rsplit(slash, 1)[0]+slash
#        if not os.path.exists(directory):
#            os.makedirs(directory)
#        if model in recording: return
#        with open(filePath, 'wb') as f:
#            recording.append(model)
#            while model in wanted:
#                try:
#                    data = fd.read(1024)
#                    f.write(data)
#                except:
#                    f.close()
#                    break
#
#    except: 
#        pass
#    finally:
#        if model in recording:
#            recording.remove(model)

# 获得在线模特列表
def getOnlineModels():
    online = [] # 在线模特列表
    global wanted
    s = requests.session()

    for gender in genders:
        try:
            data = {'categories': gender, 'num': 127}
            result = requests.post("https://roomlister.stream.highwebmedia.com/session/start/", data=data, timeout=5).json()
            length = len(result['rooms'])
            online.extend([m['username'].lower() for m in result['rooms']])
            data['key'] = result['key']

            # 如果模特数量==127，取下一页
            while length == 127:
                result = requests.post("https://roomlister.stream.highwebmedia.com/session/next/", data=data, timeout=5).json()
                #print(result)
                length = len(result['rooms'])
                data['key'] = result['key']
                online.extend([m['username'].lower() for m in result['rooms']])
        except Exception as e:
            #print('except!!!')
            #print(e)
            #traceback.print_exc()
            # 为了防止post获得json有问题，终止，从而无法和获得其他性别的模特列表。
            # 所以将 break 换成 pass
            pass

    f = open(wishlist, 'r') # 打开模特列表
    wanted =  list(set(f.readlines())) # 按行读取
    wanted = [m.strip('\n').split('chaturbate.com/')[-1].lower().strip().replace('/', '') for m in wanted]
    wantedModels = [m for m in (list(set(wanted))) if m in online and m not in recording]
    for theModel in wantedModels:
        #print(theModel)
        startRecording(theModel)
#        thread = Thread(target=startRecording, args=(theModel,))
#        thread.start()
    f.close()

# 主函数
if __name__ == '__main__':
    #s = requests.session()
    #result = s.get('https://zh.chaturbate.com/')

    AllowedGenders = ['female', 'male', 'trans', 'couple']
    for gender in genders:
        if gender.lower() not in AllowedGenders:
            print(gender, "is not an acceptable gender. Options are as follows: female, male, trans, and couple.")
            print("Please correct your config file.")
            exit()
    genders = [a.lower()[0] for a in genders]

    getOnlineModels()



