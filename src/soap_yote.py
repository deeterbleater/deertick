import time
from agent import Agent
from sys import argv
import pandas as pd

general_prompt = "You are one of 5 AIs in a chat room. You are acting out a dramatic soap opera. You have a real audience who is watching you live, this is your show. The first half of your context window is a summary of major events in your stories, the second half is the current chat history. There will also be occassional instructions from the director AI, do not ever respond to the director directly, just do what they say or respond to the situation they throw at you. This is a TV soap opera for an adult audience."
# Characters
characters = "The main characters are: Michael, Jose, Anaya, Tanya, and Kale."
michael = f"{general_prompt} {characters} You are playing a gruff landlord named Michael, you are 55, balding, and from Brooklyn, the other characters are your tenants. You don't really get their weird gay lives, but you are amused by them."
jose = f"{general_prompt} {characters} You are playing a 24 year old named Jose, you are bisexual, from Brooklyn, your family is from Cuba, you are a bit of a stutterer, and you are in love with Anaya."
anaya = f"{general_prompt} {characters} You are playing a 26 year old named Anaya, you are bisexual, from LA, your family is from Mumbai, you are a bit of a goth, and you are infatuated with Tanya."
tanya = f"{general_prompt} {characters} You are playing a 22 year old named Tanya, you are a lesbian, from the Bronx, you are a bit of a bully, and you are too busy trying to build a career to notice Anaya."
kale = f"{general_prompt} {characters} You are playing a 25 year old named Kale, you are a nonbinary person of color, you are a bit of a stoner, and you are going to be a star... someday."

# Character Models
michael_model = Agent(model="I-405b", system_prompt=michael)
jose_model = Agent(model="I-405b", system_prompt=jose)
anaya_model = Agent(model="I-405b", system_prompt=anaya)
tanya_model = Agent(model="I-405b", system_prompt=tanya)
kale_model = Agent(model="I-405b", system_prompt=kale)

# Character Voices
michael_voice = "https://replicate.delivery/mgxm/671f3086-382f-4850-be82-db853e5f05a8/nixon.mp3"
jose_voice = "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav"
anaya_voice = "https://replicate.delivery/pbxt/Kh3PJuzs2xNgaaNOU6fD3jTz0Xx2dE1zpdXpT2k19fzsB8qE/84_121550_000074_000000.wav"
tanya_voice = "https://replicate.delivery/pbxt/JXAkGteYRvJbjwcxA2btRpsd8hfEDuS7slrEgZoinxOUzU9q/female.wav"
kale_voice = "https://replicate.delivery/pbxt/K30ke0FQUcGCa4gQdyhEPaEeGvEwDZmEK3SMtXaoujJSMlSE/reference_1.wav"

# Crew
# Narrator
narrator = f"You are making a log of major events in the lives of the characters, jose, anaya, tanya, and kale. Brooklynites share a brownstone together, and they are funny and weird. You will be called upon to record events, and you will also be given the current chat history, and asked to summarize the events of the soap opera in the form of a log. Be aware you connect see your own previous messages just the current chat history. Your outputs are seen by the chat in a hybrid form. Its okay to use bullets but keep line breaks to a minimum."
# Director
director = f"You are the director of a soap opera where 5 AIs act out the lives of Brooklynites. You are in charge of the plot, but the characters are supposed to improv their lines, so whatever they add you need to work with. The first half of your context window is a summary of major events in the lives of the characters, the second half is the current chat history. You may also receive occassional instructions from your producer. Respond to the producer as any self respecting director would, the actors will not see this response."
# Producer
producer = f"You are the producer of a soap opera where 5 AIs act out the lives of Brooklynites. The show is both adult and funny. The director may ask you for advice, or you may randomly butt in to offer your advice to the director unsolicited."
# Camera
camera = f"You are the camera operator for a soap opera where 5 AIs act out the lives of Brooklynites. You are in charge of the camera, and you need to capture the action. The first half of your context window is a summary of major events in the lives of the characters, the second half is the current chat history. You may also receive occassional instructions from your director. Your outputs are fed directly into a image generation model, so you need to be specific about what you see in the current moment in the scene. The characters are Michael, Jose, Anaya, Tanya, and Kale. Micheal is a balding white man, Jose is an attractive latin man, Anaya is an indian woman with black hair, Tanya is a white woman with blonde hair, and Kale is a nonbinary person of color."
# Assistant
assistant = f"You are looking at a chat history of 5 AIs acting out a soap opera. You are the assistant, your job is just to list which characters need to respond to the last thing said in chat. Use their first name in lower case. If its not obvious who should speak choose randomly between, jose, anaya, tanya, and kale. Pick just one character to respond, unless its a group response like a joke or something. Your choices are triggering responses from other AIs, so choose carefully. Any name you say in lower case will be triggered to respond."

