import json
import requests
import os
from argparse import ArgumentParser
from lxml import etree as ET
from re import match, sub
from yaml import safe_load
from time import perf_counter

PAR_SEP = 'PaRaSeP'

def get_tei_locations(oai_base: str) -> dict:
    """Fetch TEI locations from OAI-PMH endpoint."""
    response = requests.get(f"{oai_base}?verb=ListRecords")
    tree = ET.fromstring(response.content)
    nsmap = {'dc': 'http://purl.org/dc/elements/1.1/'}
    ids = tree.xpath('//dc:identifier/text()', namespaces=nsmap)
    titles = tree.xpath('//dc:title/text()', namespaces=nsmap)
    return dict(zip(ids, titles))

def get_paragraph(node):
    """Get parent paragraph element."""
    while node is not None and node.tag != '{http://www.tei-c.org/ns/1.0}p' and node.tag != '{http://www.tei-c.org/ns/1.0}body':
        node = node.getparent()
    return node

def run_udp(text: str, lang: str, cfg: dict) -> str:
    """Process text through UDPipe API."""
    data = {
        'data': text,
        'model': cfg['models'][lang],
        'tokenizer': '',
        'tagger': '',
        'output': 'conllu'
    }
    
    response = requests.post(cfg['apiUrl'], files=data)
    result = response.json()['result']
    
    vertical = "<p>\n<s>\n"
    for line in result.split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 10:
            continue
            
        item = {
            'text': parts[1],
            'lemma': parts[2],
            'upos': parts[3]
        }
        
        if item['text'] == PAR_SEP:
            vertical += "</s>\n</p>\n<p>\n<s>\n"
        else:
            vertical += f"{item['text']}\t{item['lemma']}\t{item['upos']}\n"
            if 'SpaceAfter=No' in parts[9]:
                vertical += "<g/>\n"
                
    vertical += "</s>\n</p>\n"
    return vertical

def run_spacy(text: str, lang: str, cfg: dict) -> str:
    import spacy

    nlp = spacy.load(cfg['models'][lang])
    doc = nlp(text)
    assert doc.has_annotation("SENT_START")

    vertical = "<p>\n<s>\n"
    sent = None
    for token in doc:
        if token.is_space:
            continue

        # end of sentence recognition
        sent = sent or token.sent
        if sent != token.sent:
            vertical += '</s>\n<s>\n'
        sent = token.sent

        # check if the glue element is needed
        if not match('\\s', text) and token.is_punct:
            vertical += "<g/>\n"
        text = sub(f'^\\s*', '', text)
        text = text[len(token.text):]

        # token itself
        if token.text == PAR_SEP:
            vertical += "</s>\n</p>\n<p>\n<s>\n"
        else:
            vertical += f"{token.text}\t{token.lemma_ if not token.is_punct else token.text}\t{token.pos_}\n"

    vertical += "</s>\n</p>\n"
    return vertical

def create_vertical(corpora: dict, output_path: str, cfg: dict) -> dict:
    """Create vertical file and its config from corpus data."""

    corpora["vertical"] = output_path
    create_config(corpora, sub('[.][^.]+$', '', output_path), cfg)

    with open(output_path, 'w', encoding='utf-8') as vertical:
        vertical.write(f'<doc LandingPageURI="{corpora["landingPage"]}">\n')
        
        time = {'download': 0.0, 'process': 0.0, 'total': perf_counter(), 'tokens': 0}
        N = len(corpora['tei'])
        n = 1
        for tei_url, title in corpora['tei'].items():
            print(f'    {tei_url} ({n}/{N} {round(100 * n / N, 1)}%)')
            html_url = tei_url.replace('.xml', '.html')
            t1 = perf_counter()
            response = requests.get(tei_url)
            t2 = perf_counter()

            tei_content = response.text
            tei_content = tei_content.replace('<lb/>', ' ')
            
            tree = ET.fromstring(tei_content.encode('utf-8'))
            nsmap = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            vertical.write(f'<chapter ID="{corpora["id"]}" LandingPageURI="{html_url}">\n')
            
            last_p = None
            text = ''
            
            for element in tree.xpath(corpora['xpath'], namespaces=nsmap):
                part = element.replace("\n", ' ').replace("\r", ' ').strip()
                if part == '':
                    continue
                    
                p = get_paragraph(element.getparent())
                if last_p is None:
                    last_p = p
                if p != last_p:
                    text += f' {PAR_SEP} '
                    last_p = p
                text += part + " "
        
            t3 = perf_counter()
            if cfg['backend'] == 'udppipe':
                processed = run_udp(text.strip(), corpora['lang'], cfg['udppipe'])
            else:
                processed = run_spacy(text.strip(), corpora['lang'], cfg['spacy'])
            t4 = perf_counter()
            tokens = processed.count('\n')

            vertical.write(processed.replace("<s>\n</s>\n", '').replace("<p>\n</p>\n", ''))
            vertical.write("</chapter>\n")
            
            t5 = perf_counter()
            time['download'] += t2 - t1
            time['process']  += t4 - t3
            time['tokens'] += tokens
            print(f'        dwnld {round(t2 - t1, 2)}s nlp {round(t4 - t3, 2)}s total {round(t5 - t1, 2)}s tokens {tokens}')
            n += 1
            
        vertical.write("</doc>\n")

        time['total'] = perf_counter() - time['total']
        time = {k: round(v, 2) for k, v in time.items()}
        print(f'    {time}')

