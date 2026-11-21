#!/usr/bin/env python3
"""Build index.html for danielfinol.github.io from the four PDFs.

Usage (from the repository root):
    python3 tools/build_site.py

Reads  : CV_Daniel_E_Finol_G_{en,es}_b.pdf  and  Resume_Daniel_E_Finol_G_{en,es}.pdf  (repo root)
         tools/template.html                (page design + behaviour; contains the JS and CSS)
         contact info from tools/contact.json (NOT committed, see contact.example.json)
         or the environment variables FINOL_EMAIL and FINOL_PHONE
Writes : index.html (repo root)

Needs Python 3 and poppler-utils (the `pdftohtml` command).
Options: --pdf-dir DIR  --template FILE  --out FILE  --contact FILE
"""
import re, json, unicodedata, os, sys, argparse, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--pdf-dir', default=str(HERE.parent))
ap.add_argument('--template', default=str(HERE / 'template.html'))
ap.add_argument('--out', default=str(HERE.parent / 'index.html'))
ap.add_argument('--contact', default=str(HERE / 'contact.json'))
ARGS = ap.parse_args()

CV_PDF = 'CV_Daniel_E_Finol_G_{lang}_b.pdf'
RESUME_PDF = 'Resume_Daniel_E_Finol_G_{lang}.pdf'

def load_contact():
    email, phone = os.environ.get('FINOL_EMAIL'), os.environ.get('FINOL_PHONE')
    p = Path(ARGS.contact)
    if (not email or not phone) and p.exists():
        c = json.loads(p.read_text(encoding='utf-8')); email = email or c.get('email'); phone = phone or c.get('phone')
    if not email or not phone:
        sys.exit('Missing contact details: create tools/contact.json (see contact.example.json) or set FINOL_EMAIL and FINOL_PHONE.')
    return email, phone

def to_xml(kind, pattern, tmp):
    d = Path(tmp) / kind; d.mkdir(parents=True, exist_ok=True)
    for lang in ('en', 'es'):
        pdf = Path(ARGS.pdf_dir) / pattern.format(lang=lang)
        if not pdf.exists(): sys.exit(f'Missing PDF: {pdf}')
        subprocess.run(['pdftohtml', '-xml', '-i', '-q', '-noroundcoord', str(pdf), str(d / lang)], check=True)
    return str(d)

_TMP = tempfile.TemporaryDirectory()
CV_XML = to_xml('cv', CV_PDF, _TMP.name)
RS_XML = to_xml('resume', RESUME_PDF, _TMP.name)

# ---------------------------------------------------------------------------
# Source text: parsing rules and the hand-written highlight summaries
# ---------------------------------------------------------------------------
BUL = re.compile(r'^\s*(?:[▪•·])\s*')
HEADS = {
 'en': [("HIGHER EDUCATION","edu"),("PROFESSIONAL EXPERIENCE","exp"),("PUBLICATIONS AND RESEARCH","pub"),
        ("COURSES SYMPOSIA WORKSHOPS AND HACKATHONS","courses"),("SKILLS ASSESSMENT AT DATACAMP","dc"),
        ("AWARDS AND DISTINCTIONS","awards"),("PROGRAMMING LANGUAGES","prog"),("LANGUAGES","lang"),
        ("MASSIVE OPEN ONLINE COURSES","mooc")],
 'es': [("FORMACIÓN ACADÉMICA","edu"),("EXPERIENCIA PROFESIONAL","exp"),("PUBLICACIONES E INVESTIGACIÓN","pub"),
        ("DISTINCIONES Y RECONOCIMIENTOS","awards"),("EVALUACIÓN DE HABILIDADES EN DATACAMP","dc"),
        ("CURSOS SIMPOSIOS TALLERES Y HACKATONES","courses"),("LENGUAJES DE PROGRAMACIÓN","prog"),
        ("IDIOMAS","lang"),("CURSOS EN LÍNEA ABIERTOS MASIVOS","mooc")]}
TITLES = {
 'en': dict(edu="Higher education",exp="Professional experience",pub="Publications and research",
   courses="Courses, symposia, workshops and hackathons",dc="Skills assessment at DataCamp",
   awards="Awards and distinctions",prog="Programming languages",lang="Languages",
   mooc="Massive open online courses (MOOCs)"),
 'es': dict(edu="Formación académica",exp="Experiencia profesional",pub="Publicaciones e investigación",
   courses="Cursos, simposios, talleres y hackatones",dc="Evaluación de habilidades en DataCamp",
   awards="Distinciones y reconocimientos",prog="Lenguajes de programación",lang="Idiomas",
   mooc="Cursos en línea abiertos masivos (MOOCs)")}
