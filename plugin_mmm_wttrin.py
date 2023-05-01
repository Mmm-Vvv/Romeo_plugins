# Погода через wttr.in  
# coauthor: mmm

# TODO: (все настраивается тут, потом переделать)

from datetime import datetime
import requests
import os
from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname


# информация о плагине и начальные настройки
def start(core: VACore):
    manifest = {
        'name': 'MMM_Погода (wttr.in)',
        'version': '1.0',
        'require_online': True,
        
        "default_options": {
            'location': 'Moscow', ## местоположение
        },
        
        'commands': {
            'погода': get_weather,
            'полный прогноз погоды': get_weather_forecast,
            'прогноз погоды|какая погода': get_weather_short,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass
    
    
# вычисляет вариант текста для конкретного числительного из набора вариантов
def compute_suffix(value: str, variants: list):
    n = int(value.strip()[-1])
    if (n == 0) or (n >= 5):
        suffix = variants[0]
    elif (n == 1):
        suffix = variants[1]
        if len(value) >= 2:
            if value.strip()[-2] == '1':
                suffix = variants[2]
    else:
        suffix = variants[2]
    return suffix
    
    
# текст прогноза погоды на основании переданных данныхъ о температуре, влажности, давлении и скорости ветра 
def forecast_text(temp: str, humidity: str, pressure: str, wind_speed: str):
    text = 'Температура {0} {1}, Влажность {2} {3}, Давление - {4} {5} ртутного столба, Ветер {6} {7} в час.'.format(
            temp, compute_suffix(temp, ['градусов', 'градус', 'градуса']),
            humidity, compute_suffix(humidity, ['процентов', 'процент', 'процента']),
            pressure, compute_suffix(pressure, ['миллиметров', 'миллиметр', 'миллиметра']),
            wind_speed, compute_suffix(humidity, ['километров', 'километр', 'километра'])
            )
    return text
        
# запросить погоду для данного местоположения
def request_weather(core: VACore):
    options = core.plugin_options(modname)
    # print(f'Location={options["location"]}')
    url = 'https://wttr.in/{0}?Q?m&format=j1&lang=ru'.format(options["location"])
    req = requests.get(url)
    return req.json()

        
# сформировать описание погоды, на основании словаря JSON
def get_weather_text(data: dict):
    
    descr = data['lang_ru'][0]['value']
    
    humidity = data['humidity']
    pressure = round(int(data['pressure']) / 1.333)
    
    if 'temp_C' in data:
        temp = data['temp_C']
    else:
        temp = data['tempC']
        
    wind_speed = data['windspeedKmph']

    return descr + '. ' + forecast_text(temp, humidity, str(pressure), wind_speed)
    
# сформировать описание погоды, на основании словаря JSON =кратко
def get_weather_text_short(data: dict, full:bool = False):
    def temp2text(temp:int, full:bool = False):
        from utils.num_to_text_ru import num2text
        units = ((u'', u'', u''), 'm')
        if full: units = ((u'градус', u'градуса', u'градусов'), 'm')
        text = "плюс "
        if temp > 0: return "плюс " + num2text(temp,units)
        else: return num2text(temp,units)  
        
    descr = data['lang_ru'][0]['value']
    # print(descr)
    if 'temp_C' in data: temp = data['temp_C']
    else: temp = data['tempC']
    # print(temp)
    full_text = descr + '. ' + temp2text(int(temp), full)
    return full_text
    
        
# получить текст для описания даты прогноза
def get_date(data: str):
    day_list = ('первое', 'второе', 'третье', 'четвёртое','пятое', 'шестое', 'седьмое', 'восьмое','девятое', 'десятое', 'одиннадцатое', 'двенадцатое','тринадцатое', 'четырнадцатое', 'пятнадцатое', 'шестнадцатое','семнадцатое', 'восемнадцатое', 'девятнадцатое', 'двадцатое','двадцать первое', 'двадцать второе', 'двадцать третье','двадцать четвёртое', 'двадцать пятое', 'двадцать шестое','двадцать седьмое', 'двадцать восьмое', 'двадцать девятое','тридцатое', 'тридцать первое')
    weekday_list = ('понедельник','вторник','среду','четверг','пятницу','субботу','воскресенье')
    month_list = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня','июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')
    
    d = datetime.strptime(data, '%Y-%m-%d')
    day = day_list[d.day - 1]
    weekday = weekday_list[d.weekday()]
    month = month_list[d.month - 1]
    #year = d.year
    
    #text = 'Прогноз на ' + weekday + ' с датой' +  day + ' ' + month + ' ' + str(year) + ' года.'
    text = 'Прогноз на ' + weekday + ' с датой' +  day + ' ' + month + ' '
    return text
    
# текущая погода
def get_weather(core: VACore, phrase: str):
    # options = core.plugin_options(modname)
    try:
        core.play_voice_assistant_speech('Текущая погодная сводка')
        weathers = request_weather(core) 
        text = get_weather_text(weathers['current_condition'][0])
        core.play_voice_assistant_speech(text)
        return
    except Exception as e:
        pass
        
# прогноз погоды на три дня 
def get_weather_forecast(core: VACore, phrase: str):
    # options = core.plugin_options(modname)
    
    # произнести прогноз на определенное время суток
    def say_hourly_weather(daytime: str, hourly: dict):
        core.play_voice_assistant_speech(daytime);
        text = get_weather_text(hourly)
        core.play_voice_assistant_speech(text)
        
        
    try:
        core.play_voice_assistant_speech('Прогноз погоды на три дня')
        
        weathers = request_weather(core)['weather'] # город или координаты
        
        for weather in weathers:
            # дата на которую прогноз
            d = weather['date']
            
            # произнести дату
            core.play_voice_assistant_speech(get_date(d))
            
            # произнести утренний прогноз
            say_hourly_weather("Утро", weather['hourly'][2])
            
            # произнести дневной прогноз
            say_hourly_weather("День", weather['hourly'][4])
            
            # произнести вечернний прогноз
            say_hourly_weather("Вечер", weather['hourly'][6])
        
        return
    except Exception as e:
        pass

#  погода сейчас, через шесть часов и завтра
def get_weather_short(core: VACore, phrase: str):
    # options = core.plugin_options(modname)
    # произнести прогноз на определенное время суток
    def say_hourly_weather_short(daytime: str, hourly: dict, full:bool = False):
        text = get_weather_text_short(hourly, full)
        core.play_voice_assistant_speech(daytime+" "+text)
        
    try:
        weathers = request_weather(core) # город или координаты
        say_hourly_weather_short("за окном - ", weathers['current_condition'][0], True)
        
        now = datetime.now()
        hours = int(now.strftime("%H")) 

        prognoz_date = (hours + 6) // 24
        prognoz_period = ((hours + 6) % 24 ) // 3
        
        # print("дата " + str(prognoz_date) + " период " + str(prognoz_period))
        say_hourly_weather_short("Через шесть часов - ", weathers['weather'][prognoz_date]['hourly'][prognoz_period])
        
        say_hourly_weather_short("Завтра днём", weathers['weather'][1]['hourly'][4])
        return
    except Exception as e:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с погодой. Посмотрите логи")
        pass