def create_config(corpora: dict, output_path: str, cfg: dict) -> None:
    with open(output_path, 'w') as f:
        # variable part
        f.write(f'MAINTAINER "{cfg["maintainer"]}"\n')
        f.write(f'INFO "{corpora["id"]}"\n')
        f.write(f'NAME "{corpora["id"]}"\n')
        f.write(f'INFOHREF "{corpora["landingPage"]}"\n')
        f.write(f'PATH "{os.path.join(cfg["basePath"]["data"], corpora["id"])}"\n')
        f.write(f'LANGUAGE "{cfg["langMap"][corpora["lang"]]}"\n')
        f.write(f'VERTICAL "{os.path.join(cfg["basePath"]["vertical"], os.path.basename(corpora["vertical"]))}"\n')
        # constant part
        f.write('''
ENCODING "UTF-8"

ATTRIBUTE word

ATTRIBUTE lemma

ATTRIBUTE pos

ATTRIBUTE lc {
	DYNAMIC    utf8lowercase
	DYNLIB     internal
	ARG1       "C"
	FUNTYPE    s
	FROMATTR   word
	TYPE       index
	TRANSQUERY yes
}

STRUCTURE doc {
    ATTRIBUTE LandingPageURI
}

STRUCTURE chapter {
	ATTRIBUTE ID
    ATTRIBUTE LandingPageURI
}

STRUCTURE p

STRUCTURE s

STRUCTURE g {
   DISPLAYTAG 0
   DISPLAYBEGIN "_EMPTY_"
}
''')

def main():
    """Main function to process all endpoints."""

    parser = ArgumentParser('Create (No)Sketch Engine verticals from dse-static digital editions')
    parser.add_argument('-l', action='store_true', help='list all availble editions')
    parser.add_argument('-c', default='config.yaml', help='config file to use (default config.yaml)')
    parser.add_argument('-e', help='if specified, processes only single digital edition with a specified key')
    args = parser.parse_args()

    with open(args.c, 'r') as f:
        cfg = safe_load(f)
    response = requests.get(cfg['src'])
    src_data = response.json()['endpoints']

    if args.l:
        for key in src_data.keys():
            print(key)
        return
   
    os.makedirs(cfg['outputDir'], exist_ok=True)

    for key, val in src_data.items():
        if args.e and key != args.e:
            continue

        key = sub('[^a-zA-Z0-9]', '', key)
        teis = get_tei_locations(val['oai'])
        corpora = {
            'id': key,
            'tei': teis,
            'xpath': val['fulltext_xpath'],
            'landingPage': sub('/[^/]*/?$', '', next(iter(teis.keys()))),
            'lang': val['default_lang']
        }
        print(f"{key}: {corpora['lang']} {len(corpora['tei'])}")
        
        create_vertical(corpora, os.path.join(cfg['outputDir'], f"{key}.vrt"), cfg)

if __name__ == "__main__":
    main()