SUMM = {
 'en': dict(
  edu="Master of Applied Computer Science (grade average 97.8%) and B.Sc. in Computer Science, ranked first in the class of 2001, both at Universidad del Zulia.",
  exp="Lecturer in programming and data science; Aggregate Professor in the Applied Computer Science Master's at Universidad del Zulia (2005–2018); teaching assistant at Neuromatch Academy.",
  pub="Articles and book chapters on artificial intelligence, algorithmic transparency and intellectual property, plus research on global optimization with surrogate models.",
  courses="AI safety, NeuroAI, data science bootcamps and workshops with BlueDot Impact, Neuromatch Academy, The Alan Turing Institute, MIT, Cambridge and others.",
  dc="100th percentile in Understanding and Interpreting Data and 99th in Python Programming.",
  awards="Second prize in the XI ASEDA Prize (2017) and first places in several programming marathons, including the South American ACM regional.",
  prog="Python, C and Matlab/Octave.",
  lang="Native Spanish; English at C2 level (EF SET 95/100); French with DELF A1–A4 certificates.",
  mooc="Dozens of courses from Stanford, Johns Hopkins, Boston University, deeplearning.ai and other institutions, in AI, machine learning, neuroscience and mathematics."),
 'es': dict(
  edu="Magíster en Computación Aplicada (promedio 97.8%) y Licenciado en Computación, Primer Lugar de la Promoción 2001, ambos en la Universidad del Zulia.",
  exp="Profesor de programación y ciencia de datos; Profesor Agregado de la Maestría en Computación Aplicada de la Universidad del Zulia (2005–2018); asistente docente en Neuromatch Academy.",
  pub="Artículos y capítulos de libro sobre inteligencia artificial, transparencia algorítmica y propiedad intelectual; investigación en optimización global con modelos sustitutos.",
  courses="Seguridad de la IA, NeuroAI, bootcamps de ciencia de datos y talleres con BlueDot Impact, Neuromatch Academy, The Alan Turing Institute, MIT, Cambridge y otros.",
  dc="Percentil 100 en Understanding and Interpreting Data y 99 en Python Programming.",
  awards="Accésit en el XI Premio Aseda (2017) y primeros lugares en varias maratones de programación, incluida la eliminatoria sudamericana de la ACM.",
  prog="Python, C y MATLAB/Octave.",
  lang="Español nativo; inglés nivel C2 (EF SET 95/100); francés con certificados DELF A1–A4.",
  mooc="Decenas de cursos de Stanford, Johns Hopkins, Boston University, deeplearning.ai y otras instituciones, en IA, aprendizaje automático, neurociencia y matemáticas.")}

# Topic filter buttons on the full-CV view (hand-written). An item is shown for a topic when its text,
# links' addresses excluded, matches one of the terms. 'ci': case-insensitive regular expressions
# (written so they work in both Python and JavaScript; avoid \b next to accented letters).
# 'cs': exact-case terms matched as whole words (e.g. AI, IA). Both languages share the same terms,
# because the Spanish CV keeps many course titles in English. The build prints the matches per topic.
TOPICS = [
 dict(key='ai', en="Artificial intelligence", es="Inteligencia artificial",
      ci=[r"artificial intelligence", r"inteligencia artificial", r"machine learning", r"aprendizaje automático",
          r"deep learning", r"neural network", r"redes neuronales", r"neuroai", r"scikit-learn", r"alignment"],
      cs=["AI", "IA", "GenAI"]),
 dict(key='data', en="Data science", es="Ciencia de datos",
      ci=[r"data scien", r"ciencia de datos", r"statistic", r"estadístic", r"data study",
          r"social data", r"interpreting data", r"time series", r"visuali[sz]ation", r"analytics",
          r"network analysis", r"network science", r"machine learning", r"scikit-learn", r"\bsql\b", r"\br programming"],
      cs=[]),
 dict(key='teach', en="Teaching", es="Docencia",
      ci=[r"\bteacher", r"teaching assistant", r"teaching and learning", r"teaching update", r"\bprofess?or",
          r"\btaught", r"preparador docente", r"perfeccionamiento docente", r"enseñanza y aprendizaje", r"enseñado"],
      cs=[]),
 dict(key='neuro', en="Neuroscience", es="Neurociencia",
      ci=[r"neurosci", r"neurocienc", r"neuroai", r"neurons", r"\bbrain", r"fmri", r"psychiatry", r"cognitive"],
      cs=[]),
 dict(key='law', en="AI ethics, law & safety", es="IA: ética, derecho y seguridad",
      ci=[r"\blaw\b", r"\bderecho", r"\blegal\b", r"jurídic", r"intellectual property", r"propiedad intelectual",
          r"copyright", r"transparen", r"\bethic", r"ai safety", r"sécurité de l.ia", r"alignment", r"transformative ai"],
      cs=[]),
 dict(key='math', en="Mathematics & optimization", es="Matemáticas y optimización",
      ci=[r"optimi[sz]", r"optimizac", r"mathematic", r"matemátic", r"calculus i\b", r"cálculo i\b", r"calculus:",
          r"differential equations", r"stochastic", r"estocástic", r"multidimensional", r"surrogate", r"sustitutos",
          r"metamodel", r"algorithms: design"],
      cs=[]),
 dict(key='prog', en="Programming", es="Programación",
      ci=[r"programming", r"programación", r"python", r"matlab", r"\bsql\b", r"full-stack", r"data structures",
          r"estructuras de datos", r"marat[oó]n", r"marathon", r"\bmpi\b"],
      cs=[r"C(?=[\ue000-\ue00b]*:)"]),
]

