#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Load the data, perform iterative parsing and audittng and write the
output to csv files. 

"""
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema
import os

import audit

OSM_PATH = "warsaw_poland.osm"

if not os.path.exists('./CSV_Files'):
    os.makedirs('./CSV_Files/')

NODES_PATH = './CSV_Files/' + OSM_PATH[:-4] + "_nodes.csv"
NODE_TAGS_PATH ='./CSV_Files/' + OSM_PATH[:-4] + "_nodes_tags.csv"
WAYS_PATH = './CSV_Files/' + OSM_PATH[:-4] + "_ways.csv"
WAY_NODES_PATH = './CSV_Files/' + OSM_PATH[:-4] + "_ways_nodes.csv"
WAY_TAGS_PATH = './CSV_Files/' + OSM_PATH[:-4] + "_ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

audit.building_mapping={}
audit.cafe_names_mapping={}

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def audit_k(tag, entries, default_tag_type):
    '''Audit k attribute of element and return proper k and type values'''

    k = tag.attrib['k']
    if not PROBLEMCHARS.search(k):
        index = k.find(':')
        if index == -1:
            entries['key'] = k
            entries['type']= default_tag_type
        else: 
            entries['key'] = k[index+1:]
            entries['type']= k[:index]
    else:        
        entries['type']= default_tag_type 
                    
    return entries
    


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""
    
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    is_cafe = False


    if element.tag == 'node':
        
        # Iterate over node fields
        for tag in element.iter("node"):
            for field in node_attr_fields:
                node_attribs[field]= tag.attrib[field]
                
        # Iterate over tag fields&remember the cafe value
        for tag in element.iter('tag'):
            if tag.attrib['v'] =='cafe':
                is_cafe = True

        # Iterate over tag fields
        for tag in element.iter('tag'):
            entries={}
            entries['id']= node_attribs['id']

            # audit the v atttribute
            entries['value'] = audit.audit_v(is_cafe, tag)

            # audit the k attribute
            entries = audit_k(tag, entries, default_tag_type)
            tags.append(entries) 
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        
        # Iterate over way fields
        for tag in element.iter('way'):
            for field in way_attr_fields:
                way_attribs[field]= tag.attrib[field]
                
        # Iterate over tag fields&remember the cafe value
        for tag in element.iter('tag'):
            if tag.attrib['v'] =='cafe':
                is_cafe = True

        # Iterate over tag fields        
        for tag in element.iter('tag'):
            entries={}
            entries['id']= way_attribs['id']

            # audit the v atttribute
            entries['value'] = audit.audit_v(is_cafe, tag)

            # audit the k attribute
            entries = audit_k(tag, entries, default_tag_type)
            tags.append(entries)
            
        # Iterate over nd fields
        i=0
        for tag in element.iter('nd'):
            entriesnd={}
            entriesnd['id']= way_attribs['id']
            entriesnd['node_id'] = tag.attrib['ref']
            entriesnd['position'] = i
            i+=1
            way_nodes.append(entriesnd)    
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])



# Note: Validation is ~ 10X slower. For the project consider using a small
# sample of the map when validating.
    
process_map(OSM_PATH, validate=False)
print('Processed {} Map Succesfully!'.format(OSM_PATH[:-4]))