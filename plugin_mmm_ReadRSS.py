# Рандом
# author: Vladislav Janvarev
import os
from vacore import VACore
modname = os.path.basename(__file__)[:-3] # calculating modname

import feedparser
fp = feedparser
fp_current_feed = 0

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "MMM_ReadRSS", # имя
        "version": "1.0", # версия
        "require_online": True, # требует ли онлайн?
        "default_options": {
            "RSSLink": 'http://lenta.ru/rss/last24',
            "delay": 3
        },
        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "новости|новость": RSSStart,
         }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass
    
def RSSStart(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    options = core.plugin_options(modname)
    
    global fp
    global fp_current_feed
    fp = feedparser.parse(options["RSSLink"])['entries']
    fp_current_feed = 0
    core.play_voice_assistant_speech(fp[fp_current_feed]['title'])

        # entry['summary']
    # ----------- set context ------
    core.context_set(RSSContext, options["delay"], RSSNext)


def RSSContext(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    core.context_clear()
    # выходим из контекста
    if phrase in ("хватит", "стоп", "тихо", "стой"):
        core.context_clear_play()
        return
        
    # команды в контексте модуля радио
    if phrase in ("дальше", "далее", "ещё"): core.accept(); RSSNext(core, phrase)
    elif phrase in ("повтори", "ещё раз", "еще раз"): 
        core.accept(); 
        core.play_voice_assistant_speech(fp[fp_current_feed]['title'])
    elif phrase in ("подробнее", "подробне", "раскрой"): 
        core.accept(); 
        core.play_voice_assistant_speech(fp[fp_current_feed]['summary'])
    else: core.play_voice_assistant_speech("не понял. повтори?")

    # ----------- set context ------
    options = core.plugin_options(modname)
    core.context_set(RSSContext, options["delay"], RSSNext)

def RSSNext(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
    # ----------- clear context ------
    core.context_clear()    
    
    global fp
    global fp_current_feed
    fp_current_feed += 1
    if fp_current_feed == len(fp):

        core.play_voice_assistant_speech('больше новостей нет')
        core.context_clear_play()
        return
    core.play_voice_assistant_speech(fp[fp_current_feed]['title'])
    # ----------- set context ------
    options = core.plugin_options(modname)
    core.context_set(RSSContext, options["delay"], RSSNext)
