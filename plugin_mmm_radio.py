import os
import time


from vacore import VACore
# from python_mpv_jsonipc import MPV

import mpv
player = mpv.MPV()
lastRadioVolumeChange = 15
modname = os.path.basename(__file__)[:-3] # calculating modname

TimerSleep = False

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "MMM_Radio", # имя
        "version": "1.0", # версия
        "require_online": True, # требует ли онлайн?
        "default_options": {
            "radioStations": [
                "http://nashe2.hostingradio.ru/nashe-128.mp3",
                "http://nashe1.hostingradio.ru/nashesongs.mp3",
                "https://orfeyfm.hostingradio.ru:8034/orfeyfm192.mp3",
            ],
            "radioPlay": 0,
            "radioVolume": 100,
            "TimeSleep": 1800,  # по команде "Спать": через сколько секунд выключить радио.
            "TimesToReduce": 2, # по команде "Спать": во сколько раз уменьшить громкость, 1 - не уменьшать. 
        },

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "радио|включи радио": RadioPlay, # "радио тихо|включи радио тихо": включает радио, а если уже включено не сообщает об этом 
            "поменяй радио|другое радио|смени радио": RadioChange,
            "тихо|выключи радио": RadioStop,
            "пауза|паузу": RadioPause,
            "тише": (RadioVolumeChange, -15),
            "громче": (RadioVolumeChange, 15),
            "чуть тише": (RadioVolumeChange, -5),
            "чуть громче": (RadioVolumeChange, 5),
            "сильно тише": (RadioVolumeChange, -35),
            "сильно громче": (RadioVolumeChange, 35),
            "потом выключи|спать": (RadioTimerSleep),
         }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass
    
def RadioPlay(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    options = core.plugin_options(modname)
    global player
    if player.filename:
        if phrase!='тихо': core.play_voice_assistant_speech("уже запущено")
        player.pause = False
    else:
        # core.play_voice_assistant_speech("включаю")
        # player.volume = options["radioVolume"]
        player.volume = 0
        player.play(options["radioStations"][options["radioPlay"]])
        while player.volume <= options["radioVolume"]:
            player.volume +=1
            time.sleep(0.1)

    # ----------- set context ------
    core.context_set(RadioContext)
 
def RadioChange(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    global player
    if not player.filename:
        core.play_voice_assistant_speech("радио не включено")
        return
    options = core.plugin_options(modname)
    player.stop()
    options["radioPlay"] = (options["radioPlay"] + 1) % len(options["radioStations"])
    core.save_plugin_options(modname,options)
    player.play(options["radioStations"][options["radioPlay"]])

    # ----------- set context ------
    core.context_set(RadioContext)

def RadioContext(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    # выходим из контекста
    if phrase in ("хорошо", "оставь", "стать", "оставить"):
        #core.context_clear_play()
        core.context_clear()
        return
        
    # команды в контексте модуля радио
    if phrase in ("другое", "поменяй"): RadioChange(core, phrase)
    elif phrase=="пауза": RadioPause(core, phrase)
    elif phrase=="выключи": RadioStop(core, phrase)
    
    elif phrase=="тише": RadioVolumeChange(core, phrase, -15)
    elif phrase=="громче": RadioVolumeChange(core, phrase, 15)
    elif phrase=="чуть тише": RadioVolumeChange(core, phrase, -5)
    elif phrase=="чуть громче": RadioVolumeChange(core, phrase, 5)
    elif phrase=="сильно тише": RadioVolumeChange(core, phrase, -35)
    elif phrase=="сильно громче": RadioVolumeChange(core, phrase, 35)
    elif phrase in ("потом выключи", "спать"): RadioTimerSleep(core, phrase)
    elif phrase=="ещё": 
        #core.accept() 
        global lastRadioVolumeChange
        RadioVolumeChange(core, phrase, lastRadioVolumeChange)
   
    else: core.play_voice_assistant_speech("не разобрал. Что сделать с рАдио?")

    # ----------- set context ------
    core.context_set(RadioContext)

def RadioStop(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
    global player
    global TimerSleep
    
    if TimerSleep:
        while player.volume > 1:
            player.volume -=1
            time.sleep(0.1)

    if player.filename:
        player.stop()
        if not TimerSleep: core.context_clear_play()
        # core.context_clear()
    else:
        if not TimerSleep: core.play_voice_assistant_speech("было выключено")

    # ----------- clear context ------
    core.context_clear()
    if TimerSleep: TimerSleep=False
        
def RadioPause(core:VACore, phrase: str):
    global player
    player.pause = not player.pause

    # ----------- set context ------
    core.context_set(RadioContext)
    
def RadioVolumeChange(core:VACore, phrase: str, level:int):
    global player
    global lastRadioVolumeChange
    lastRadioVolumeChange = level
    new_volume = player.volume + level
    if new_volume < 0:
        player.volume = 1
    elif new_volume > 100:
        player.volume = 100
    else:
        player.volume = new_volume
        
    # ----------- saving level in settings ------
    options = core.plugin_options(modname)
    options["radioVolume"]=player.volume
    core.save_plugin_options(modname,options)
    
    # ----------- set context ------
    core.context_set(RadioContext)
    
def RadioTimerSleep(core:VACore, phrase: str):
    # print("Выключить радио через options["TimeSleep"] секунд")
    global player
    global TimerSleep
    options = core.plugin_options(modname)
    TimerSleep = True
    # print("Уменьшаем громкость в options["TimesToReduce"] раз")
    player.volume = player.volume//options["TimesToReduce"]
    core.play_voice_assistant_speech("выключу радио попозже")
    core.set_timer(options["TimeSleep"],(RadioStop, phrase))

    