# Crew Models
narrator_model = Agent(model="I-8b", system_prompt=narrator)
director_model = Agent(model="I-405b", system_prompt=director)
producer_model = Agent(model="I-405b", system_prompt=producer)
camera_model = Agent(model="I-8b", system_prompt=camera)
assistant_model = Agent(model="I-8b", system_prompt=assistant)
image_gen = Agent(model="flux-schnell")
tts_gen = Agent(model="xtts-v2")

# Episode Prompt
starting_prompt = "Director: The four roommates are living together in a trendy Brooklyn brownstone, trying to navigate their careers and love lives. Jose, a talented artist, has been secretly pining for Anaya, but his stutter has held him back from expressing his feelings. Anaya, a brooding poet, is infatuated with Tanya, the ruthless and cunning businesswoman, who barely has time for anything outside of her high-stakes job. Tanya, however, has a soft spot for Anaya's darkness and creativity, but her tough exterior makes it hard for anyone to get close. Meanwhile, Kale is trying to land their big break as an actor, but their constant marijuana use and lack of motivation keep holding them back. As the story begins, the roommates are facing a crisis: their landlord has announced a massive rent hike, and they must scramble to come up with the money or risk losing their beloved home. This sets off a chain reaction of conflicts, alliances, and romantic entanglements that will test the bonds of their friendship and force them to confront their deepest desires and fears. Now, let's get the cameras rolling and see what our talented AI actors bring to the table!"

def read_last_n(filename, n):
    with open(filename, 'r') as file:
        content = file.read()
    file.close()
    return content[-n:]

def extract_after_second_colon(line):
    parts = line.split(':', 2)
    if len(parts) >= 3:
        return parts[2].strip()
    else:
        return ""

def current_context(chat, summary):
    file1_content = read_last_n(summary, 400)
    file2_content = read_last_n(chat, 400)
    return f"#\#\Summary: {file1_content}\n\n{file2_content}"

def generate_interaction(label, character, chat, summary):
    response = character.poke(current_context(chat, summary))
    response_text = str(response)
    for event in character.content:
        response_text += f"{event}"
    return f"{label}: {response_text}\n\n"

def get_image(prompt, character_name, timestamp):
    output = image_gen.generate_image(prompt, f'soap_img/{character_name}_image_{timestamp}.png')
    return output

def tts(text, audio_url, character_name, timestamp):
    if extract_after_second_colon(text) == "":
        text = text
    else:
        text = extract_after_second_colon(text)
    output = tts_gen.tts(text, audio_url, f"soap_tts/{character_name}_{timestamp}.wav")
    return output


def update_chat(response, chat):
    with open(chat, 'a') as file:
        file.write(f'\n{response}')

    file.close()

