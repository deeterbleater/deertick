# DatasetGenerator API Reference

## Class: DatasetGenerator

The `DatasetGenerator` class provides methods for creating datasets from various input sources such as folders containing text files, tabular files (CSV, Excel, JSON, HTML, XML), or individual text files. It also supports uploading datasets to Hugging Face.

### Constructor

#### `__init__(self, input_path=None, text_column=None, hf_repo_name=None, hf_token=None)`

Initializes a new instance of the DatasetGenerator class.

**Parameters:**
- `input_path` (str, optional): Path to the input directory or file.
- `text_column` (str, optional): Name of the text column for tabular files.
- `hf_repo_name` (str, optional): Name of the Hugging Face repository to upload to.
- `hf_token` (str, optional): Hugging Face API token.

**Returns:** None

**Example:**
```python
generator = DatasetGenerator("path/to/input", text_column="content", hf_repo_name="my-dataset", hf_token="hf_api_token")
```

### Methods

#### `handle_error(self, error_message, exception=None)`

Handles errors by logging them and optionally raising an exception.

**Parameters:**
- `error_message` (str): The error message to log.
- `exception` (Exception, optional): The exception to raise.

**Returns:** None

#### `read_file(self, file_path)`

Reads the content of a file.

**Parameters:**
- `file_path` (str): The path to the file to be read.

**Returns:**
- str: The content of the file.

**Example:**
```python
content = generator.read_file("path/to/file.txt")
```

#### `parse_content(self, content)`

Parses the content of a file into paragraphs.

**Parameters:**
- `content` (str): The content to be parsed.

**Returns:**
- list: A list of dictionaries, each containing a 'text' key with a paragraph as its value.

**Example:**
```python
paragraphs = generator.parse_content("This is paragraph 1.\n\nThis is paragraph 2.")
```

#### `create_dataset_from_folder(self, folder_path)`

Creates a dataset from a folder containing text and tabular files.

**Parameters:**
- `folder_path` (str): The path to the folder containing the files.

**Returns:**
- Dataset: A Hugging Face Dataset object containing the parsed content of all files in the folder.

**Example:**
```python
dataset = generator.create_dataset_from_folder("path/to/folder")
```

#### `is_tabular_file(self, filename)`

Checks if a file is a supported tabular format.

**Parameters:**
- `filename` (str): The name of the file to check.

**Returns:**
- bool: True if the file is a supported tabular format, False otherwise.

#### `read_tabular_file(self, file_path)`

Reads a tabular file using pandas.

**Parameters:**
- `file_path` (str): The path to the tabular file.

**Returns:**
- pandas.DataFrame: The content of the tabular file as a DataFrame.

#### `process_dataframe(self, df)`

Processes a DataFrame to extract text data or convert it to a list of dictionaries.

**Parameters:**
- `df` (pandas.DataFrame): The DataFrame to process.

**Returns:**
- list: A list of dictionaries containing the processed data.

#### `create_dataset_from_tabular(self, file_path)`

Creates a dataset from a single tabular file.

**Parameters:**
- `file_path` (str): The path to the tabular file.

**Returns:**
- Dataset: A Hugging Face Dataset object containing the processed data from the tabular file.

**Example:**
```python
dataset = generator.create_dataset_from_tabular("path/to/file.csv")
```

#### `save_dataset(self, output_file=None)`

Saves the dataset to disk.

**Parameters:**
- `output_file` (str, optional): The path where the dataset should be saved. If not provided, uses the default output file.

**Returns:** None

**Example:**
```python
generator.save_dataset("path/to/output.arrow")
```

#### `process_input(self, upload_to_hf=False)`

Processes the input based on its type (folder, tabular file, or text file), creates a dataset, and optionally uploads it to Hugging Face.

**Parameters:**
- `upload_to_hf` (bool, optional): Whether to upload the dataset to Hugging Face. Default is False.

**Returns:** None

**Example:**
```python
generator.process_input(upload_to_hf=True)
```

#### `upload_to_huggingface(self)`

Uploads the dataset to Hugging Face.

**Parameters:** None

**Returns:** None

**Example:**
```python
generator.upload_to_huggingface()
```

## Command-line Usage

The script can be run from the command line with the following arguments:

- `input_path`: Path to the input directory or file (required)
- `--text_column`: Name of the text column for tabular files (optional)
- `--upload_to_hf`: Flag to upload the dataset to Hugging Face (optional)
- `--hf_repo_name`: Name of the Hugging Face repository to upload to (required if --upload_to_hf is used)
- `--hf_token`: Hugging Face API token (required if --upload_to_hf is used)

**Examples:**

1. For a directory of mixed files (text and tabular):
   ```
   python data_set_gen.py path/to/directory --text_column content
   ```

2. For a tabular file:
   ```
   python data_set_gen.py path/to/file.csv --text_column column_name
   ```

3. For a single text file:
   ```
   python data_set_gen.py path/to/file.txt
   ```

4. To upload the dataset to Hugging Face:
   ```
   python data_set_gen.py path/to/input --text_column content --upload_to_hf --hf_repo_name my-dataset --hf_token hf_api_token
   ```