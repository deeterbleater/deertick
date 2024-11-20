import { Agent } from './agent';
import { listAll, fileRead, modelByName } from './modelData';
import { program } from 'commander';

program
  .name('deertick')
  .description('DeerTick: A Multi-Provider Language Model Interface')
  .version('1.0.0');

program
  .option('-m, --model <model>', 'Specify the model to use', 'Meta: Llama 3.1 405B (base)')
  .option('-p, --provider <provider>', 'Specify the provider', 'openrouter')
  .option('-s, --system <prompt>', 'Set the system prompt for the conversation', '')
  .option('-i, --interactive', 'Start an interactive chat session')
  .option('-f, --file <path d="">', 'Read input from a file')
  .option('-o, --output <path d="">', 'Write output to a file')
  .option('-l, --list', 'List available models and providers')
  .option('--crawl <url>', 'Start a web crawl from the specified URL')
  .option('--scrape <url>', 'Scrape content from the specified URL')
  .option('--deep-analysis', 'Perform deep analysis during web crawling')
  .option('--export-db', 'Export scraped data to the database')
  .option('--backup-db', 'Create a backup of the entire database')
  .option('--discord', 'Start the Discord bot')
  .option('--generate-image <prompt>', 'Generate an image based on the given prompt')
  .option('--tts <text>', 'Convert the given text to speech')
  .option('--voice <name>', 'Specify the voice to use for text-to-speech')
  .option('--create-agent <name>', 'Create a new agent with the specified name')
  .option('--delete-agent <name>', 'Delete the agent with the specified name')
  .option('--agent-info <name>', 'Display information about the specified agent')
  .option('--set-param <agent> <param name="" value=""> <value>', 'Set a parameter for the specified agent')
  .option('--list-agents', 'List all available agents');

program.parse();

const options = program.opts();
const model = modelByName(options.model);
if (!model) {
  console.error('Invalid model specified');
  process.exit(1);
}

const agent = new Agent(model.id, options.system, options.provider);

async function main() {
  if (options.list) {
    listAll();
  } else if (options.interactive) {
    if (model.type !== "llm" && options.provider === "openrouter") {
      console.error("Openrouter only works with llm models, please choose another provider.");
      process.exit(1);
    }
    
    if (model.incompatible.includes(options.provider)) {
      console.error("The provider you have chosen is currently incompatible with this model. Please consider asking in the deerTick discord for more information.");
      process.exit(1);
    }

    const { TerminalChat } = await import('./terminalChat');
    await new TerminalChat(agent).chat("");
  } else if (options.file) {
    const response = await agent.generateResponse(options.system, fileRead(options.file));
    if (options.output) {
      const fs = await import('fs/promises');
      await fs.writeFile(options.output, response, 'utf-8');
    } else {
      console.log(`Agent: ${response}`);
    }
  }
  // Add other command implementations here
}

main().catch(console.error);