import html as _h
MK=dict(B0='',B1='',I0='',I1='',A0='',A1='',A2='',S0='',S1='')
URLRE=re.compile(r'https?://[^\s<]*[^\s<.,;)]')
def seg(t,b=False,i=False,u=None,s=False): return dict(t=t,b=b,i=i,u=u,s=s)
def parse_inner(inner):
    out=[];B=I=0;U=[]
    for tok in re.split(r'(<[^>]+>)',inner):
        if not tok: continue
        if tok[0]=='<':
            if tok=='<b>':B+=1
            elif tok=='</b>':B-=1
            elif tok=='<i>':I+=1
            elif tok=='</i>':I-=1
            elif tok.startswith('<a '):
                h=_h.unescape(re.search(r'href="([^"]*)"',tok)[1]); U.append(h if h.startswith('http') else None)
            elif tok=='</a>':U.pop()
        else:
            t=unicodedata.normalize('NFC',_h.unescape(tok))
            out.append(seg(t,B>0,I>0,U[-1] if U else None))
    return out
def clean(segs):
    n=len(segs)
    for k,s in enumerate(segs):
        if s['t'].strip()=='':
            p=segs[k-1] if k else None; q=segs[k+1] if k+1<n else None
            for a in ('b','i','u','s'):
                s[a]=p[a] if (p and q and p[a]==q[a]) else (None if a=='u' else False)
    out=[]
    for s in segs:
        if not s['t']: continue
        if out and all(out[-1][a]==s[a] for a in 'biu') and out[-1]['s']==s['s']: out[-1]['t']+=s['t']
        else: out.append(dict(s))
    for s in out: s['t']=re.sub(r'\s+',' ',s['t'])
    if out: out[0]['t']=out[0]['t'].lstrip(); out[-1]['t']=out[-1]['t'].rstrip()
    out=[s for s in out if s['t']]
    res=[]
    for s in out:
        if s['u'] is None:
            pos=0
            for m in URLRE.finditer(s['t']):
                if m.start()>pos: res.append(dict(s,t=s['t'][pos:m.start()]))
                res.append(dict(s,t=m[0],u=m[0])); pos=m.end()
            if pos<len(s['t']): res.append(dict(s,t=s['t'][pos:]))
        else: res.append(s)
    return res
def load_lines(lang, base=None, meta=False):
    xml=open(f'{base or CV_XML}/{lang}.xml',encoding='utf-8').read()
    lines=[]
    for pg in re.split(r'<page ',xml)[1:]:
        els=[]
        for m in re.finditer(r'<text top="([\d.]+)" left="([\d.]+)" width="[\d.]+" height="([\d.]+)" font="\d+">(.*?)</text>',pg,re.S):
            els.append((float(m[1]),float(m[2]),float(m[3]),parse_inner(m[4])))
        els.sort(key=lambda e:(e[0],e[1]))
        groups=[]
        for e in els:
            if groups and e[0]-groups[-1][-1][0]<=8: groups[-1].append(e)
            else: groups.append([e])
        for g in groups:
            g.sort(key=lambda e:e[1]); segs=[]
            for top,left,h,ss in g:
                sup=any(o[2]>1.3*h and top<=o[0]-1 for o in g)
                for s in ss:
                    s['s']=sup; segs.append(s)
            segs=clean(segs)
            if segs: lines.append((g[0][1],max(e[2] for e in g),segs) if meta else segs)
    return lines
