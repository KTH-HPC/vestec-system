import os
import requests

class DataManagerException(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

def registerDataWithDM(filename, machine, description, size, originator, group = "none", storage_technology=None, path=None):
    arguments = {   'filename': filename, 
                    'machine':machine,
                    'storage_technology' : storage_technology, 
                    'description':description, 
                    'size':size, 
                    'originator':originator,
                    'group' : group }
    if storage_technology is not None:
        arguments["storage_technology"]=storage_technology
    if path is not None:
        arguments["path"]=path

    returnUUID = requests.put(_get_DM_URL()+'/register', data=arguments)
    if returnUUID.status_code == 201:
        return returnUUID.text
    else:
        raise DataManagerException(returnUUID.status_code, returnUUID.text)

def searchForDataInDM(filename, machine, path=None):
    appendStr="filename="+machine+"&machine="+machine
    if path is not None:
        appendStr+="path="+path
    foundDataResponse = requests.get(_get_DM_URL()+'/search?'+appendStr)
    if foundDataResponse.status_code == 200:
        return foundDataResponse.json()
    else:
        raise DataManagerException(foundDataResponse.status_code, foundDataResponse.text)

def getInfoForDataInDM(data_uuid=None):
    if data_uuid is not None:
        response=requests.get(_get_DM_URL()+'/info/'+data_uuid)
    else:
        response=requests.get(_get_DM_URL()+'/info')
    if response.status_code == 200:
        return response.json()
    else:
        raise DataManagerException(response.status_code, response.text)

def getByteDataViaDM(data_uuid):
    retrieved_data=requests.get(_get_DM_URL()+'/get/'+data_uuid)
    if retrieved_data.status_code == 201:
        return retrieved_data.text
    else:
        raise DataManagerException(retrieved_data.status_code, retrieved_data.text)

def putByteDataViaDM(filename, machine, description, originator, payload, group = "none", storage_technology=None, path=None):
    arguments = {   'filename': filename, 
                    'machine':machine,
                    'storage_technology' : storage_technology, 
                    'description':description, 
                    'payload':payload, 
                    'originator':originator,
                    'group' : group }
    if storage_technology is not None:
        arguments["storage_technology"]=storage_technology
    if path is not None:
        arguments["path"]=path

    response=requests.put(_get_DM_URL()+'/put', data=arguments)
    if response.status_code == 201:
        return response.text
    else:
        raise DataManagerException(response.status_code, response.text)

def downloadDataToTargetViaDM(filename, machine, description, originator, url, protocol, group = "none", storage_technology=None, path=None, options=None ):
    arguments = {   'filename': filename, 
                    'machine':machine,
                    'storage_technology' : storage_technology, 
                    'description':description, 
                    'url':url, 
                    'protcol':protcol, 
                    'originator':originator,
                    'group' : group }
    if storage_technology is not None:
        arguments["storage_technology"]=storage_technology
    if path is not None:
        arguments["path"]=path
    if options is not None:
        arguments["options"]=options

    returnUUID = requests.put(_get_DM_URL()+'/getexternal', data=arguments)
    if returnUUID.status_code == 201:
        return returnUUID.text
    else:
        raise DataManagerException(returnUUID.status_code, returnUUID.text)

def moveDataViaDM(data_uuid):
    response=requests.post(_get_DM_URL()+'/move/'+data_uuid)
    if response.status_code == 201:
        return response.text
    else:
        raise DataManagerException(response.status_code, response.text)

def copyDataViaDM(data_uuid):
    response=requests.post(_get_DM_URL()+'/copy/'+data_uuid)
    if response.status_code == 201:
        return response.text
    else:
        raise DataManagerException(response.status_code, response.text)

def deleteDataViaDM(data_uuid):
    response=requests.delete(_get_DM_URL()+'/remove/'+data_uuid)
    if response.status_code != 200:
        raise DataManagerException(response.status_code, response.text)

def getDMHealth():
    try:
        health_status = requests.get(_get_DM_URL() + '/health')        
        return health_status.status_code == 200            
    except:
        return False

def _get_DM_URL():
    if "VESTEC_DM_URI" in os.environ:
        return os.environ["VESTEC_DM_URI"]
    else:
        return 'http://localhost:5000/DM'