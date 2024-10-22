import PyPDF2
from deertick import Agent
import os
import argparse
import logging
import sys
import traceback
import asyncio
from collections import OrderedDict

class TextProcessor:
    def __init__(self, model="cohere/command-r-plus-08-2024", provider="openrouter", 
                 chunk_size=5, system_prompt=None, rate_limit=2.0, max_concurrent=5):
        self.agent = Agent(model=model, provider=provider, rate_limit=rate_limit, max_concurrent=max_concurrent)
        self.chunk_size = chunk_size
        self.default_system_prompt = "Correct the spacing of each line in the chunk. Some of them will be jumbled together like this 'Britainsuicideremainsthehighestsinglecauseofdeathforbothmalesandfemalesaged15–34.', these are the only ones that need to be adjusted. Do not change the content or add any punctuation. Do not add any capitalization. Only adjust spacing. There may be no need to adjust spacing within a specific chunk. Preserve line breaks."
        self.agent.system_prompt = system_prompt if system_prompt else self.default_system_prompt
        self.setup_logging()

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        fh = logging.FileHandler('text_processor.log')
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def pdf_to_txt(self, pdf_file, txt_file):
        try:
            with open(pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                with open(txt_file, 'w', encoding='utf-8') as output:
                    for page in reader.pages:
                        output.write(page.extract_text())
            self.logger.info(f"PDF converted to text. Output saved to {txt_file}")
        except Exception as e:
            return self.handle_error(f"Error converting PDF to text: {str(e)}", pdf_file)

    def correct_line_formatting(self, input_file, output_file, resume_line=0):
        try:
            with open(input_file, 'r', encoding='utf-8', errors='replace') as infile, open(output_file, 'a', encoding='utf-8') as outfile:
                chunk = []
                for i, line in enumerate(infile):
                    if i < resume_line:
                        continue
                    chunk.append(line.strip())
                    if len(chunk) == self.chunk_size:
                        self.process_chunk(chunk, outfile)
                        chunk = []
                        # Save progress
                        with open(f"{output_file}.progress", 'w') as progress_file:
                            progress_file.write(str(i + 1))
                
                if chunk:
                    self.process_chunk(chunk, outfile)

            self.logger.info(f"Formatting correction complete. Output saved to {output_file}")
            # Remove progress file if exists
            if os.path.exists(f"{output_file}.progress"):
                os.remove(f"{output_file}.progress")
        except Exception as e:
            return self.handle_error(f"Error correcting line formatting: {str(e)}", input_file)

    def process_chunk(self, chunk, outfile):
        input_text = "\n".join(chunk)
        corrected_text = self.agent.poke(input_text).strip()
        corrected_lines = corrected_text.split('\n')
        
        self.logger.debug(f'Input chunk:\n{input_text}\n')
        self.logger.debug(f'Output chunk:\n{corrected_text}\n')
        self.logger.debug('***********************************')
        
        for line in corrected_lines:
            outfile.write(line + '\n')

    def handle_error(self, error_message, file_path):
        self.logger.error(error_message)
        self.logger.error("Full traceback:")
        self.logger.error(traceback.format_exc())
        
        if "PDF" in error_message:
            self.logger.error("There was an issue with the PDF file. Please check if it's corrupted or password-protected.")
        elif "formatting" in error_message:
            self.logger.error("There was an issue during the formatting process. Please check the input file encoding.")
        elif "permission" in error_message.lower():
            self.logger.error("Permission denied. Please check if you have the necessary permissions to read/write the files.")
        elif "memory" in error_message.lower():
            self.logger.error("Out of memory error. The file might be too large to process. Try increasing available memory or processing in smaller chunks.")
        elif "not found" in error_message.lower():
            self.logger.error("File not found. Please check if the specified file path is correct.")
        elif "network" in error_message.lower():
            self.logger.error("Network error occurred. Please check your internet connection and try again.")
        elif "api" in error_message.lower() or "choices" in error_message.lower():
            self.logger.error("API error occurred. There might be issues with the AI service. Please try again later or check your API credentials.")
        else:
            self.logger.error("An unexpected error occurred. Please check the error message and stack trace for more details.")
        
        while True:
            choice = input("Do you want to try again with a different input file? (y/n): ").lower()
            if choice == 'y':
                new_file = input("Enter the path to the new input file: ")
                return new_file
            elif choice == 'n':
                self.logger.info("Exiting the program.")
                sys.exit(1)
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    async def process_chunk_async(self, chunk, chunk_id):
        input_text = "\n".join(chunk)
        corrected_text = await self.agent.async_poke(input_text)
        return chunk_id, corrected_text.strip().split('\n')

    async def correct_line_formatting_async(self, input_file, output_file, resume_line=0):
        try:
            tasks = []
            results = OrderedDict()
            with open(input_file, 'r', encoding='utf-8', errors='replace') as infile:
                chunk = []
                for i, line in enumerate(infile):
                    if i < resume_line:
                        continue
                    chunk.append(line.strip())
                    if len(chunk) == self.chunk_size:
                        chunk_id = i // self.chunk_size
                        task = asyncio.create_task(self.process_chunk_async(chunk, chunk_id))
                        tasks.append(task)
                        chunk = []

                if chunk:
                    chunk_id = (i // self.chunk_size) + 1
                    task = asyncio.create_task(self.process_chunk_async(chunk, chunk_id))
                    tasks.append(task)

            for completed_task in asyncio.as_completed(tasks):
                chunk_id, corrected_lines = await completed_task
                results[chunk_id] = corrected_lines

            with open(output_file, 'w', encoding='utf-8') as outfile:
                for chunk_id in sorted(results.keys()):
                    for line in results[chunk_id]:
                        outfile.write(line + '\n')
                    # Save progress
                    with open(f"{output_file}.progress", 'w') as progress_file:
                        progress_file.write(str((chunk_id + 1) * self.chunk_size))

            self.logger.info(f"Formatting correction complete. Output saved to {output_file}")
            # Remove progress file if exists
            if os.path.exists(f"{output_file}.progress"):
                os.remove(f"{output_file}.progress")
        except Exception as e:
            return self.handle_error(f"Error correcting line formatting: {str(e)}", input_file)

async def main_async():
    parser = argparse.ArgumentParser(description="Process PDF files and correct line formatting.")
    parser.add_argument("input_file", help="Input PDF file path")
    parser.add_argument("output_file", help="Output text file path")
    parser.add_argument("--chunk_size", type=int, default=5, help="Number of lines per chunk (default: 5)")
    parser.add_argument("--model", default="cohere/command-r-plus-08-2024", help="AI model to use")
    parser.add_argument("--provider", default="openrouter", help="AI provider to use")
    parser.add_argument("--keep_txt", action="store_true", help="Keep the intermediate text file")
    parser.add_argument("--system_prompt", help="Custom system prompt for the AI")
    parser.add_argument("--resume", action="store_true", help="Resume from last saved progress")
    parser.add_argument("--rate_limit", type=float, default=2.0, help="Rate limit in seconds between API calls (default: 2.0)")
    parser.add_argument("--max_concurrent", type=int, default=5, help="Maximum number of concurrent API calls (default: 5)")

    args = parser.parse_args()

    processor = TextProcessor(model=args.model, provider=args.provider, chunk_size=args.chunk_size, 
                              system_prompt=args.system_prompt, rate_limit=args.rate_limit, 
                              max_concurrent=args.max_concurrent)
    
    input_file = args.input_file
    while True:
        txt_file = input_file.rsplit('.', 1)[0] + ".txt"

        # Convert PDF to TXT if not resuming
        if not args.resume:
            result = processor.pdf_to_txt(input_file, txt_file)
            if isinstance(result, str):
                input_file = result
                continue

        # Check for progress file
        resume_line = 0
        if args.resume and os.path.exists(f"{args.output_file}.progress"):
            with open(f"{args.output_file}.progress", 'r') as progress_file:
                resume_line = int(progress_file.read().strip())

        # Correct line formatting asynchronously
        result = await processor.correct_line_formatting_async(txt_file, args.output_file, resume_line)
        if isinstance(result, str):
            input_file = result
            continue

        break

    # Clean up intermediate txt file if not specified to keep
    if not args.keep_txt and not args.resume:
        os.remove(txt_file)
        print(f"Removed intermediate file: {txt_file}")
    else:
        print(f"Kept intermediate file: {txt_file}")

if __name__ == "__main__":
    asyncio.run(main_async())
