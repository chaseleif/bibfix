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
    value = value.strip()
    while value.startswith('{') and value.endswith('}'):
      value = value[1:-1]
    if value == '':
      return
    fieldtype = fieldtype.lower().lstrip('%/ ')
    if fieldtype not in BibEntry.fieldtypes:
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
      if all([re.sub('[{}]','',self.fields[key].lower()) == \
              re.sub('[{}]','',other.fields[key].lower()) \
              for key in other.fields]):
        return True
    # all of self fields in other fields
    elif all([key in other.fields for key in self.fields]):
      # all are equal
      if all([re.sub('[{}]','',self.fields[key].lower()) == \
              re.sub('[{}]','',other.fields[key].lower()) \
              for key in self.fields]):
        self.fields.update(other.fields)
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
  top = re.compile('@ ?([^ {]+) ?{ ?([^ ,]+) ?,')
  starts = []
  i = bibfile.find('@')
  count = 0
  while i >= 0:
    if top.match(bibfile[i:]):
      starts.append(i)
      count += 1
    else:
      print(bibfile[i:i+50])
      choice = input('Is this an invalid entry? [Y/n] ')
      print(f'\r\x1b[2A\x1b[0K',end='')
      if not choice.lower().startswith('n'):
        print(f'Ignoring invalid entry {bibfile[i:i+50]}')
        starts.append(i)
      print('\x1b[0K',end='')
    i = bibfile.find('@',i+1)
  entries = {}
  print(f'Found {count} possible entries')
  print('Reading')
  for starti in range(len(starts)):
    if not top.match(bibfile[starts[starti]:]):
      continue
    nextstart = len(bibfile) if starti+1==len(starts) else starts[starti+1]
    i = top.match(bibfile[starts[starti]:]).span()[1] + starts[starti]
    entry = BibEntry(*top.match(bibfile[starts[starti]:]).groups())
    print(f'\r\x1b[1A\x1b[8C\x1b[0K@{entry.entrytype}{{{entry.citekey}')
    if bibfile[i] == ' ':
      i += 1
    while i < nextstart and bibfile[i] not in ['}','@']:
      key = ''
      while i < nextstart and bibfile[i] not in [' ','=']:
        key += bibfile[i]
        i += 1
      while i < nextstart and bibfile[i] in [' ','=']:
        i += 1
      value = ''
      level = 0
      if i == nextstart:
        pass
      elif bibfile[i] == '{':
        i += 1
        stopchars = ['}']
      elif bibfile[i] == '\"':
        i += 1
        stopchars = ['\"']
      else:
        stopchars = [',',' ','}']
      while i < nextstart and (level > 0 or bibfile[i] not in stopchars):
        value += bibfile[i]
        if bibfile[i] == '{':
          level += 1
        elif bibfile[i] == '}':
          level -= 1
        i += 1
      if i < nextstart:
        i += 1
      while i < nextstart and bibfile[i] in [' ',',']:
        i += 1
      entry.addfield(key, value)
    if i == nextstart:
      print(f'\r\x1b[1A\x1b[0K@{entry.entrytype}{{{entry.citekey}}} incomplete')
      print('Reading')
      continue
    if len(entry.fields) == 0:
      print(f'\r\x1b[1A\x1b[0K@{entry.entrytype}{{{entry.citekey}}} is empty')
      print('Reading')
      continue
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
  print(f'Creating output files')
  count = 0
  with open(f'{outprefix}.bib','w') as outfile:
    for key in keys:
      if isinstance(entries[key], list):
        continue
      count += 1
      outfile.write(str(entries[key]))
  if count == 0:
    print(f'No unique entries to write to {outprefix}.bib')
    os.unlink(f'{outprefix}.bib')
  else:
    print(f'Created {outprefix}.bib with {count} unique entries')
  uniqcount, count = 0, 0
  with open(f'{outprefix}_duplicates.bib','w') as outfile:
    for key in keys:
      if not isinstance(entries[key], list):
        continue
      uniqcount += 1
      for entry in entries[key]:
        outfile.write(str(entry))
        count += 1
  if count == 0:
    print(f'No duplicate entries to write to {outprefix}_duplicates.bib')
    os.unlink(f'{outprefix}_duplicates.bib')
  else:
    print(f'Created {outprefix}_duplicates.bib',
          f'with {uniqcount} unique keys and {count} total entries')

if __name__ == '__main__':
  if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
    args = {'input':sys.argv[1],'output':'filtered'}
  else:
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

