import glob
import xml.etree.ElementTree as et

fns = glob.glob('*.xml')
print fns
xmls = [et.parse(fn) for fn in fns]

def verify(xml):
    root = xml.getroot()
    # verify that each section has only one meeting
    for course in root:
        if course.tag != 'course':
            return False
        subcourses = set()
        for section in course.find('sections'):
            subcourses.add(section.attrib['ssr_component'])
        if len(subcourses) > 2:
            print section.attrib['class_number']
            return False

    return True

print map(verify, xmls)
