# fman duplicate file and increment index extension
duplicate the currently selected file from [FMan](https://www.fman.io) with ctrl+d and increment the index

![plot](./media/demo.gif)

# Install
install the plugin by copying the release to 
> %AppData%\Roaming\fman\Plugins\User

Or just use the "install plugin" function from within fman and search for FManDuplicateFilesAndIncrementExtension.

# Usage
Select one or more files and press ctrl+d

The files will be copied and the file index will be incremented.

The plugin intelligently detects and increments numbers in various filename patterns:

## Supported Patterns

### 1. Files ending with numbers (no underscore required)
- `Folie8.jpg` → `Folie9.jpg`
- `Folie08.jpg` → `Folie09.jpg` (preserves leading zeros)
- `Photo123.png` → `Photo124.png`

### 2. Files with underscore + number
- `test_1.jpg` → `test_2.jpg`
- `test_0000001.txt` → `test_0000002.txt`

### 3. Files with version patterns
- `document_v3.pdf` → `document_v4.pdf`
- `file_v03.txt` → `file_v04.txt` (preserves leading zeros)
- `report_V2.docx` → `report_V3.docx` (preserves case)

### 4. Files starting with numbers
- `01_test.jpg` → `02_test.jpg` (with underscore)
- `01test.jpg` → `02test.jpg` (without underscore)
- `001_document.txt` → `002_document.txt` (preserves leading zeros)
- `09_file.pdf` → `10_file.pdf` (handles padding correctly)

**Note:** Trailing numbers take priority over leading numbers. For example:
- `01_test_05.jpg` → `01_test_06.jpg` (increments the trailing 05, not the leading 01)

### 5. Files without numbers
- `document.txt` → `document_copy.txt`

## Multiple File Selection

When selecting multiple files, the plugin intelligently handles naming conflicts by finding the next available filenames starting from the highest number in the selection.

### How it works:
1. Groups selected files by their base pattern
2. Finds the highest number within each group
3. Assigns sequential available filenames starting from `highest + 1`
4. Checks the directory for existing files to avoid any collisions

### Examples:

**Basic multiple selection:**
- Select: `Folie7.jpg`, `Folie8.jpg`
- Result: `Folie7.jpg` → `Folie9.jpg`, `Folie8.jpg` → `Folie10.jpg`
- *Both files are duplicated starting from the next available number after the highest (8)*

**With gaps in existing files:**
- Existing files: `Folie8.jpg`, `Folie11.jpg`
- Select: `Folie7.jpg`, `Folie8.jpg`
- Result: `Folie7.jpg` → `Folie9.jpg`, `Folie8.jpg` → `Folie10.jpg`
- *Skips Folie11 since it already exists*

**Mixed patterns in selection:**
- Select: `Photo5.jpg`, `Photo7.jpg`, `Document_v2.txt`
- Result: `Photo5.jpg` → `Photo8.jpg`, `Photo7.jpg` → `Photo9.jpg`, `Document_v2.txt` → `Document_v3.txt`
- *Each pattern group is handled independently*

**Non-sequential selection:**
- Select: `Folie3.jpg`, `Folie5.jpg`, `Folie9.jpg`
- Result: `Folie3.jpg` → `Folie10.jpg`, `Folie5.jpg` → `Folie11.jpg`, `Folie9.jpg` → `Folie12.jpg`
- *All duplicates start from 10 (highest number 9 + 1)*

**Leading numbers work too:**
- Select: `01_test.jpg`, `02_test.jpg`, `03_test.jpg`
- Result: `01_test.jpg` → `04_test.jpg`, `02_test.jpg` → `05_test.jpg`, `03_test.jpg` → `06_test.jpg`
- *All duplicates start from 04 (highest number 03 + 1)*

Files that already exist will not be overwritten. You'll receive an alert if a target filename already exists.







