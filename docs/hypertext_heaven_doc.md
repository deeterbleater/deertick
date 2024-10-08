Here's an API reference document that explains the features of the `hypertext_heaven.py` file and how to use them:

# Hypertext Heaven API Reference

## Overview

The Hypertext Heaven module provides a `Heaven` class that automates the process of creating webpages using various AI agents. It generates HTML, CSS, and JavaScript code, and can even create images based on the webpage content.

## Class: Heaven

### Initialization

```python
heaven = Heaven()
```

Creates a new `Heaven` instance, initializing several AI agents for different tasks.

### Methods

#### create_webpage(idea, previous_page=None)

Creates a complete webpage based on a given idea.

- Parameters:
  - `idea` (str): The concept or idea for the webpage.
  - `previous_page` (str, optional): HTML content of a previous version to iterate upon.

- Usage:
  ```python
  heaven = Heaven()
  heaven.create_webpage("A portfolio website for a digital artist")
  ```

### Private Methods

These methods are used internally by `create_webpage()` but can be called separately if needed:

#### _generate_outline(idea, previous_page)

Generates a detailed outline for the webpage.

#### _build_html_structure(outline)

Creates the HTML structure based on the outline.

#### _create_css(outline, html_structure)

Generates CSS for the webpage.

#### _build_javascript(outline, html_structure)

Creates JavaScript for the webpage's functionality.

#### _combine_format_validate(html_structure, css, js)

Combines HTML, CSS, and JavaScript into a single, valid HTML file.

#### _save_page(final_page)

Saves the final webpage, generating images for `<img>` tags and CSS background images.

## AI Agents

The `Heaven` class uses several AI agents for different tasks:

- `agent_405b`: Uses "Meta: Llama 3.1 405B Instruct" model for generating outlines.
- `agent_sonnet`: Uses "Anthropic: Claude 3.5 Sonnet" model for HTML and CSS generation.
- `agent_opus`: Uses "Anthropic: Claude 3 Opus" model for JavaScript generation and final combination.
- `agent_gpt4o`: Uses "gpt-4o-mini-or" model for generating image descriptions.
- `agent_flux`: Uses "flux-dev" model for generating images.

## Image Generation

The `_save_page()` method automatically generates images for:
- All `<img>` tags in the HTML.
- All background images specified in the CSS.

It uses `agent_gpt4o` to create descriptions and `agent_flux` to generate the actual images.

## Command-line Usage

The script can be run from the command line:

```
python hypertext_heaven.py <idea> [previous_page]
```

- `<idea>`: Required. The concept for the webpage.
- `[previous_page]`: Optional. Path to an HTML file of a previous version to iterate upon.

## Example

```python
from hypertext_heaven import Heaven

heaven = Heaven()
heaven.create_webpage("A responsive landing page for a tech startup")
```

This will generate a complete HTML file with embedded CSS and JavaScript, along with any necessary images, saved in the current directory.

## Notes

- The generated webpage is designed to run locally without external dependencies.
- Image generation may fail silently if there are any errors.
- The script requires an active internet connection to communicate with the AI models.

@Deertick can use this API to automate the creation of webpages, including content, structure, styling, functionality, and even images, all driven by AI.