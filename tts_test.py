from gtts import gTTS
text = "错过你，尝尽酸甜都无味"
language = 'zh-CN'
tts = gTTS(text=text, lang=language)
tts.save('C:\\Users\\Eleve\\Downloads\\Language app\\uploads\\test3_tts.mp3')