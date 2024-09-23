import deertick
from datetime import datetime

x = ''
ai1 = deertick.Agent('Google: Gemini Flash 1.5 Experimental')
ai2 = deertick.Agent('Dolphin 2.9.2 Mixtral 8x22B')
ai3 = deertick.Agent('405b-base')
ai1.system_prompt = 'write a chorus to a song based on the word in the user prompt'
ai2.system_prompt = 'finish the song based on the chorus you are given'
ai2.max_tokens = 2000
while True:
    if x.lower() == 'q':
        break

    ai3.poke('give me a single word based on your feelings')
    # sigh classic base model shit
    ai1.poke(ai3.content)
    # yikes okay
    ai2.poke(ai1.content)
    print(f'{ai2.content}\n\n')
    x = input('Any key to run again s to save q to quit')
    if x.lower() == 's':
        current_t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'song_{current_t}.txt', 'w') as f:
            f.write(ai2.content)