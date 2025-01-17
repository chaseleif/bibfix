#! /usr/bin/env python3

import os, re, sys
from argparse import ArgumentParser

class BibEntry:
  entrytypes = ['article','book','booklet','conference','inbook',
                'incollection','inproceedings','manual','masterthesis','misc',
                'phdthesis','proceedings','techreport','unpublished']
  fieldtypes = [
    'title',
    'author',
    'month',
    'year',
    'doi',
    'url',
    'issn',
    'isbn',
    'address',
    'annote',
    'booktitle',
    'chapter',
    'edition',
    'editor',
    'howpublished',
    'institution',
    'journal',
    'note',
    'number',
    'organization',
    'pages',
    'publisher',
    'school',
    'series',
    'type',
    'volume',
  ]
  def __init__(self, entrytype, citekey):
    self.notes = []
    self.entrytype = entrytype.lower()
    if self.entrytype not in BibEntry.entrytypes:
      self.entrytype = 'misc'
    self.citekey = citekey
    self.fields = {}
  def addfield(self, fieldtype, value):
    value = re.sub('{ ','{',value)
    value = re.sub(' }','}',value)
    while value.startswith('{') and value.endswith('}'):
      value = value[1:-1]
    value = value.strip()
    if value == '':
      return
    fieldtype = fieldtype.lower()
    if fieldtype not in BibEntry.fieldtypes:
      fieldtype = fieldtype.lstrip('%')
      self.notes.append(f'{fieldtype}={{{value}}},')
      return
    if fieldtype in self.fields:
      if self.fields[fieldtype].lower() != value.lower():
        self.notes.append(f'duplicate field: {fieldtype}={value}')
      return
    self.fields[fieldtype] = value
  def __eq__(self, other):
    if not isinstance(other, BibEntry):
      return False
    # even though different case citekeys are different,
    #  consider them the same as they would effectively be duplicates
    if self.citekey.lower() != other.citekey.lower():
      return False
    # all of other fields in self fields
    if all([key in self.fields for key in other.fields]):
      # all are equal
      if all([self.fields[key].lower() == other.fields[key].lower() \
              for key in other.fields]):
        return True
    # all of self fields in other fields
    elif all([key in other.fields for key in self.fields]):
      # all are equal
      if all([self.fields[key].lower() == other.fields[key].lower() \
              for key in self.fields]):
        return True
    return False
  def __str__(self):
    ret = ''
    if len(self.notes) > 0:
      ret += f'% {self.entrytype}{{{self.citekey}}}\n'
      for note in self.notes:
        ret += f'% {note}\n'
    ret += f'@{self.entrytype}{{{self.citekey},\n'
    for key in BibEntry.fieldtypes:
      if key in self.fields:
        ret += f'  {key}={{{self.fields[key]}}},\n'
    ret += '}\n'
    return ret

def fix(bibfilename, outprefix):
  with open(bibfilename, 'r') as infile:
    bibfile = infile.read().strip()
  bibfile = re.sub('[\r\n\t]',' ',bibfile)
  bibfile = re.sub('  +',' ',bibfile)
  top = re.compile('@ ?([^ {]+) ?{([^ ,]+) ?,')
  entries = {}
  print('Reading')
  while len(bibfile) > 1:
    if not top.match(bibfile):
      bibfile = bibfile[1:]
    if not bibfile.startswith('@'):
      bibfile = bibfile[bibfile.find('@'):]
      continue
    lstart = top.match(bibfile).span()[1]
    entry = BibEntry(*top.match(bibfile).groups())
    print(f'\r\x1b[1A\x1b[8C\x1b[0K@{entry.entrytype}{{{entry.citekey}')
    rstart = lstart
    if bibfile[rstart] == ' ':
      rstart += 1
    while bibfile[rstart:rstart+1] not in ['','}','@']:
      key = ''
      c = bibfile[rstart]
      while c not in [' ','=']:
        key += c
        rstart += 1
        c = bibfile[rstart]
      while bibfile[rstart] in [' ','=']:
        rstart += 1
      value = ''
      level = 0
      if bibfile[rstart] == '{':
        rstart += 1
        stopchars = ['}']
      elif bibfile[rstart] == '\"':
        rstart += 1
        stopchars = ['\"']
      else:
        stopchars = [',',' ','}']
      while level > 0 or bibfile[rstart] not in stopchars:
        value += bibfile[rstart]
        if bibfile[rstart] == '{':
          level += 1
        elif bibfile[rstart] == '}':
          level -= 1
        rstart += 1
      rstart += 1
      while bibfile[rstart] in [' ',',']:
        rstart += 1
      entry.addfield(key, value)
    bibfile = bibfile[rstart:]
    key = entry.citekey.lower()
    if key in entries:
      if not isinstance(entries[key], list):
        if entries[key] == entry:
          continue
        entries[key] = [entries[key]]
      elif any([entry==other for other in entries[key]]):
        continue
      entries[key].append(entry)
    else:
      entries[key] = entry
  print(f'\r\x1b[1A\x1b[0KDone reading {bibfilename}')
  keys = sorted(entries.keys())
  print(f'Creating {outprefix}.bib and {outprefix}_duplicates.bib')
  with open(f'{outprefix}.bib','w') as outfile:
    for key in keys:
      if isinstance(entries[key], list):
        continue
      outfile.write(str(entries[key]))
  with open(f'{outprefix}_duplicates.bib','w') as outfile:
    for key in keys:
      if not isinstance(entries[key], list):
        continue
      for entry in entries[key]:
        outfile.write(str(entry))

if __name__ == '__main__':
  parser = ArgumentParser(prog=sys.argv[0], description='Bibtex bib fixer')
  parser.add_argument('-i', '--input', default='main.bib',
                      metavar='<input file>', help='input bib file')
  parser.add_argument('-o', '--output', default='filtered',
                      metavar='<output prefix>', help='output file prefix')
  args = vars(parser.parse_args())
  if not os.path.isfile(args['input']):
    parser.print_help()
    parser.exit('Input file does not exist!')
  fix(args['input'], args['output'])

