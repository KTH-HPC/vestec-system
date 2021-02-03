import sys
#sys.path.append("../")
from manager import workflow
import os
import pony.orm as pny
import datetime
import time
import json
from base64 import b64decode
from Database import LocalDataStorage
from Database.workflow import Simulation
from DataManager.client import registerDataWithDM, putByteDataViaDM, DataManagerException
from SimulationManager.client import createSimulation, submitSimulation, SimulationManagerException
from ExternalDataInterface.client import registerEndpoint, ExternalDataInterfaceException, removeEndpoint

# we now want to define some handlers
@workflow.handler
def external_data_arrival_handler(message):
    print("Got some external data from "+message["data"]["source"])
    workflow.Complete(message["IncidentID"])

@workflow.handler
@pny.db_session
def manually_add_data(message):    
    file_contents_to_add = json.loads(message["data"]["payload"])
    if ("," in file_contents_to_add["payload"]):
        header, encoded = file_contents_to_add["payload"].split(",", 1)        
        data = b64decode(encoded)
    else:
        header=file_contents_to_add["payload"]
        data=""

    if (":" in header and ";" in header):        
        filetype=header.split(":", 1)[1].split(";", 1)[0]
    else:
        filetype=""

    incidentId=message["IncidentID"]
    new_file = LocalDataStorage(contents=data, filename=incidentId+"/"+file_contents_to_add["filename"], filetype=filetype)
    pny.commit()        

    try:
        registerDataWithDM(file_contents_to_add["filename"], "localhost", "manually uploaded", filetype, str(len(data)), "Manually added", 
                storage_technology="VESTECDB", path=incidentId, associate_with_incident=True, incidentId=incidentId, kind=file_contents_to_add["filetype"], 
                comment=file_contents_to_add["filecomment"])
    except DataManagerException as err:
        print("Error registering uploaded data with DM, "+err.message)

@workflow.handler
@pny.db_session
def test_workflow(message):
    print("Test called!")
    callbacks = {'COMPLETED': 'simple_workflow_execution_completed'}    

    try:
        sim_id=createSimulation(message["IncidentID"], 100, "00:10", "test run", "subtest.pbs", callbacks, template_dir="template")
    except SimulationManagerException as err:
        print("Error creating simulation "+err.message)
        return
    
    simulation=Simulation[sim_id]

    data_blob="Sample configuration file"
    try:
        data_uuid=putByteDataViaDM("configuration.txt", "ARCHER", "simulation configuration file", "text/plain", "VESTEC autogenerated", data_blob, path=simulation.directory)
        print("Data uuid is "+data_uuid)
    except DataManagerException as err:
        print("Error creating configuration file on machine, continuing without! "+err.message)            

    try:
        submitSimulation(sim_id)
    except SimulationManagerException as err:
        print("Error submitting simulation "+err.message)

@workflow.handler
def simple_workflow_execution_completed(message):
    print("Stage completed with simulation ID "+message["simulationId"])

@workflow.handler
def shutdown_simple(message):
    print("Shutdown simple workflow for "+message["IncidentID"])

    try:
        removeEndpoint(message["IncidentID"], "editest", "external_data_arrival")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on endpoint removal "+err.message)

    try:
        removeEndpoint(message["IncidentID"], "add_data_simple"+message["IncidentID"], "add_data_simple")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on registration "+err.message)

    try:
        removeEndpoint(message["IncidentID"], "test_stage_"+message["IncidentID"], "test_workflow_simple")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on registration "+err.message)

    workflow.Cancel(message["IncidentID"])

@workflow.handler
def initialise_simple(message):
    print("Initialise simple workflow for "+message["IncidentID"])
    
    try:
        registerEndpoint(message["IncidentID"], "editest", "external_data_arrival")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on registration "+err.message)
    
    try:
        registerEndpoint(message["IncidentID"], "add_data_simple"+message["IncidentID"], "add_data_simple")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on registration "+err.message)

    try:
        registerEndpoint(message["IncidentID"], "test_stage_"+message["IncidentID"], "test_workflow_simple")
    except ExternalDataInterfaceException as err:
        print("Error from EDI on registration "+err.message)

    workflow.setIncidentActive(message["IncidentID"])

# we have to register them with the workflow system
def RegisterHandlers():
    workflow.RegisterHandler(external_data_arrival_handler, "external_data_arrival")
    workflow.RegisterHandler(manually_add_data, "add_data_simple")
    workflow.RegisterHandler(test_workflow, "test_workflow_simple")
    workflow.RegisterHandler(initialise_simple, "initialise_simple")
    workflow.RegisterHandler(shutdown_simple, "shutdown_simple")
    workflow.RegisterHandler(simple_workflow_execution_completed, "simple_workflow_execution_completed")
