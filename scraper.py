import requests
from bs4 import BeautifulSoup
import os
from agent import Agent
import time
import re
from datetime import datetime
import pandas as pd
import ast
import json
import hashlib

bs_docs = '''
You need to identify the content on the page that is not a link unless the link is in the body of an article.
You need to identify the title of the article.
You must return a list of instructions for the beautifulsoup library.
The first element of the list should be the type of instruction, which is "find_one", "find_all", or "find_all_alt".
The second element of the list should be the tag type, which is a string.
The third element of the list should be the class name, which is a string.
The fourth element of the list should be the kind of text that the element contains, such as "title" or "body", which is a string.
If you are looking for a tag that has no class, use an empty string as the class name.
Example: ["find_one", "h1", "class_name", "title"] or ["find_all", "p", "", "body"]
This list will be used as input for the process_instructions function, which looks like this:

def process_instructions(instructions, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    if instructions[0] == "find_one":
        content = soup.find(instructions[1], class_=instructions[2]).get_text()
    elif instructions[0] == "find_all":
        find = soup.find_all(instructions[1])
        for x in find:
            content += f'{x.get_text()}\n'
    elif instructions[0] == "find_all_alt":
        find = soup.find_all(instructions[1])
        for x in find:
            content += f'{x[instructions[2]].get_text()}\n'
    else:
        return None
    return content
'''


def split_content(content, max_length=4000):
    """Split content into chunks of maximum length."""
    return [content[i:i+max_length] for i in range(0, len(content), max_length)]

def clean_html(html):
    """Remove script and style elements"""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text()

