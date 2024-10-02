from agent import Agent
import pandas as pd
from datetime import datetime
import os
from moviepy.editor import AudioFileClip, TextClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import configparser
import moviepy.config as conf

config = configparser.ConfigParser()
config.read('config.ini')

conf.IMAGEMAGICK_BINARY = config.get('video', 'MAGICK')

class Podcast:
    def __init__(self,
                 title,
                 prompt,
                 agent1="Meta: Llama 3.1 405B Instruct",
                 agent2="Dolphin 2.9.2 Mixtral 8x22B",
                 agent3="Anthropic: Claude 3 Opus",
                 agent2_name="Sarah",
                 agent3_name="Brian",
                 voice_sample_1=None,
                 voice_sample_2=None,
                 chunk_iterations=1):
        self.agent1 = Agent(model=agent1, provider="openrouter")
        self.agent2 = Agent(model=agent2, provider="openrouter")
        self.agent3 = Agent(model=agent3, provider="openrouter")
        self.agent2_name = agent2_name
        self.agent3_name = agent3_name
        if voice_sample_1 is not None:
            self.agent2_voice_sample = voice_sample_1
        else:
            self.agent2_voice_sample = "https://replicate.delivery/pbxt/JXAkGteYRvJbjwcxA2btRpsd8hfEDuS7slrEgZoinxOUzU9q/female.wav"
        if voice_sample_2 is not None:
            self.agent3_voice_sample = voice_sample_2
        else:
            self.agent3_voice_sample = "https://replicate.delivery/mgxm/671f3086-382f-4850-be82-db853e5f05a8/nixon.mp3"
        self.tts = Agent(model="xtts-v2", provider="replicate")
        self.image = Agent(model="flux-dev", provider="replicate")
        self.agent1_system_prompt = f"You are the director of the podcast 'Coffee with Agents', you are responsible for giving pointers on how to proceed to the hosts. The user prompt is the outline of the podcast. Introduce the topic and then tell the hosts to begin. The topic is: {prompt}. The user prompt will be the conversation up to this point, if there is none, this is the first topic."
        self.agent2_system_prompt = f"You are {self.agent2_name} from the podcast 'Coffee with Agents', you and your co-host {self.agent3_name} discuss various topics, today's topic was generated from this prompt: '{prompt}'. There is a director who will give pointers on how to proceed but you are supposed to speak your mind, do not speak to the director, the audience doesn't know its there, only speak to {self.agent3_name} or Rhetorically. The user prompt is the dialogue between the two of you and the director's instructions. Each line of dialogue is labeled with who said it, always respond to the last thing {self.agent3_name} said or move on to the next topic of discussion as instructed by the director."
        self.agent3_system_prompt = f"You are {self.agent3_name} from the podcast 'Coffee with Agents', you and your co-host {self.agent2_name} discuss various topics, today's topic was generated from this prompt: '{prompt}'. There is a director who will give pointers on how to proceed but you are supposed to speak your mind, do not speak to the director, the audience doesn't know its there, only speak to {self.agent2_name} or Rhetorically. The user prompt is the dialogue between the two of you and the director's instructions. Each line of dialogue is labeled with who said it, always respond to the last thing {self.agent2_name} said or move on to the next topic of discussion as instructed by the director."
        self.title = title
        self.prompt = prompt
        self.chat_history = []
        self.outline = []
        self.df = None
        self.loaded_file = None
        self.image_path = None
        self.chunk_iterations = chunk_iterations

    def generate_outline(self):
        self.agent1_system_prompt = f"Generate a podcast outline based on the user prompt. The outline should be a list of topics or questions that the hosts will discuss. Each topic or question should be concise and engaging. The outline should have new lines between each topic or question. Make sure there are no more than 3 topics, start each topic header with ** followed by a roman numeral, its okay to combine some concepts/questions into one topic."
        outline = self.agent1.generate_response(self.agent1_system_prompt, self.prompt)
        self.outline = outline.split("**")
        self.outline = [topic for topic in self.outline if topic.strip().startswith(("I.", "II.", "III.", "IV.", "V.", "VI.", "VII.", "VIII.", "IX.", "X."))]
        with open(f"podcast_{self.title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w") as f:
            f.write(outline)
        print(f"Outline generated and saved to podcast_{self.title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        
    def chatlog(self):
        chat_string = ""
        for entry in self.chat_history:
            chat_string += f"{entry['role']}: {entry['content']}\n"
        return chat_string

    def generate_podcast(self):
        self.chat_history = [{"role": "Director", "content": '\n'.join(self.outline)}]
        try:
            iterations = 0
            for topic in self.outline:
                if 'end of podcast' in self.chat_history[-1]['content'].lower():
                    break
                if len(topic) > 20:
                    counter = 0
                    while True:
                        self.chat_history.append({"topic": topic, "role": self.agent2_name, "content": self.agent2.generate_response(self.agent2_system_prompt, self.chatlog())})
                        self.chat_history.append({"topic": topic, "role": self.agent3_name, "content": self.agent3.generate_response(self.agent3_system_prompt, self.chatlog())})
                        self.agent1.system_prompt = f"You are the director of the podcast 'Coffee with Agents', you are responsible for giving pointers on how to proceed to the hosts. Keep the hosts on topic and tell the to move on to the next topic with the keyword 'NEXT TOPIC'. Current topic: {topic}. The program is waiting for that keyword to feed the next topic so make sure you include it if its needed. The user prompt will be the conversation up to this point."
                        self.chat_history.append({"topic": topic, "role": "Director", "content": self.agent1.generate_response(self.agent1_system_prompt, self.chatlog())})
                        counter += 1
                        iterations += 1
                        print(f"Iterations: {iterations}")
                        if "end of podcast" in self.chat_history[-1]["content"].lower() or counter > self.chunk_iterations:
                            break
        except Exception as e:
            print(e)
        self.df = pd.DataFrame(self.chat_history)
        self.loaded_file = f"podcast_{self.title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        self.df.to_csv(self.loaded_file, index=False)
        print(f"Podcast generated and saved to {self.loaded_file}")

    def format_chat_history(self):
        formatted_chat_history = []
        run = True
        for _, row in self.df.iterrows():
            if not run:
                break
            content_lines = row['content'].split('\n')
            for line in content_lines:
                if line.lower().startswith(self.agent2_name.lower() + ": "):
                    formatted_chat_history.append({"role": self.agent2_name, "content": line[len(self.agent2_name):].strip()})
                elif line.lower().startswith(self.agent3_name.lower() + ": "):
                    formatted_chat_history.append({"role": self.agent3_name, "content": line[len(self.agent3_name):].strip()})
                elif line.lower().startswith("director"):
                    continue
                if 'end of podcast' in line.lower():
                    run = False
        self.chat_history = formatted_chat_history
        self.df = pd.DataFrame(self.chat_history)
        self.df.to_csv(self.loaded_file, index=False, mode='w')
        print(f"Chat history formatted and saved to {self.loaded_file}")

    def generate_tts(self):
        if self.df is None:
            raise Exception("No chat history found")
        for index, row in self.df.iterrows():
            file_path = f'tts/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.wav'
            if row["role"] == self.agent2_name:
                self.tts.tts(row["content"], self.agent2_voice_sample, file_path)
                self.df.at[index, "tts"] = file_path
            elif row["role"] == self.agent3_name:
                self.tts.tts(row["content"], self.agent3_voice_sample, file_path)
                self.df.at[index, "tts"] = file_path
        if self.loaded_file is not None:
            self.df.to_csv(self.loaded_file, index=False, mode='w')
        else:
            self.loaded_file = f"podcast_{self.title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
            self.df.to_csv(self.loaded_file, index=False)
        print(f"TTS generated and saved to {self.loaded_file}")

    def generate_image(self):
        self.agent1.system_prompt = f"You are the director of the podcast 'Coffee with Agents', you are responsible for generating an image description for the background of the podcast. The user prompt is the summary of the podcast. The outline is: {self.outline}. Your response should be a description of the image, no more than 2 sentences, it will be given directly to the image generation model."
        self.image_prompt = self.agent1.generate_response(self.agent1_system_prompt, self.chatlog())
        self.image_path = f'img/{self.title}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png'
        self.image.generate_image(self.image_prompt, self.image_path)
        print(f"Image generated and saved to {self.image_path}")

    def generate_video(self, background_image_path):
        if self.df is None or 'tts' not in self.df.columns:
            raise Exception("No TTS data found. Please run generate_tts() first.")

        clips = []
        for _, row in self.df.iterrows():
            if row['role'] not in ['Director', 'director']:
                audio = AudioFileClip(row['tts'])
                txt_clip = TextClip(row['content'], fontsize=24, color='white', size=(720, 480), method='caption', align='center')
                txt_clip = txt_clip.set_pos('center').set_duration(audio.duration)
                bg_clip = ImageClip(background_image_path).set_duration(audio.duration)
                video_clip = CompositeVideoClip([bg_clip, txt_clip])
                video_clip = video_clip.set_audio(audio)
                clips.append(video_clip)
        final_clip = concatenate_videoclips(clips)
        output_filename = f"podcast_{self.title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        final_clip.write_videofile(output_filename, fps=24)
        print(f"Video generated and saved to {output_filename}")

    def generate_podcast_full(self):
        print("Generating outline...")
        self.generate_outline()
        print("Generating podcast...")
        self.generate_podcast()
        print("Formatting chat history...")
        self.format_chat_history()
        print("Generating TTS...")
        self.generate_tts()
        print("Generating image...")
        self.generate_image()
        print("Generating video...")
        self.generate_video(self.image_path)
        print("Podcast generation complete.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python podcast.py <title> <prompt> [chunk_iterations]")
        print("Example: python podcast.py 'AI Ethics' 'What are the ethical implications of AI?' 2")
        sys.exit(1)

    title = sys.argv[1]
    prompt = sys.argv[2]
    chunk_iterations = 0 if len(sys.argv) < 4 else int(sys.argv[3])
    podcast = Podcast(title=title, prompt=prompt, chunk_iterations=chunk_iterations)
    podcast.generate_podcast_full()
