import os
from agent import Agent
import datetime
import sys
from bs4 import BeautifulSoup
import re


class Heaven:
    def __init__(self):
        self.agent_405b = Agent(model="Meta: Llama 3.1 405B Instruct", provider="openrouter")
        self.agent_sonnet = Agent(model="Anthropic: Claude 3.5 Sonnet", provider="openrouter")
        self.agent_opus = Agent(model="Anthropic: Claude 3 Opus", provider="openrouter")
        self.agent_gpt4o = Agent(model="gpt-4o-mini-or", provider="openrouter")
        self.agent_flux = Agent(model="flux-dev", provider="replicate")
        self.agent_405b.max_tokens = 16000
        self.agent_sonnet.max_tokens = 16000
        self.agent_opus.max_tokens = 16000
        self.agent_gpt4o.max_tokens = 256
        self.agents = [self.agent_405b, self.agent_sonnet, self.agent_opus]
        
    def create_webpage(self, idea, previous_page=None):
        print(f"Creating webpage with idea: {idea}")
        outline = self._generate_outline(idea, previous_page)
        print(f"Outline: {outline}")
        html_structure = self._build_html_structure(outline)
        print(f"HTML Structure: {html_structure}")
        css = self._create_css(outline, html_structure)
        print(f"CSS: {css}")
        js = self._build_javascript(outline, html_structure)
        print(f"JavaScript: {js}")
        final_page = self._combine_format_validate(html_structure, css, js)
        print(f"Final Page: {final_page}")
        self._save_page(final_page)
        
    def _generate_outline(self, idea, previous_page):
        prompt = f"Create a detailed outline for a webpage based on this idea: {idea}"
        if previous_page:
            prompt += f"\nIterate on this previous version:\n{previous_page}"
        return self.agent_405b.generate_response("You are a web designer. Create a detailed outline for a webpage, including layout, components, and functionality. Don't include any non code content.", prompt)
    
    def _build_html_structure(self, outline):
        prompt = f"Create the HTML structure for a webpage based on this outline:\n{outline}"
        return self.agent_sonnet.generate_response("You are an HTML expert. Create valid, semantic HTML structure. Include placeholders for CSS and JavaScript. Don't include any non code content.", prompt)
    
    def _create_css(self, outline, html_structure):
        prompt = f"Create CSS for a webpage based on this outline and HTML structure:\nOutline:\n{outline}\n\nHTML:\n{html_structure}"
        return self.agent_sonnet.generate_response("You are a CSS expert. Create efficient, responsive CSS that matches the outlined design. Don't include any non code content.", prompt)
    
    def _build_javascript(self, outline, html_structure):
        prompt = f"Create JavaScript for a webpage based on this outline and HTML structure:\nOutline:\n{outline}\n\nHTML:\n{html_structure}"
        return self.agent_opus.generate_response("You are a JavaScript expert. Create efficient, error-free JavaScript that implements the outlined functionality. Don't include any non code content.", prompt)
    
    def _combine_format_validate(self, html_structure, css, js):
        prompt = f"""Combine, format, and validate this HTML, CSS, and JavaScript into a single, valid HTML file that can run locally without any external dependencies, don't include any non code content:

                    HTML Structure:
                    {html_structure}

                    CSS:
                    {css}

                    JavaScript:
                    {js}

                    Ensure that:
                    1. The CSS is placed in a <style> tag in the <head> section.
                    2. The JavaScript is placed in a <script> tag at the end of the <body> section.
                    3. The final HTML file is properly formatted, valid, and can run locally without any external dependencies.
                    4. There are no errors or conflicts between HTML, CSS, and JavaScript.
                """
        return self.agent_opus.generate_response("You are a full-stack web development expert. Combine HTML, CSS, and JavaScript into a single, valid HTML file that can run locally without any external dependencies. Don't include any non code content.", prompt)
    
    def _save_page(self, final_page):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webpage_{timestamp}.html"

        soup = BeautifulSoup(final_page, 'html.parser')
        img_tags = soup.find_all('img')
        image_dict = {}
        try:
            for i, img in enumerate(img_tags):
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                prompt = f"Describe the image that should be at this location: {img_src or img_alt}"
                description = self.agent_gpt4o.generate_response("You are an image description expert. Provide a detailed description for the image based on the context.", prompt)
                filename = f"image_{i+1}.png"
                generated_image = self.agent_flux.generate_image(description, filename)
                img['src'] = filename
                img['alt'] = description
                image_dict[f"image_{i+1}"] = {
                "description": description,
                "generated_image": generated_image
                }

            style_tag = soup.find('style')
            if style_tag:
                css_content = style_tag.string
                background_image_matches = re.findall(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', css_content)
                for i, bg_image in enumerate(background_image_matches):
                    prompt = f"Describe the background image that should be at this location: {bg_image}"
                    description = self.agent_gpt4o.generate_response("You are an image description expert. Provide a detailed description for the background image based on the context.", prompt)
                    filename = f"bg_image_{i+1}.png"
                    generated_image = self.agent_flux.generate_image(description, filename)
                    css_content = css_content.replace(bg_image, filename)
                    image_dict[f"bg_image_{i+1}"] = {
                        "description": description,
                        "generated_image": generated_image
                    }
                style_tag.string = css_content
        except Exception as e:
            print(f"Error generating image: {e}")
            pass

        final_page = str(soup)
        filename = f"webpage_{timestamp}.html"
        print(f"Generated {len(image_dict)} images based on the webpage content.")
        with open(filename, "w") as f:
            f.write(final_page)
        
        print(f"Webpage saved as {filename}")


if __name__ == "__main__":
    heaven = Heaven()
    if len(sys.argv) < 2:
        print("Usage: python hypertext_heaven.py <idea> [previous_page]")
        sys.exit(1)
    
    idea = sys.argv[1]
    previous_page = sys.argv[2] if len(sys.argv) > 2 else None
    
    heaven.create_webpage(idea, previous_page=previous_page)
