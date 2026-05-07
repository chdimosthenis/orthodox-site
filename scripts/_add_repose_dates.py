"""
Add reposeYear and reposeLabel to every Greek saint's frontmatter.

reposeYear: integer used for chronological sort. NEGATIVE for BC.
reposeLabel: human-readable display (e.g. "9ος αἰὼν π.Χ.", "†1809").

Rules of thumb when an exact year is uncertain:
  - OT figures: BC century, year = -century*100 + 50, label "Xος αἰὼν π.Χ."
  - 1st-century apostles: ~60-100 AD, label "1ος αἰών" or "†c. YYYY"
  - Unknown medieval: estimate from century, year = century*100 + 50,
    label "X' αἰών" (Greek numeral century).

Run from repo root:  python scripts/_add_repose_dates.py
"""
import os, re, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SAINTS_DIR = os.path.join('src', 'content', 'saints')

# Lookup table: slug -> (reposeYear, reposeLabel, confidence)
# confidence: 'known' (well-attested year) | 'estimate' (century-level only)
DATA = {
    # === Old Testament prophets ===
    'profitis-elias':                 (-850, '9ος αἰὼν π.Χ.',          'estimate'),  # 9th c. BC
    'profitis-mosis':                 (-1250, '13ος αἰὼν π.Χ.',        'estimate'),  # ~13th c. BC

    # === New Testament apostles & evangelists (1st century) ===
    'agios-andreas-protoklitos':      (60,  '†c. 60',                   'known'),    # martyred Patras ~60-70
    'agioi-petros-pavlos':            (67,  '†c. 67',                   'known'),    # Peter & Paul Rome ~64-67
    'agios-iakovos-tou-zevedaiou':    (44,  '†44',                      'known'),    # Acts 12:1-2 ~44
    'agios-iakovos-adelfotheos':      (62,  '†c. 62',                   'known'),    # Josephus, Antiquities
    'agios-fillipos-apostolos':       (80,  '†c. 80',                   'estimate'), # Hierapolis tradition
    'agios-vartholomeos-apostolos':   (68,  '†c. 68',                   'estimate'), # Armenia tradition
    'agios-thomas-apostolos':         (72,  '†c. 72',                   'known'),    # Mylapore tradition
    'agios-mattheos-evangelistis':    (80,  '†c. 80',                   'estimate'), # 1st c.
    'agios-markos-evangelistis':      (68,  '†c. 68',                   'known'),    # Alexandria
    'agios-loukas-evangelistis':      (84,  '†c. 84',                   'estimate'), # Boeotia tradition
    'agios-iohannis-theologos':       (100, '†c. 100',                  'known'),    # Ephesus
    'agios-iohannis-prodromos':       (32,  '†c. 32',                   'known'),    # Beheading, Gospel acc.
    'agios-stefanos-protomartyras':   (34,  '†c. 34',                   'known'),    # Acts 7
    'agios-dionysios-areopagitis':    (96,  '†c. 96',                   'estimate'), # 1st c. Athens
    'agios-lazaros-tetraimeros':      (63,  '†c. 63',                   'estimate'), # Cyprus tradition
    'agioi-iohakeim-anna':            (1,   '1ος αἰὼν',                 'estimate'), # parents of Theotokos
    'agia-foteini-samaritis':         (66,  '†c. 66',                   'estimate'), # 1st c. martyr

    # === 2nd-3rd century martyrs & fathers ===
    'agios-ignatios-antiocheias':     (107, '†c. 107',                  'known'),    # Rome under Trajan
    'agios-polykarpos':               (155, '†155',                     'known'),    # Smyrna 155/156
    'agia-sofia-pisteos-elpidos-agapis': (137, '†c. 137',               'estimate'), # Hadrian era
    'agios-charalampos':              (202, '†202',                     'known'),    # Magnesia under Severus
    'agios-fanourios':                (300, '4ος αἰὼν',                 'estimate'), # uncertain, late
    'agia-eirini-megalomartys':       (304, '†c. 304',                  'estimate'), # Diocletian
    'agios-eustathios-plakidas':      (118, '†c. 118',                  'estimate'), # under Hadrian
    'agios-prokopios':                (303, '†303',                     'known'),    # Caesarea, Diocletian
    'agios-georgios':                 (303, '†303',                     'known'),    # Diocletian
    'agios-dhimitrios':               (306, '†306',                     'known'),    # Thessaloniki, Galerius
    'agia-varvara':                   (306, '†c. 306',                  'known'),    # Diocletian/Maximian
    'agios-pantelehmon':              (305, '†305',                     'known'),    # Nicomedia
    'agia-aikaterini':                (305, '†c. 305',                  'known'),    # Alexandria, Maxentius
    'agia-marina':                    (304, '†c. 304',                  'estimate'), # Antioch tradition
    'agia-paraskevi':                 (140, '†c. 140',                  'estimate'), # Antoninus Pius era
    'agios-minas':                    (296, '†296',                     'known'),    # Egypt, Diocletian
    'agioi-anargyroi-kosmas-damianos': (287, '†c. 287',                 'estimate'), # 3rd c.
    'agios-stylianos-paflagon':       (550, '6ος αἰὼν',                 'estimate'), # Paphlagonia
    'agios-alexios-anthropos-theou':  (411, '†c. 411',                  'estimate'), # Rome under Honorius

    # === 4th century: Council of Nicaea era + Cappadocians ===
    'agios-nikolaos':                 (343, '†c. 343',                  'known'),    # Myra
    'agios-spyridon':                 (348, '†c. 348',                  'known'),    # Trimythous
    'agioi-konstantinos-eleni':       (337, '†337',                     'known'),    # Helena 330, Constantine 337
    'agios-vasileios':                (379, '†379',                     'known'),    # Caesarea
    'agios-grigorios-theologos':      (390, '†c. 390',                  'known'),    # Nazianzus
    'agios-iohannis-chrysostomos':    (407, '†407',                     'known'),    # Komana
    'agios-athanasios-alexandreias':  (373, '†373',                     'known'),    # Alexandria
    'agios-antonios-megas':           (356, '†356',                     'known'),    # Egypt desert
    'agios-pachomios-megas':          (348, '†348',                     'known'),    # Tabennese
    'agios-efthymios-megas':          (473, '†473',                     'known'),    # Palestine
    'agios-symeon-stylitis':          (459, '†459',                     'known'),    # Aleppo
    'agios-theodoros-stratilatis':    (319, '†319',                     'known'),    # Heraclea
    'agioi-saranta-martyres-sevasteias': (320, '†320',                  'known'),    # Sebaste, Lake of
    'agia-xeni-roma':                 (450, '5ος αἰὼν',                 'estimate'), # Rome→Mylasa, 5th c.

    # === 5-6th century ===
    'agia-maria-aigyptia':            (522, '†c. 522',                  'known'),    # Egypt desert ~522
    'agios-neilos-sinaitis':          (430, '†c. 430',                  'estimate'), # Sinai
    'agios-david-evvoeus':            (1589, '†1589',                   'known'),    # actually 16th c. — Limni
    # NOTE: Δαβίδ Ευβοίας is 16th c. (1519-1589). Re-checked: yes, 1589.

    # === 7th century ===
    'agios-maximos-omologitis':       (662, '†662',                     'known'),    # Lazika

    # === 8-9th century ===
    'agios-fotios-megas':             (893, '†893',                     'known'),    # Constantinople

    # === 9-10th century Slavic mission era ===
    'agia-olga-isapostolos':          (969, '†969',                     'known'),    # Kiev
    'agios-vladimiros-isapostolos':   (1015, '†1015',                   'known'),    # Kiev

    # === 11-13th century ===
    'agios-iohannis-kalyvitis':       (450, '5ος αἰὼν',                 'estimate'), # actually 5th c.! Constantinople
    'agios-sergios-radonez':          (1392, '†1392',                   'known'),    # Russia
    'grigorios-palamas':              (1359, '†1359',                   'known'),    # Thessaloniki

    # === Iconic Byzantine figures (placed as best estimate) ===
    'agios-iakovos-tsalikis':         (1991, '†1991',                   'known'),    # Evvia (Osios Iakovos)
    'agios-amfilochios-patmou':       (1970, '†1970',                   'known'),    # Patmos
    'agia-anthimi-chiou':             (1856, '†1856',                   'known'),    # Chios

    # === Post-Byzantine / Ottoman era ===
    'agia-filothei-athinaia':         (1589, '†1589',                   'known'),    # Athens
    'agios-dionysios-zakynthou':      (1622, '†1622',                   'known'),    # Zakynthos
    'agios-gerasimos-kefallinias':    (1579, '†1579',                   'known'),    # Kefalonia
    'agios-kosmas-aitolos':           (1779, '†1779',                   'known'),    # Albania
    'agios-nikodimos-agioritis':      (1809, '†1809',                   'known'),    # Athos
    'agioi-rafail-nikolaos-eirini':   (1463, '†1463',                   'known'),    # Lesvos, post-fall

    # === 19th century ===
    'agios-serafeim-sarof':           (1833, '†1833',                   'known'),    # Sarov
    'agios-nikolaos-planas':          (1932, '†1932',                   'known'),    # Athens

    # === 20th century moderns ===
    'agios-nektarios':                (1920, '†1920',                   'known'),    # Aegina
    'agios-silouanos-athonitis':      (1938, '†1938',                   'known'),    # Athos
    'agios-iosif-isychastis':         (1959, '†1959',                   'known'),    # Athos
    'agios-porfyrios-kafsokalyvitis': (1991, '†1991',                   'known'),    # Athos / Oropos
    'agios-paisios-agioreitis':       (1994, '†1994',                   'known'),    # Athos
    'agios-sofronios-essex':          (1993, '†1993',                   'known'),    # Essex
    'agios-loukas-symferoupoleos':    (1961, '†1961',                   'known'),    # Crimea
    'agia-matrona-moskhas':           (1952, '†1952',                   'known'),    # Moscow
    'agios-savvas-kalymniou':         (1948, '†1948',                   'known'),    # Kalymnos
    'agios-nikiforos-lepros':         (1964, '†1964',                   'known'),    # Chios/Athens
    'agios-eumenios-saridakis':       (1999, '†1999',                   'known'),    # Athens
    'agios-antonios-souroz':          (2003, '†2003',                   'known'),    # London (Metr. Anthony)
}