def plain(sl): return ''.join(s['t'] for s in sl)
def cut(sl,n):
    out=[]
    for s in sl:
        if n>=len(s['t']): n-=len(s['t']); continue
        out.append(dict(s,t=s['t'][n:])); n=0
    return out
def strip_chars(sl,ch):
    sl=[dict(s) for s in sl]
    while sl and not sl[0]['t'].lstrip(ch): sl.pop(0)
    if sl: sl[0]['t']=sl[0]['t'].lstrip(ch)
    while sl and not sl[-1]['t'].rstrip(ch): sl.pop()
    if sl: sl[-1]['t']=sl[-1]['t'].rstrip(ch)
    return sl
def render(sl):
    def inner(s):
        t=s['t']; core=t.strip()
        if not core: return t
        lead=t[:len(t)-len(t.lstrip())]; trail=t[len(t.rstrip()):]
        op=cl=''
        if s['b']: op+=MK['B0']; cl=MK['B1']+cl
        if s['i']: op+=MK['I0']; cl=MK['I1']+cl
        if s['s']: op+=MK['S0']; cl=MK['S1']+cl
        return lead+op+core+cl+trail
    o=''; k=0
    while k<len(sl):
        u=sl[k]['u']; j=k
        while j<len(sl) and sl[j]['u']==u: j+=1
        run=''.join(inner(x) for x in sl[k:j])
        if u:
            m=re.match(r'(\s*)(.*?)(\s*)$',run,re.S)
            run=m[1]+MK['A0']+u+MK['A1']+m[2]+MK['A2']+m[3]
        o+=run; k=j
    o=re.sub(r' {2,}',' ',o)
    o=re.sub('\ue003( ?)\ue002',r'\1',o); o=re.sub('\ue001( ?)\ue000',r'\1',o)
    return o
MKS=''.join(MK.values())
def pl(r): return re.sub('['+MKS+']','',re.sub('[^]*','',r))
def join(a,b):
    if pl(a) and pl(a)[-1] in '-–' and pl(b)[:1].isdigit(): return a+b
    return a+' '+b

def parse(lang):
    lines=load_lines(lang)
    secs={}; cur_sec=None; cur=None
    for sl in lines:
        p=plain(sl)
        if not p.strip(): continue
        hit=None
        if not BUL.match(p):
            for h,k in HEADS[lang]:
                if p.startswith(h): hit=(h,k); break
        if hit:
            h,k=hit
            cur_sec=secs.setdefault(k,dict(items=[],note='')); cur=None
            rest=strip_chars(cut(sl,len(h)),' :')
            for x in rest: x['s']=False
            if k=='mooc' and plain(rest).startswith('(MOOCS)'): rest=strip_chars(cut(rest,7),' :')
            if rest:
                if k=='dc': cur_sec['note']=render(strip_chars(rest,'() '))
                else: cur_sec['items'].append(render(rest)); cur=len(cur_sec['items'])-1
            continue
        if cur_sec is None: continue
        it=cur_sec['items']
        if lang=='es' and p.strip()=='1': continue
        if lang=='es' and re.match(r'^1?\s*Puntaje',p):
            secs.setdefault('dc',dict(items=[],note=''))['note']=render(sl); continue
        m=BUL.match(p)
        if m: it.append(render(cut(sl,m.end()))); cur=len(it)-1; continue
        if lang=='es' and secs.get('edu') is cur_sec and re.match(r'^(Magíster|Licenciado|Primer Lugar)',p):
            if p.startswith('Primer Lugar'): it[-1]+='\n'+render(sl); continue
            it.append(render(sl)); cur=len(it)-1; continue
        mo=re.match(r'^o\s+',p)
        if lang=='en' and mo and cur is not None:
            it[cur]+='\n'+render(cut(sl,mo.end())); continue
        if cur_sec is secs.get('dc') and not it:
            r=render(sl); cur_sec['note']=join(cur_sec['note'],r) if cur_sec['note'] else r; continue
        r=render(sl)
        if cur is None: it.append(r); cur=len(it)-1
        else: it[cur]=join(it[cur],r)
    fix=lambda x:re.sub(r'(\d) ()',r'\1\2',x)
    for s in secs.values():
        s['items']=[fix(i) for i in s['items']]; s['note']=fix(s['note'])
    return secs


