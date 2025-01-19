# bibfix
A fix-utility for BIbtex .bib files

## Usage
```bash
$ python bibfix.py main.bib
```
or
```bash
$ python bibfix.py --help
usage: bibfix.py [-h] [-i <input file>] [-o <output prefix>]

Bibtex bib fixer

options:
  -h, --help            show this help message and exit
  -i, --input <input file>
                        input bib file
  -o, --output <output prefix>
                        output file prefix
```

## Notes
- The bib file should be mostly correct
- There is a prompt to confirm possible entries which would be invalid
  - Choose yes if these entries are an invalid entry start
  - Choose no if this was found, e.g., because of an @ symbol in an email address
- Text between entries of the input (comments between entries) is discarded
- Entries with an invalid/non-standard entry-type will become 'misc' type
- Non-standard fields will be printed as comments above the entry
- Entries that are not terminated will be notified as incomplete
- Notifications will also be printed for empty entries
- Files created: `outputprefix.bib` and `outputprefix_duplicates.bib`
- Output entries and duplicate entries are sorted alphabetically by their cite-key
- The duplication check is case-insensitive, the cite-key `bibtex` is equal to `BibTex`
- If 2 entries are duplicates but contain the same values, the later one is discarded
- An entry with duplicates will "absorb" extra fields from later entries