def patch_file(path: str, slug: str, year: int, label: str) -> bool:
    """Insert reposeYear and reposeLabel into the frontmatter just before the
    closing ---. Idempotent: if reposeYear is already present, skip."""
    with open(path, 'r', encoding='utf-8') as fp:
        content = fp.read()
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m:
        print(f'  SKIP no-frontmatter: {slug}')
        return False
    fm = m.group(1)
    if 'reposeYear:' in fm:
        # already patched
        return False
    # insert before the closing ---
    # Build the new frontmatter
    new_lines = [f'reposeYear: {year}',
                 f'reposeLabel: "{label}"']
    new_fm = fm.rstrip() + '\n' + '\n'.join(new_lines)
    new_content = '---\n' + new_fm + '\n---' + content[m.end():]
    with open(path, 'w', encoding='utf-8') as fp:
        fp.write(new_content)
    return True


def main():
    saints_dir = SAINTS_DIR
    if not os.path.isdir(saints_dir):
        print(f'ERROR: {saints_dir} not found. Run from repo root.', file=sys.stderr)
        sys.exit(1)

    greek_slugs = []
    for f in sorted(os.listdir(saints_dir)):
        if not f.endswith('.md'):
            continue
        path = os.path.join(saints_dir, f)
        with open(path, 'r', encoding='utf-8') as fp:
            content = fp.read()
        m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        if re.search(r'^draft:\s*true', fm, re.MULTILINE):
            continue
        if not re.search(r'^language:\s*el', fm, re.MULTILINE):
            continue
        greek_slugs.append(f[:-3])

    missing = [s for s in greek_slugs if s not in DATA]
    if missing:
        print('ERROR: missing entries in DATA for these slugs:')
        for s in missing:
            print(f'  - {s}')
        sys.exit(2)

    patched = 0
    skipped = 0
    estimated = []
    known = []
    for slug in greek_slugs:
        year, label, conf = DATA[slug]
        path = os.path.join(saints_dir, slug + '.md')
        if patch_file(path, slug, year, label):
            patched += 1
        else:
            skipped += 1
        if conf == 'estimate':
            estimated.append((slug, year, label))
        else:
            known.append((slug, year, label))

    print(f'\nPatched: {patched}')
    print(f'Skipped (already had reposeYear or no frontmatter): {skipped}')
    print(f'Total Greek saints: {len(greek_slugs)}')
    print(f'\nKnown (well-attested year): {len(known)}')
    print(f'Estimated (century-level only): {len(estimated)}')
    if estimated:
        print('\n--- Estimates (audit these): ---')
        for s, y, lab in estimated:
            print(f'  {s}: {y} ({lab})')


if __name__ == '__main__':
    main()