RH = {'en': {'Summary':'summary','Skills':'skills','Experience':'exp','Education':'edu',
             'Applied projects, awards & publications':'applied','Courses':'courses'},
      'es': {'Perfil':'summary','Habilidades':'skills','Experiencia':'exp','Formación académica':'edu',
             'Proyectos aplicados, distinciones y publicaciones':'applied','Cursos':'courses'}}
RORDER = ['summary','skills','exp','edu','applied','courses']
RTITLES = {'en': dict(summary='Summary',skills='Skills',exp='Experience',edu='Education',
                      applied='Applied projects, awards & publications',courses='Courses'),
           'es': dict(summary='Perfil',skills='Habilidades',exp='Experiencia',edu='Formación académica',
                      applied='Proyectos aplicados, distinciones y publicaciones',courses='Cursos')}
RSUMM = {
 'en': dict(
  skills="Python (pandas, scikit-learn), C, MATLAB/Octave and SQL; supervised and unsupervised learning, neural networks and surrogate models; DataCamp-assessed in the 98th to 100th percentile.",
  exp="Python and data science at Universidad Alberto Hurtado (2026), survey programming at Ipsos, Neuromatch Academy, and 13 years as Aggregate Professor at Universidad del Zulia.",
  edu="MSc in Applied Computer Science (97.8% average) and BSc in Computer Science, ranked first in the class of 2001, both at Universidad del Zulia.",
  applied="Alan Turing Institute Data Study Group, data science and full-stack bootcamps, programming-contest podiums, and 8 papers and book chapters.",
  courses="Stanford, deeplearning.ai, Hinton and Inria machine-learning courses, recent AI-safety and Gen AI courses, and 30+ MOOCs."),
 'es': dict(
  skills="Python (pandas, scikit-learn), C, MATLAB/Octave y SQL; aprendizaje supervisado y no supervisado, redes neuronales y modelos sustitutos; evaluaciones DataCamp entre los percentiles 98 y 100.",
  exp="Python y ciencia de datos en la Universidad Alberto Hurtado (2026), programación de encuestas en Ipsos, Neuromatch Academy y 13 años como Profesor Agregado en la Universidad del Zulia.",
  edu="Magíster en Computación Aplicada (promedio 97,8%) y Licenciado en Computación, Primer Lugar de la promoción 2001, ambos en la Universidad del Zulia.",
  applied="Data Study Group del Alan Turing Institute, bootcamps de ciencia de datos y Python full stack, podios en maratones de programación y 8 artículos y capítulos.",
  courses="Cursos de machine learning de Stanford, deeplearning.ai, Hinton e Inria, cursos recientes de seguridad de la IA e IA generativa, y más de 30 MOOCs.")}

def join2(a, b):
    if pl(a)[-1:] == '-' and pl(b)[:1].islower(): return a + b
    return a + ' ' + b

def parse_resume(lang):
    rows = load_lines(lang, RS_XML, True)
    secs = {k: dict(items=[], text='') for k in RORDER}
    cur = None
    for left, h, sl in rows:
        p = plain(sl).strip()
        if h > 19.0:
            if p in RH[lang]: cur = RH[lang][p]
            continue
        if cur is None: continue
        r = render(sl)
        if cur == 'summary':
            secs[cur]['text'] = join2(secs[cur]['text'], r) if secs[cur]['text'] else r; continue
        items = secs[cur]['items']
        if p.startswith('•'):
            rest = strip_chars(cut(sl, plain(sl).index('•') + 1), ' ')
            rr = render(rest)
            if cur == 'exp': items[-1] += '\n' + rr
            else: items.append(rr)
        elif cur == 'exp' and left < 120 and sl[0]['b']:
            items.append(r)
        else:
            items[-1] = join2(items[-1], r)
    for s in secs.values():
        s['items'] = [re.sub(r' {2,}', ' ', i) for i in s['items']]
        s['text'] = re.sub(r' {2,}', ' ', s['text'])
    return secs

