from argparse import ArgumentParser
from create_verticals import create_config, create_mquery_sru_config, run_spacy, run_udp
from csv import reader
from os import makedirs
from os.path import basename, join
from re import sub
from yaml import safe_load
from time import perf_counter

GLUE = '<g/>'
PAR_SEP = 'PaRaSeP'


def reprocess(input, output, lang, cfg) -> bool:
    time = {'nlp': 0.0, 'total': perf_counter(), 'tokens': 0}

    tagsP = cfg['tags']['paragraph']
    tagsC = cfg['tags']['chapter']

    output.write(f'<doc>\n')

    chapter = ''
    glue = False
    t1 = perf_counter()
    for row in input:
        if len(row) == 0:
            continue

        text = row[0]
        if text == GLUE:
            glue = True
        elif text.startswith('<'):
            tag = sub('[ /].*$', '', text[1:])
            if tag in tagsC:
                t2 = perf_counter()
                if cfg['backend'] == 'udppipe':
                    processed = run_udp(chapter, lang, cfg['udppipe'])
                else:
                    processed = run_spacy(chapter, lang, cfg['spacy'])
                t3 = perf_counter()

                output.write("<chapter>\n")
                output.write(processed.replace("<s>\n</s>\n", '').replace("<p>\n</p>\n", '').replace("<chapter>\n</chapter>\n", ''))
                output.write("</chapter>\n")
                    
                tokens = processed.count('\n')
                time['nlp']  += t3 - t2
                time['tokens'] += tokens
                print(f'    nlp {round(t3 - t2, 2)}s total {round(t3 - t1, 2)}s tokens {tokens}')

                t1 = perf_counter()
                chapter = ''
                glue = False
            elif tag in tagsP:
                chapter += f' {PAR_SEP} '
        else:
            if glue:
                chapter += ' '
            chapter += text
    
    output.write('</doc>\n')
    time['total'] = perf_counter() - time['total']
    time = {k: round(v, 2) for k, v in time.items()}
    print(f'{time}')
    return True

def main():
    parser = ArgumentParser('Reprocess a vertical')
    parser.add_argument('vertical', help='path to the vertical file')
    parser.add_argument('-c', default='config.yaml', help='config file to use (default config.yaml)')
    parser.add_argument('--co', action='store_true', help='create only the config file - useful if only the corpora configuration file template was changed')
    args = parser.parse_args()

    with open(args.c, 'r') as f:
        cfg = safe_load(f)

    makedirs(cfg['outputDir'], exist_ok=True)

    path_vertical = join(cfg['outputDir'], basename(args.vertical))
    path_config = sub('[.][^.]+$', '', path_vertical)

    with open(args.vertical) as infile:
        r = reader(infile, delimiter="\t")
        lang = next(r)[0]

        corpora = {
            'id': basename(path_config),
            'title': basename(path_config),
            'pid': '',
            'landingPage': '',
            'lang': lang,
            'vertical': path_vertical
        }

        create_config(corpora, path_config, cfg)
        create_mquery_sru_config(corpora, f'{path_config}.yml', cfg)


        if not args.co:
            for i in range(10):
                with open(join(cfg['outputDir'], basename(args.vertical)), 'w') as outfile:
                    print(f'{args.vertical} {lang}')
                    try:
                        if reprocess(r, outfile, lang, cfg):
                            break
                    except Exception as e:
                        print(f'{e}')
                sleep(5)

if __name__ == "__main__":
    main()
