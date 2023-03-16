# Чтение RSS ленты
# author: mmm
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
            "delay": 4, # Пауза между новостями
            "RSSArticleTitle": "title",      # Тег в RSS - Название статьи
            "RSSArticleBody": "description", # Тег в RSS - Тело статьи
            
        },
        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "новости|новость": RSSStart,
         }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass
    
def RSSStart(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла, если юзер сказал больше в этом плагине не используется
    options = core.plugin_options(modname)
    global fp
    global fp_current_feed
    try:
        fp = feedparser.parse(options["RSSLink"])['entries']
    except Exception as e:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с получением новостей. Посмотрите логи")
        pass
    fp_current_feed = 0
    try:
        if isinstance(fp[fp_current_feed][options['RSSArticleTitle']], str):
            print(" RSS RSSArticleTitle - Ok")
        if isinstance(fp[fp_current_feed][options['RSSArticleBody']], str):
            print(" RSS RSSArticleBody - Ok")
    except Exception as e:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с парсером новостей. Посмотрите логи")
        pass
    core.play_voice_assistant_speech(fp[fp_current_feed][options['RSSArticleTitle']])
    # ----------- set context ------
    core.contextOnClearing=RSSNext
    core.context_set(RSSContext, options["delay"])


def RSSContext(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла, если юзер сказал больше в этом плагине не используется
    options = core.plugin_options(modname)
    core.context_clear()
    # выходим из контекста
    if phrase in ("хватит", "стоп", "тихо", "стой"):
        core.contextOnClearing=None
        core.context_clear_play()
        return
        
    # команды в контексте модуля радио
    if phrase in ("дальше", "далее", "ещё"): core.accept(); RSSNext(core, phrase)
    elif phrase in ("повтори", "ещё раз", "еще раз"): 
        core.accept(); 
        core.play_voice_assistant_speech(fp[fp_current_feed][options['RSSArticleTitle']])
    elif phrase in ("подробнее", "подробне", "раскрой"): 
        core.accept(); 
        core.play_voice_assistant_speech(fp[fp_current_feed][options['RSSArticleBody']])
    else: core.play_voice_assistant_speech("не понял. повтори?")

    # ----------- set context ------
    core.contextOnClearing=RSSNext
    core.context_set(RSSContext, options["delay"])

def RSSNext(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла, если юзер сказал больше в этом плагине не используется
    options = core.plugin_options(modname)
    # ----------- clear context ------
    core.context_clear()    
    
    global fp
    global fp_current_feed
    fp_current_feed += 1
    if fp_current_feed == len(fp):
        core.play_voice_assistant_speech('больше новостей нет')
        core.contextOnClearing=None
        core.context_clear_play()
        return
    core.play_voice_assistant_speech(fp[fp_current_feed][options['RSSArticleTitle']])
    # ----------- set context ------
    core.contextOnClearing=RSSNext
    core.context_set(RSSContext, options["delay"])
