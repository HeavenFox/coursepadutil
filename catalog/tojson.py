import simplejson
import umsgpack
import glob
import xml.etree.ElementTree as et
import re

fns = glob.glob('*.xml')
xmls = [et.parse(fn) for fn in fns]

all_profs = set()

faulty_prof = {
    'Francis,J)' : 'Francis,J (jdf2)',
    'Glathar,E)' : 'Glathar,E',
    'Cady,B)' : 'Cady,B'
}

day_pattern = {
    'M': 1,
    'T': 1<<1,
    'W': 1<<2,
    'R': 1<<3,
    'F': 1<<4,
    'S': 1<<5,
    'U': 1<<6
}

def to_bool(s):
    return True if s == 'Y' else False

def to_list(node):
    return [a.text.strip() for a in node]


def set_if_truthy(obj, idx, value):
    if value:
        obj[idx] = value

def convert_crosslist(c):
    if c is None:
        return None
    if len(c) > 0:
        return [c.find('subject').text, int(c.find('catalog_nbr').text)]
    return None

def get_s(node):
    if node is None:
        return None
    return node.text

def parse_prof(name):
    if name in faulty_prof:
        name = faulty_prof[name]

    result = re.search(r'\((.+)\)', name)
    if result is None:
        print "warning: %s dont have netid" % name
        return name
    else:
        netid = result.group(1)
        all_profs.add(netid)
        return netid


def convert_meeting(node):
    obj = {}
    pattern = 0
    pattern_desc = node.find('meeting_pattern_sdescr').text
    if pattern_desc != 'TBA':
        for c in pattern_desc:
            pattern |= day_pattern[c]
    set_if_truthy(obj, 'ptn', pattern)
    set_if_truthy(obj, 'bldg', node.find('building_code').text)
    set_if_truthy(obj, 'rm', node.find('room').text)
    set_if_truthy(obj, 'st', node.find('start_time').text)
    set_if_truthy(obj, 'et', node.find('end_time').text)
    set_if_truthy(obj, 'sd', node.find('start_date').text)
    set_if_truthy(obj, 'ed', node.find('end_date').text)
    set_if_truthy(obj, 'profs', [parse_prof(s) for s in to_list(node.find('instructors') or [])])

    return obj


def convert_section(node):
    comp = node.get('ssr_component')

    obj = {}
    obj['nbr'] = node.get('class_number')
    obj['sec'] = node.get('class_section')
    set_if_truthy(obj, 'consent', get_s(node.find('consent_ldescr')))
    set_if_truthy(obj, 'note', get_s(node.find('notes')))
    set_if_truthy(obj, 'mt', [convert_meeting(s) for s in node.findall('meeting')])

    return comp, obj

def maybe_float(s):
    if s.find('.') > -1:
        return float(s)
    return int(s)

def convert_units(s):
    return [maybe_float(a) for a in s.split('-')]

def convert_course(node):
    obj = {}
    obj['sub'] = node.get('subject')
    obj['nbr'] = int(node.get('catalog_nbr'))
    obj['unit'] = convert_units(node.find('units').text)
    obj['title'] = node.find('course_title').text
    set_if_truthy(obj, 'topics', to_list(node.find('topics')))
    set_if_truthy(obj, 'crosslists', [convert_crosslist(a) for a in node.find('crosslists') or []])
    set_if_truthy(obj, 'comeetings', [convert_crosslist(a) for a in node.find('comeetings') or []])
    secs = {}
    for sec in node.find('sections'):
        comp, sec = convert_section(sec)
        if comp not in secs:
            secs[comp] = []
        secs[comp].append(sec)

    obj['secs'] = secs

    return obj




courses = []

for xml in xmls:
    for c in xml.getroot():
        courses.append(convert_course(c))

output = open('courses.json', 'wb')
simplejson.dump(courses, output)
output.close()


output = open('courses_readable.json', 'wb')
simplejson.dump(courses, output, indent='  ', sort_keys=True)
output.close()

profs_sorted = list(all_profs)
profs_sorted.sort()
print profs_sorted