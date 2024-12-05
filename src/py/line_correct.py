import PyPDF2
from deertick import Agent
import os
import argparse
import logging
import sys
import traceback
import asyncio
from collections import OrderedDict
import pandas as pd
import io

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

    def pdf_to_txt(self, pdf_file):
        try:
            text = []
            with open(pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            self.handle_error(f"Error converting PDF to text: {str(e)}", pdf_file)
            return None

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

    def read_input_file(self, input_file, columns=None):
        _, ext = os.path.splitext(input_file)
        if ext.lower() == '.pdf':
            return self.pdf_to_txt(input_file)
        elif ext.lower() in ['.txt', '.md']:
            with open(input_file, 'r', encoding='utf-8') as f:
                return f.readlines()
        elif ext.lower() == '.csv':
            df = pd.read_csv(input_file)
            if columns:
                df = df[columns]
            return df.apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def correct_line_formatting_async(self, input_file, output_file, resume_line=0, columns=None):
        try:
            lines = self.read_input_file(input_file, columns)
            if lines is None:
                return

            tasks = []
            results = OrderedDict()

            for i in range(resume_line, len(lines), self.chunk_size):
                chunk = lines[i:i+self.chunk_size]
                chunk_id = i // self.chunk_size
                task = asyncio.create_task(self.process_chunk_async(chunk, chunk_id))
                tasks.append(task)

            for completed_task in asyncio.as_completed(tasks):
                chunk_id, corrected_lines = await completed_task
                results[chunk_id] = corrected_lines

            _, ext = os.path.splitext(output_file)
            if ext.lower() == '.csv':
                self.write_csv_output(results, output_file, columns)
            else:
                self.write_text_output(results, output_file)

            self.logger.info(f"Formatting correction complete. Output saved to {output_file}")
            # Remove progress file if exists
            if os.path.exists(f"{output_file}.progress"):
                os.remove(f"{output_file}.progress")
        except Exception as e:
            return self.handle_error(f"Error correcting line formatting: {str(e)}", input_file)

    def write_csv_output(self, results, output_file, columns):
        df = pd.DataFrame(columns=columns if columns else ['corrected_text'])
        for chunk_id in sorted(results.keys()):
            for line in results[chunk_id]:
                if columns:
                    parts = line.split(maxsplit=len(columns)-1)
                    df = df.append(dict(zip(columns, parts)), ignore_index=True)
                else:
                    df = df.append({'corrected_text': line}, ignore_index=True)
        df.to_csv(output_file, index=False)

    def write_text_output(self, results, output_file):
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for chunk_id in sorted(results.keys()):
                for line in results[chunk_id]:
                    outfile.write(line + '\n')
                # Save progress
                with open(f"{output_file}.progress", 'w') as progress_file:
                    progress_file.write(str((chunk_id + 1) * self.chunk_size))

    def save_text_to_file(self, text: str, file_path: str):
        """
        Save a single string of text to a .txt file.

        Args:
        text (str): The text to be saved.
        file_path (str): The path where the file should be saved.

        Returns:
        None
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text)
            self.logger.info(f"Text successfully saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving text to file: {str(e)}")
            self.handle_error(f"Error saving text to file: {str(e)}", file_path)

    def remove_blank_lines(self, input_file, output_file):
        """
        Remove blank lines from the input file and save the result to the output file.
        
        Args:
        input_file (str): Path to the input file.
        output_file (str): Path to the output file.
        
        Returns:
        None
        """
        try:
            lines = self.read_input_file(input_file)
            if lines is None:
                return

            non_blank_lines = [line.strip() for line in lines if line.strip()]

            _, ext = os.path.splitext(output_file)
            if ext.lower() == '.csv':
                df = pd.DataFrame(non_blank_lines, columns=['text'])
                df.to_csv(output_file, index=False)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(non_blank_lines))

            self.logger.info(f"Blank lines removed. Output saved to {output_file}")
        except Exception as e:
            self.handle_error(f"Error removing blank lines: {str(e)}", input_file)

    def txt_to_md(self, input_file, output_file):
        """
        Convert a text file to Markdown format.
        
        Args:
        input_file (str): Path to the input text file.
        output_file (str): Path to the output Markdown file.
        
        Returns:
        None
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
                in_code_block = False
                for line in infile:
                    stripped_line = line.strip()
                    
                    # Handle empty lines
                    if not stripped_line:
                        outfile.write('\n')
                        continue
                    
                    # Check for code blocks
                    if stripped_line.startswith('```'):
                        in_code_block = not in_code_block
                        outfile.write(line)
                        continue
                    
                    if not in_code_block:
                        # Convert headers
                        if stripped_line.startswith('#'):
                            outfile.write(line)
                        # Convert lists
                        elif stripped_line.startswith(('- ', '* ', '+ ')):
                            outfile.write(line)
                        # Convert numbered lists
                        elif stripped_line[0].isdigit() and len(stripped_line) > 1 and stripped_line[1:].startswith('. '):
                            outfile.write(line)
                        # Convert links
                        elif '[' in line and '](' in line and ')' in line:
                            outfile.write(line)
                        # Convert emphasis
                        elif '*' in line or '_' in line:
                            outfile.write(line)
                        # Convert horizontal rules
                        elif set(stripped_line) in [set('-'), set('*'), set('_')] and len(stripped_line) >= 3:
                            outfile.write(line)
                        # Convert blockquotes
                        elif stripped_line.startswith('>'):
                            outfile.write(line)
                        # Regular paragraph
                        else:
                            outfile.write(line)
                    else:
                        # Inside code block, write as is
                        outfile.write(line)
            
            self.logger.info(f"Text file converted to Markdown. Output saved to {output_file}")
        except Exception as e:
            self.handle_error(f"Error converting text to Markdown: {str(e)}", input_file)

async def main_async():
    parser = argparse.ArgumentParser(description="Process files and correct line formatting.")
    parser.add_argument("input_file", help="Input file path (PDF, TXT, MD, or CSV)")
    parser.add_argument("output_file", help="Output file path (TXT or CSV)")
    parser.add_argument("--chunk_size", type=int, default=5, help="Number of lines per chunk (default: 5)")
    parser.add_argument("--model", default="cohere/command-r-plus-08-2024", help="AI model to use")
    parser.add_argument("--provider", default="openrouter", help="AI provider to use")
    parser.add_argument("--system_prompt", help="Custom system prompt for the AI")
    parser.add_argument("--resume", action="store_true", help="Resume from last saved progress")
    parser.add_argument("--rate_limit", type=float, default=2.0, help="Rate limit in seconds between API calls (default: 2.0)")
    parser.add_argument("--max_concurrent", type=int, default=5, help="Maximum number of concurrent API calls (default: 5)")
    parser.add_argument("--columns", nargs='+', help="Columns to process for CSV input (space-separated)")
    parser.add_argument("--pdf_to_txt", action="store_true", help="Convert PDF to TXT without processing")
    parser.add_argument("--remove_blank_lines", action="store_true", help="Remove blank lines from the input file")
    parser.add_argument("--txt_to_md", action="store_true", help="Convert TXT to MD without processing")

    args = parser.parse_args()

    processor = TextProcessor(model=args.model, provider=args.provider, chunk_size=args.chunk_size, 
                              system_prompt=args.system_prompt, rate_limit=args.rate_limit, 
                              max_concurrent=args.max_concurrent)
    
    if args.pdf_to_txt:
        if not args.input_file.lower().endswith('.pdf'):
            print("Error: Input file must be a PDF when using --pdf_to_txt option.")
            sys.exit(1)
        text = processor.pdf_to_txt(args.input_file)
        if text:
            processor.save_text_to_file(text, args.output_file)
        sys.exit(0)

    if args.remove_blank_lines:
        processor.remove_blank_lines(args.input_file, args.output_file)
        sys.exit(0)

    if args.txt_to_md:
        if not args.input_file.lower().endswith('.txt'):
            print("Error: Input file must be a TXT when using --txt_to_md option.")
            sys.exit(1)
        processor.txt_to_md(args.input_file, args.output_file)
        sys.exit(0)

    input_file = args.input_file
    resume_line = 0
    if args.resume and os.path.exists(f"{args.output_file}.progress"):
        with open(f"{args.output_file}.progress", 'r') as progress_file:
            resume_line = int(progress_file.read().strip())

    await processor.correct_line_formatting_async(input_file, args.output_file, resume_line, args.columns)

if __name__ == "__main__":
    asyncio.run(main_async())