HOME = {
 'en': dict(
  sub="Computer & Data Scientist · Python · Machine Learning",
  lead="Computer and data scientist (MSc, 97.8% average) with 13 years of graduate teaching in machine learning, statistics and programming.",
  para="Led a funded research project on machine learning and co-authored papers on AI and law. Taught Python and data science in Chile; spent a year at Ipsos, an English-language global organization, programming surveys. Known for explaining complex technical ideas clearly to technical and non-technical audiences. Recent training in AI safety and generative AI. Bilingual: native Spanish, English C2.",
  cards=dict(resume="The short version: skills, experience, education and selected projects. Two pages.",
             cv="The complete record: every publication, award, course and MOOC.")),
 'es': dict(
  sub="Científico de Computación y Datos · Python · Machine Learning",
  lead="Científico de computación y datos (Magíster, promedio 97,8%) con 13 años de docencia de maestría en machine learning, estadística y programación.",
  para="Dirigí un proyecto de investigación financiado sobre machine learning y soy coautor de artículos sobre IA y derecho. Enseñé Python y ciencia de datos en Chile; trabajé un año en Ipsos, una organización global de habla inglesa, programando encuestas. Destaco por explicar con claridad conceptos técnicos complejos a públicos técnicos y no técnicos. Formación reciente en seguridad de la IA e IA generativa. Bilingüe: español nativo, inglés C2.",
  cards=dict(resume="La versión corta: habilidades, experiencia, formación y proyectos seleccionados. Dos páginas.",
             cv="El registro completo: todas las publicaciones, distinciones, cursos y MOOCs."))}
RSUB = {'en': "Computer & Data Scientist · Python · Machine Learning · Spanish (native) / English (C2)",
        'es': "Científico de Computación y Datos · Python · Machine Learning · Español (nativo) / Inglés (C2)"}

# ---------------------------------------------------------------------------
# Assemble the page data and write index.html
# ---------------------------------------------------------------------------
D = {}
CVSUB = {'en': "Lecturer+Magister in Computer+Data Science",
         'es': "Profesor & Magíster en Computación Aplicada & Ciencia de Datos"}
EMAIL, PHONE = load_contact()
for lang in ('en', 'es'):
    secs = parse(lang); rs = parse_resume(lang)
    order = [k for _, k in HEADS[lang]]
    D[lang] = dict(
        name="Daniel E. Finol-González", phone=[ord(c) for c in PHONE][::-1],
        home=HOME[lang],
        cv=dict(sub=CVSUB[lang], pdf=CV_PDF.format(lang=lang),
                sections=[dict(key=k, title=TITLES[lang][k], summary=SUMM[lang][k], items=secs[k]['items'], note=secs[k]['note']) for k in order]),
        resume=dict(sub=RSUB[lang], pdf=RESUME_PDF.format(lang=lang),
                lead=dict(title=RTITLES[lang]['summary'], text=rs['summary']['text']),
                sections=[dict(key=k, title=RTITLES[lang][k], summary=RSUMM[lang][k], items=rs[k]['items'], note='') for k in RORDER[1:]]))
    print(lang, 'cv', [(s['key'], len(s['items'])) for s in D[lang]['cv']['sections']])
    print(lang, 'resume', [(s['key'], len(s['items'])) for s in D[lang]['resume']['sections']])
# Email and phone are stored as reversed character codes and assembled by the page's script,
# so neither appears as text in index.html.
D['mail'] = [ord(c) for c in EMAIL][::-1]
D['topics'] = TOPICS
def _topic_hits(T, items):
    ci = re.compile('|'.join(T['ci']), re.I)
    cs = re.compile(r'(?<![A-Za-zÀ-ÿ])(?:' + '|'.join(T['cs']) + r')(?![A-Za-zÀ-ÿ])') if T['cs'] else None
    plain = lambda t: re.sub('[\ue000-\ue00b]', '', re.sub('\ue004[^\ue005]*\ue005', ' ', t))
    return sum(1 for t in items if ci.search(plain(t)) or (cs and cs.search(plain(t))))
for lang in ('en', 'es'):
    print(lang, 'topics', [(T['key'], _topic_hits(T, [i for s in D[lang]['cv']['sections'] for i in s['items']])) for T in TOPICS])
tpl = Path(ARGS.template).read_text(encoding='utf-8')
assert tpl.count('/*DATA*/null') == 1, 'template placeholder missing'
out = tpl.replace('/*DATA*/null', json.dumps(D, ensure_ascii=False).replace('</', '<\\/'))
Path(ARGS.out).write_text(out, encoding='utf-8')
print('wrote', ARGS.out, len(out), 'bytes')