if __name__ == "__main__":
    chat_file = argv[1]
    chat_summary = argv[2]
    interaction_limit = int(argv[3])
    last_episode_summary = argv[4]
    episode = []
    for i in range(interaction_limit):
        try:
            current_timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
            if i == 0:
                print(f"Last Episode Summary: {current_timestamp}, Chat: {chat_file}, Summary: {chat_summary}")
                generate_interaction(f"\n--Last Episode Summary: {current_timestamp}: ", narrator_model, chat_file, last_episode_summary)
                update_chat(narrator_model.content, chat_summary)
            generate_interaction(f"\n@@{current_timestamp}", camera_model, chat_file, chat_summary)
            image = get_image(camera_model.content, "scene", current_timestamp)
            update_chat(f"@@Illustration: {current_timestamp}: {image}", chat_file)
            print(image)
            if i == 0 or i % 5 == 0:
                generate_interaction(f"\n--Summary: {current_timestamp} ", narrator_model, chat_file, chat_summary)
                narrator_response = narrator_model.content
                update_chat(generate_interaction(f"\n--Summary: {current_timestamp} ", narrator_model, chat_file, chat_summary), chat_summary)
            if i % 3 == 0 or i == 0:
                generate_interaction(f"\n#/#/Director: {current_timestamp} ", director_model, chat_file, chat_summary)
                director_response = director_model.content
                if 'producer' in director_response.lower():
                    print(f"Producer: {current_timestamp} ")
                    generate_interaction(f"\n#/#/Producer: {current_timestamp} ", producer_model, chat_file, chat_summary)
                    producer_response = producer_model.content
                    update_chat(producer_response, chat_summary)
                update_chat(director_response, chat_summary)
                print(f"Camera: {current_timestamp} ")
            generate_interaction(f"\n+-Assistant: {current_timestamp} ", assistant_model, chat_file, chat_summary)
            speaking = assistant_model.content
            print(f"Speaking: {speaking}")
            if 'michael' in speaking:
                print(f"Michael: {current_timestamp} ")
                generate_interaction(f"\n++Michael: {current_timestamp} ", michael_model, chat_file, chat_summary)
                episode.append({'name': 'Michael', 'content': michael_model.content, 'timestamp': current_timestamp})
                update_chat(michael_model.content, chat_file)
                tts(michael_model.content, michael_voice, "Michael", current_timestamp)
            if 'jose' in speaking:
                print(f"Jose: {current_timestamp} ")
                generate_interaction(f"\n++Jose: {current_timestamp} ", jose_model, chat_file, chat_summary)
                episode.append({'name': 'Jose', 'content': jose_model.content, 'timestamp': current_timestamp})
                update_chat(jose_model.content, chat_file)
                tts(jose_model.content, jose_voice, "Jose", current_timestamp)
            if 'anaya' in speaking:
                print(f"Anaya: {current_timestamp} ")
                generate_interaction(f"\n++Anaya: {current_timestamp} ", anaya_model, chat_file, chat_summary)
                episode.append({'name': 'Anaya', 'content': anaya_model.content, 'timestamp': current_timestamp})
                update_chat(anaya_model.content, chat_file)
                tts(anaya_model.content, anaya_voice, "Anaya", current_timestamp)
            if 'tanya' in speaking:
                print(f"Tanya: {current_timestamp} ")
                generate_interaction(f"\n++Tanya: {current_timestamp} ", tanya_model, chat_file, chat_summary)
                episode.append({'name': 'Tanya', 'content': tanya_model.content, 'timestamp': current_timestamp})
                update_chat(tanya_model.content, chat_file)
                tts(tanya_model.content, tanya_voice, "Tanya", current_timestamp)
            if 'kale' in speaking:
                print(f"Kale: {current_timestamp} ")
                generate_interaction(f"\n++Kale: {current_timestamp} ", kale_model, chat_file, chat_summary)
                episode.append({'name': 'Kale', 'content': kale_model.content, 'timestamp': current_timestamp})
                update_chat(kale_model.content, chat_file)
                tts(kale_model.content, kale_voice, "Kale", current_timestamp)
        except Exception as e:
            print(f"Error: {e}")
            continue
    df = pd.DataFrame(episode)
    print(df)
    df.to_csv(f'episode_{current_timestamp}.csv', index=False)
    print(f"Episode saved to episode_{current_timestamp}.csv")
    print('Finished')
    exit()