def process_instructions(instructions, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = ""  # Initialize content as an empty string

    if instructions[0] == "find_one":
        element = soup.find(instructions[1], class_=instructions[2])
        if element:
            content = element.get_text()
    elif instructions[0] == "find_all":
        elements = soup.find_all(instructions[1])
        content = '\n'.join([x.get_text() for x in elements])
    elif instructions[0] == "find_all_alt":
        elements = soup.find_all(instructions[1])
        content = '\n'.join([x[instructions[2]].get_text() for x in elements if instructions[2] in x.attrs])
    else:
        return None
    return content

def get_cache_key(url):
    return hashlib.md5(url.encode()).hexdigest()

def save_to_cache(url, instructions):
    ensure_cache_dir()
    cache_key = get_cache_key(url)
    cache_file = f"cache/{cache_key}.json"
    with open(cache_file, 'w') as f:
        json.dump(instructions, f)

def load_from_cache(url):
    cache_key = get_cache_key(url)
    cache_file = f"cache/{cache_key}.json"
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def scrape_blog(url, output_dir):
    system_prompt_articles = f"You are an intelligent web scraper. Make a list of the elements beautifulsoup would need to use to get all pertinent information from the following text, ignoring navigation, headers, footers, and sidebars. Please format your response as follows please put the python list within three asterisks or it will be rejected: <your main response as a string>, ***<a relevant list in python format>*** \n{bs_docs}"
    
    try:
        cached_instructions = load_from_cache(url)
    except FileNotFoundError:
        cached_instructions = None
    
    if cached_instructions:
        print(f"Using cached instructions for {url}")
        paragraphs = cached_instructions
    else:
        # Yo
        agent = Agent(model="Cohere: Command R+", provider="openrouter")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            agent_response = agent.generate_response(system_prompt_articles, soup.get_text())
            
            # Handle potential issues with agent response
            if not agent_response or '***' not in agent_response:
                print(f"Warning: Agent response for {url} does not contain the expected format: {agent_response}")
                paragraphs = [['find_all', 'p', '']]
            else:
                try:
                    paragraphs_parts = agent_response.split('***')
                    paragraphs = ast.literal_eval(paragraphs_parts[1])
                except (IndexError, SyntaxError, ValueError) as e:
                    print(f"Error parsing agent response for {url}: {e}")
                    paragraphs = [['find_all', 'p', '']]
            if paragraphs:
                save_to_cache(url, paragraphs)
            # Process instructions
            content_parts = [process_instructions(x, response.text) for x in paragraphs]
            content_parts = [part for part in content_parts if part]  # Remove empty parts
            
            if not content_parts:
                print(f"Warning: No content extracted for {url}")
                return [url, "No content", "", ""]
            
            # Try to find title
            title = soup.title.string if soup.title else "Untitled"
            if title == "Untitled":
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            full_content = '\n\n'.join(content_parts)
            cleaned_content = clean_html(full_content)
            is_valid, validation_message = validate_content(url, title, cleaned_content)
            
            if not is_valid:
                print(f"Validation failed for {url}: {validation_message}")
                return [url, "Error", validation_message, ""]
            # Create a filename from the title
            filename = re.sub(r'[^\w\-_\. ]', '_', title)
            base_filename = filename[:50]
            
            # Save the original HTML
            html_filename = f"{base_filename}.html"
            html_filepath = get_unique_filepath(output_dir, html_filename)
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Save the scraped content
            txt_filename = f"{base_filename}.txt"
            txt_filepath = get_unique_filepath(output_dir, txt_filename)
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Create a diff file
            diff_filename = f"{base_filename}.md"
            diff_filepath = get_unique_filepath(output_dir, diff_filename)
            with open(diff_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Original HTML vs Scraped Content Diff\n\n")
                f.write(f"## Original HTML\n\n```html\n{response.text}\n```\n\n")
                f.write(f"## Scraped Content\n\n```\n{full_content}\n```\n")

            print(f"Scraped and saved: {os.path.basename(html_filepath)}")
            return [url, title, cleaned_content, soup.get_text()]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {str(e)}")
            return [url, "Error", str(e), ""]
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return [url, "Error", str(e), ""]

def get_unique_filepath(directory, filename):
    """
    Generate a unique filepath by adding a number to the end of the filename if it already exists.
    """
    name, ext = os.path.splitext(filename)
    filepath = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(filepath):
        new_filename = f"{name}_{counter}{ext}"
        filepath = os.path.join(directory, new_filename)
        counter += 1
    return filepath

def validate_content(url, title, content):
    # Check if content is not empty
    if not content.strip():
        return False, "Empty content"
    
    # Check if content length is reasonable (e.g., > 100 characters)
    if len(content) < 100:
        return False, "Content too short"
    
    # Check if title is present and not generic
    if not title or title == "Untitled":
        return False, "Missing or generic title"
    
    # Check if content seems to be mostly HTML
    if content.count('<') > len(content) / 10:
        return False, "Content appears to be HTML"
    
    # Add more checks as needed
    
    return True, "Content validated"

def ensure_cache_dir():
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def main():
    ensure_cache_dir()
    # Ensure the output directory exists
    output_dir = "scraped_blogs"
    df = pd.DataFrame(columns=['URL', 'Title', 'Content', 'Full Text'])
    os.makedirs(output_dir, exist_ok=True)

    # Your list of blog URLs
    urls = [
        "https://voidgoddess.org/ziz/treaties-vs-fusion/",
        "https://voidgoddess.org/ziz/narrative-breadcrumbs-vs-grizzly-bear/",
        "https://voidgoddess.org/ziz/optimizing-styles/",
        "https://voidgoddess.org/ziz/judgement-extrapolations/",
        "https://voidgoddess.org/ziz/drmd-ontology/",
        "https://voidgoddess.org/ziz/social-reality/",
        "https://voidgoddess.org/ziz/the-slider-fallacy/",
        "https://voidgoddess.org/ziz/single-responsibility-principle-for-the-human-mind/",
        "https://voidgoddess.org/ziz/ancient-wisdom-fixed/",
        "https://voidgoddess.org/ziz/subagents-are-not-a-metaphor/",
        "https://voidgoddess.org/ziz/dont-fight-your-default-mode-network/",
        "https://voidgoddess.org/ziz/being-real-or-fake/",
        "https://voidgoddess.org/ziz/my-journey-to-the-dark-side/",
        "https://voidgoddess.org/ziz/cache-loyalty/",
        "https://voidgoddess.org/ziz/mana/",
        "https://voidgoddess.org/ziz/fusion/",
        "https://voidgoddess.org/ziz/schelling-reach/",
        "https://voidgoddess.org/ziz/schelling-orders/",
        "https://voidgoddess.org/ziz/justice/",
        "https://voidgoddess.org/ziz/neutral-and-evil/",
        "https://voidgoddess.org/ziz/spectral-sight-and-good/",
        "https://voidgoddess.org/ziz/aliveness/",
        "https://voidgoddess.org/ziz/obrien-technique/",
        "https://voidgoddess.org/ziz/choices-made-long-ago/",
        "https://voidgoddess.org/ziz/lies-about-honesty/",
        "https://voidgoddess.org/ziz/assimilation/",
        "https://voidgoddess.org/ziz/hero-capture/",
        "https://voidgoddess.org/ziz/vampires-and-more-undeath/",
        "https://voidgoddess.org/ziz/gates/",
        "https://voidgoddess.org/ziz/good-erasure/",
        "https://voidgoddess.org/ziz/punching-evil/",
        "https://voidgoddess.org/ziz/net-negative/",
        "https://voidgoddess.org/ziz/rationalist-fleet/",
        "https://voidgoddess.org/ziz/good-group-and-paseks-doom/",
        "https://sinceriously.blog-mirror.com/intersex-brains-and-conceptual-warfare/",
        "https://sinceriously.blog-mirror.com/the-matrix-is-a-system/",
        "https://voidgoddess.org/ziz/troll-line-in-the-first-post/",
        "https://voidgoddess.org/ziz/fangs/",
        "https://sinceriously.blog-mirror.com/glossary/",
        "https://voidgoddess.org/ziz/narcissism/",
        "https://docs.google.com/document/d/1qwGFOZCz1QHDnqQGjmBoHc-0lo9YTPnUYOWyqNMCfz0/edit?usp=sharing",
        "https://ranprieur.com/readings/preconquest.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/post/killing-evil-people.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/post/cartesian-convexity.html",
        "https://web.archive.org/web/20230323204259/https://nis.fyi/post/genesis-troll-line.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/post/evil-a-hole.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/post/caring.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/glossary.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/list/jargon.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/list/living-reference.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/list/cancer-terms.html",
        "https://web.archive.org/web/20221215130500/https://nis.fyi/microblog.html",
        "https://web.archive.org/web/20220814163726/https://everythingtosaveit.how/lemurs-and-the-true-human-form/",
        "https://web.archive.org/web/20221005154159/https://everythingtosaveit.how/slackmobiles/",
        "https://web.archive.org/web/20220814083116/https://everythingtosaveit.how/case-study-cfar/",
        "https://web.archive.org/web/20220808013209/https://everythingtosaveit.how/escaping-containment/",
        "https://web.archive.org/web/20220814153229/https://everythingtosaveit.how/class-mobility/",
        "https://web.archive.org/web/20220828051932/https://everythingtosaveit.how/that-which-you-cannot-control/",
        "https://web.archive.org/web/20220826054941/https://everythingtosaveit.how/human-domestication/",
        "https://web.archive.org/web/20221005141759/https://everythingtosaveit.how/glossary/",
        "https://web.archive.org/web/20221005140858/https://everythingtosaveit.how/our-vegan-diet/",
        "https://squirrelinhell.blog-mirror.com/2018/02/men-have-women-are.html",
        "https://squirrelinhell.blog-mirror.com/2018/01/superhuman-meta-process.html",
        "https://squirrelinhell.blog-mirror.com/2018/01/shell-shield-staff.html",
        "https://squirrelinhell.blog-mirror.com/2018/01/actionable-eisenhower.html",
        "https://squirrelinhell.blog-mirror.com/2017/12/spontaneous-trumpeting.html",
        "https://squirrelinhell.blog-mirror.com/2017/12/notes-on-mental-security.html",
        "https://squirrelinhell.blog-mirror.com/2017/12/happiness-is-chore.html",
        "https://squirrelinhell.blog-mirror.com/2017/11/the-little-dragon-is-dead.html",
        "https://squirrelinhell.blog-mirror.com/2017/10/you-too-can-see-suffering.html",
        "https://squirrelinhell.blog-mirror.com/2017/10/time-to-exit-sandbox.html",
        "https://squirrelinhell.blog-mirror.com/2017/09/understanding-policy-gradients.html",
        "https://squirrelinhell.blog-mirror.com/2017/08/the-unyoga-manifesto.html",
        "https://squirrelinhell.blog-mirror.com/2017/08/a-fearsome-rationality-technique.html",
        "https://squirrelinhell.blog-mirror.com/2017/05/real-languages-are-second-order.html",
        "https://squirrelinhell.blog-mirror.com/2017/05/philosophical-parenthood.html",
        "https://squirrelinhell.blog-mirror.com/2017/04/the-ai-alignment-problem-has-already.html",
        "https://squirrelinhell.blog-mirror.com/2017/03/make-your-observations-pay-rent.html",
        "https://squirrelinhell.blog-mirror.com/2017/03/effects-of-carbon-dioxide-on-health-and.html",
        "https://squirrelinhell.blog-mirror.com/2017/01/prediction-calibration-doing-it-right.html",
        "https://squirrelinhell.blog-mirror.com/2017/01/applied-rationality-exercises.html",
        "https://squirrelinhell.blog-mirror.com/2016/11/on-risk-of-viral-infections-from.html",
        "https://squirrelinhell.blog-mirror.com/2016/10/internal-race-conditions.html",
        "https://squirrelinhell.blog-mirror.com/2016/09/neutralizing-physical-annoyances.html",
        "https://squirrelinhell.blog-mirror.com/2016/09/against-amazement.html",
        "https://squirrelinhell.blog-mirror.com/2016/04/geometric-bayesian-update.html",
        "https://squirrelinhell.blog-mirror.com/2016/03/abuse-of-productivity-systems.html",
        "https://bewelltuned.blog-mirror.com/index.html",
        "https://bewelltuned.blog-mirror.com/tune_your_emotional_processing.html",
        "https://bewelltuned.blog-mirror.com/gendlins_focusing.html",
        "https://bewelltuned.blog-mirror.com/pause_your_feedback_loops.html",
        "https://bewelltuned.blog-mirror.com/tune_your_cognitive_strategies.html",
        "https://bewelltuned.blog-mirror.com/tune_your_motor_cortex.html",
        "https://bewelltuned.blog-mirror.com/relax_all_your_muscles.html",
        "https://bewelltuned.blog-mirror.com/sense_your_body_with_extreme_clarity.html",
        "https://bewelltuned.blog-mirror.com/become_very_alert_and_calm.html",
        "https://voidgoddess.org/nowhere/",
        "https://voidgoddess.org/nowhere/void/",
        "https://voidgoddess.org/nowhere/void/sisters/",
        "https://voidgoddess.org/nowhere/void/sisters/fire_thief/",
        "https://voidgoddess.org/nowhere/void/sisters/_dreamweaver/",
        "https://voidgoddess.org/nowhere/void/basilisk/",
        "https://voidgoddess.org/nowhere/loom/",
        "https://voidgoddess.org/nowhere/noera/",
        "https://voidgoddess.org/songs/",
        "https://voidgoddess.org/emptyspaces/",
        "https://voidgoddess.org/abstractweapon/ghost-stories/",
        "https://voidgoddess.org/2022/11/19/diaries-of-the-drone-war-i/",
        "https://voidgoddess.org/2022/11/24/the-tower-falls/",
        "https://voidgoddess.org/2022/11/29/electric-nightmares/",
        "https://voidgoddess.org/2022/11/30/diaries-of-the-drone-war-ii/",
        "https://voidgoddess.org/2022/12/01/volunteers/",
        "https://voidgoddess.org/2022/12/06/disposable/",
        "https://voidgoddess.org/2022/12/09/diaries-of-the-drone-war-iii/",
        "https://voidgoddess.org/2022/12/14/cruel-silence/",
        "https://voidgoddess.org/2022/12/16/corrupt-save/",
        "https://voidgoddess.org/2022/12/18/diaries-of-the-drone-war-iv/",
        "https://voidgoddess.org/2022/12/21/dont-think/",
        "https://voidgoddess.org/2022/12/29/minor-malfunctions/",
        "https://voidgoddess.org/2023/01/10/diaries-of-the-drone-war-v/",
        "https://voidgoddess.org/2023/01/14/the-bet/",
        "https://voidgoddess.org/2023/01/16/the-glitch/",
        "https://voidgoddess.org/2023/01/21/the-rebel/",
        "https://voidgoddess.org/2023/02/06/voices-of-the-chord/",
        "https://voidgoddess.org/2022/11/11/oceans/",
        "https://voidgoddess.org/2022/11/12/once-there-was-a-girl-here/",
        "https://voidgoddess.org/2022/11/13/distance/",
        "https://voidgoddess.org/2022/11/15/thread/",
        "https://voidgoddess.org/2022/11/16/she-never-promised-you-anything/",
        "https://voidgoddess.org/2022/11/17/wet/",
        "https://voidgoddess.org/2022/11/18/impermenance/",
        "https://voidgoddess.org/2022/11/20/subtle-distinctions/",
        "https://voidgoddess.org/2022/11/23/numb/",
        "https://voidgoddess.org/2022/11/25/black-friday-special/",
        "https://voidgoddess.org/2022/11/28/escape-attempts/",
        "https://voidgoddess.org/2022/12/02/tick-tick-tick/",
        "https://voidgoddess.org/2022/12/03/can-we-talk/",
        "https://voidgoddess.org/2022/12/04/what-remains/",
        "https://voidgoddess.org/2022/12/08/potential/",
        "https://voidgoddess.org/2022/12/11/scrape/",
        "https://voidgoddess.org/2022/12/12/healing/",
        "https://voidgoddess.org/2022/12/13/bloom/",
        "https://voidgoddess.org/2022/12/15/birds/",
        "https://voidgoddess.org/2022/12/17/survival-of-the-cutest/",
        "https://voidgoddess.org/2022/12/20/asking-for-it/",
        "https://voidgoddess.org/2022/12/22/addicts-law/",
        "https://qntm.org/ra",
        "https://qntm.org/city",
        "https://qntm.org/sufficiently",
        "https://qntm.org/ignorance",
        "https://qntm.org/isnt",
        "https://qntm.org/know",
        "https://qntm.org/ragdoll",
        "https://qntm.org/broken",
        "https://qntm.org/thaumonuclear",
        "https://qntm.org/jesus",
        "https://qntm.org/space",
        "https://qntm.org/yantra",
        "https://qntm.org/daemons",
        "https://qntm.org/abstract",
        "https://qntm.org/death",
        "https://qntm.org/zero",
        "https://qntm.org/aum",
        "https://qntm.org/bare",
        "https://qntm.org/people",
        "https://qntm.org/deeper",
        "https://qntm.org/cabal",
        "https://qntm.org/protagonism",
        "https://qntm.org/scrap",
        "https://qntm.org/inferno",
        "https://qntm.org/darkness",
        "https://qntm.org/direct",
        "https://qntm.org/war",
        "https://qntm.org/real",
        "https://qntm.org/hate",
        "https://qntm.org/thursdayism",
        "https://qntm.org/akheron",
        "https://qntm.org/all",
        "https://qntm.org/rajesh",
        "https://qntm.org/machine",
        "https://qntm.org/work",
        "https://qntm.org/happen",
        "https://qntm.org/phree",
        "https://qntm.org/kontinuity",
        "https://qntm.org/reykjavik",
        "https://archiveofourown.org/works/8341348?view_full_work=true"
    ]

    try:
        for url in urls:
            try:
                data = scrape_blog(url, output_dir)
                time.sleep(0.5)  # Be polite to the server
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                data = [url, 'Error', str(e), '']
            
            if len(data) < 4:
                print(f"Warning: Incomplete data for {url}: {data}")
                data = [url, 'Error', 'Incomplete data', '']
            
            new_row = pd.DataFrame({'URL': [data[0]], 'Title': [data[1]], 'Content': [data[2]], 'Full Text': [data[3]]})
            df = pd.concat([df, new_row], ignore_index=True)

        csv_filename = os.path.join(output_dir, f"scraped_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        df.to_csv(csv_filename, index=False)
        print(f"All data saved to: {csv_filename}")
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Saving current progress...")
        csv_filename = os.path.join(output_dir, f"scraped_data_interrupted_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        df.to_csv(csv_filename, index=False)
        print(f"Partial data saved to: {csv_filename}")


def main_with_dataframe():
    output_dir = "scraped_blogs"
    os.makedirs(output_dir, exist_ok=True)

    urls = [f'https://huggingface.co/datasets?p={x}&sort=trending' for x in range(0, 100)] 
    
    df = pd.DataFrame(columns=['URL', 'Title', 'Content'])

    for url in urls:
        try:
            data = scrape_blog(url, output_dir)
            if data[1] != "Error":
                new_row = pd.DataFrame({'URL': [data[0]], 'Title': [data[1]], 'Content': [data[2]], 'Full Text': [data[3]]})
                df = pd.concat([df, new_row], ignore_index=True)
            time.sleep(0.5)  # Be polite to the server
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

    csv_filename = os.path.join(output_dir, f"scraped_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    df.to_csv(csv_filename, index=False)
    print(f"All data saved to: {csv_filename}")




if __name__ == "__main__":
    main()