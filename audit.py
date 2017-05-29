#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' File including the auditing functions to be called through audit_v at the time of transforming the Map-XML to CSV'''
import codecs
###Audit the Phone Numbers####

def delete_spec_chars(number):
    '''Delete special characters and spaces'''

    char = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c ' 
    return filter(lambda x: not (x in char), number)

def insert_spaces(number):
    '''Insert spaces acc to the format'''
    number = number[:3] + ' ' + number[3:5] + ' ' + number[5:]
    return number
    
def get_raw_local(number):
    '''Clean the number and get raw local num'''

    #get the local number
    number = number.lstrip('+')
    number = number.lstrip('00')
    number = number.lstrip('48')

    # delete the second number or extra digits over 9
    if len(number)>=9:
        number = number[:9]
    return number
        
def is_foreign(number):
    '''Check if foreign number'''
    
    #Check if foreign
    if number.startswith('00') or number.startswith('+'):
        number = number.lstrip('+')
        number = number.lstrip('00')
        if not (number.startswith('48') or number.startswith('22')):
            return True
 
def correct_phone(number):

    #Delete special characters and spaces
    number = delete_spec_chars(number)

    if not is_foreign(number):

        #get the local number
        number = get_raw_local(number)
        
        #add the country prefix
        number = ('+48'+ number)

    number = insert_spaces(number)   
    return number

####Audit the key:Building#####

#Set the global variable for the building mapping
building_mapping={}

def correct_building(val):

    if  'shop' in val or 'store' in val or 'retail' in val or 'food' in val   or 'fuel' in val:
        building_mapping[val] = 'retail'
    elif 'office' in val or 'commercial' in val:
        building_mapping[val] = 'commercial'
    elif 'residential' in val:
        building_mapping[val] = 'apartments'
    elif  'enter' in val or 'hall' in val or 'library' in val or 'palace'in val or 'monument' in val or 'castle' in val or 'civ' in val:
        building_mapping[val] = 'civic'
    elif  'clini' in val or 'docto' in val:
        building_mapping[val] = 'hospital'
    elif 'muse' in val:
        building_mapping[val] = 'museum'
    elif 'ruin' in val or 'collapsed' in val:
        building_mapping[val] = 'ruins'
    elif 'terrac' in val:
        building_mapping[val] = 'terrace'    
    elif 'serv' in val or 'power' in val:
        building_mapping[val] = 'service'  
    elif 'avia' in val:
        building_mapping[val] = 'hangar' 
    elif 'mbass' in val:
        building_mapping[val] = 'embassy'
    elif 'boat' in val:
        building_mapping[val] = 'houseboat'
    elif 'otel' in val:
        building_mapping[val] = 'hotel'
    elif 'detache' in val:
        building_mapping[val] = 'detached'  
    elif  'convent' in val or 'basilica' in val or 'monastery' in val :
        building_mapping[val] = 'church'
    elif  'factory' in val or 'storage_tank' in val or 'silo' in val :
        building_mapping[val] = 'industrial'
    elif  'shrine' in val :
        building_mapping[val] = 'shrine'
    elif  'glass' in val :
        building_mapping[val] = 'conservatory'

    else: 
        building_mapping[val]=val

    return building_mapping[val]

####Audit the name:Cafe for key:'amenity'#####

#Set the global variable for the building mapping
cafe_names_mapping={}

def correct_cafe_names(val):    
    if  'green' in val.lower() or 'nero' in val.lower() :
        cafe_names_mapping[val] = 'Green Caffè Nero'
    elif 'costa' in val.lower():
        cafe_names_mapping[val] = 'Costa Coffee'
    elif 'blikle' in val.lower():
        cafe_names_mapping[val] = 'A. Blikle'

    else: 
        cafe_names_mapping[val]=val

    return cafe_names_mapping[val]

def audit_v(is_cafe, tag):
    '''Audit v attribute and return value'''

    v = tag.attrib['v'].encode('utf-8')

    #map building
    if tag.attrib['k']=='building':
        if v not in building_mapping.keys():
            cb = correct_building(v)
            print('Mapped: ' + v + ' => ' + cb)
        else: cb = building_mapping[v]
        return cb

    #map Cafe Names
    elif is_cafe:
        if tag.attrib['k']=='name':
            if v not in cafe_names_mapping.keys():
                cn = correct_cafe_names(v) 
                print('Mapped: ' + v + ' => ' + cn)
                return cn
            else: return cafe_names_mapping[v]

        
    # map phone
    elif tag.attrib['k']=='phone':  
        cf = correct_phone(v)      
        print('Mapped: ' + v + ' => ' + cf)
        return cf

    return v

