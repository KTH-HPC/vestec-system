import sys
sys.path.append("../")
import requests
import datetime
from flask import Flask, request, jsonify
import Utils.log as log
import json
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask("External Data Interface")
logger = log.VestecLogger("External Data Interface")
push_registered_handlers={}
pull_registered_handlers=[]
poll_scheduler=BackgroundScheduler()

def isHandlerAlreadyRegistered(handlerToAdd, existingList):
    for handler in existingList:
        if handler == handlerToAdd: return True
    return False

class DataHandler:
    def __init__(self, queue_name, incidentID, source_endpoint, pollPeriod=None):
        self.queue_name=queue_name
        self.incidentId=incidentID
        self.source_endpoint=source_endpoint
        self.pollPeriod=pollPeriod
        self.schedulerevent=None
   
    def isPollHandler(self):
        return self.pollPeriod is not None
    def getQueueName(self):
        return self.queue_name
    def getIncidentId(self):
        return self.incidentId
    def getSourceEndpoint(self):
        return self.source_endpoint
    def getPollPeriod(self):
        return self.pollPeriod
    def __eq__(self, other):
        if self.queue_name == other.getQueueName() and self.incidentId == other.getIncidentId() and self.source_endpoint == other.getSourceEndpoint() and self.pollPeriod == other.getPollPeriod():            
            return True
        else:
            return False
    def generateJSON(self):
        return {"queuename": self.queue_name, "endpoint": self.source_endpoint, "incidentid": self.incidentId, "pollperiod": self.pollPeriod}

    def schedule(self):
        self.schedulerevent=poll_scheduler.add_job(self.pollDataSource, 'interval', seconds=self.getPollPeriod())
    def cancel(self):
        if self.schedulerevent is not None:            
            self.schedulerevent.remove()
            self.schedulerevent=None
    def pollDataSource(self):
        x = requests.head(self.source_endpoint, allow_redirects=True)
        if x.ok:
            data_packet={}
            data_packet["source"]=self.source_endpoint
            data_packet["timestamp"]=int(datetime.datetime.timestamp(datetime.datetime.now()))
            data_packet["headers"]=x.headers
            data_packet["status_code"]=x.status_code            
            print("Forward headers "+str(data_packet))             

def handlePostOfData(source, data):
    if source in push_registered_handlers:
        print("got data from: "+source+" Data: "+str(data))
        return jsonify({"status": 200, "msg": "Data received"}) 
    else:
        return jsonify({"status": 400, "msg": "No matching handler registered"})

@app.route("/EDI", methods=["POST"])
def post_data_anon():    
    return handlePostOfData(request.remote_addr, request.get_data())    

@app.route("/EDI/<sourceid>", methods=["POST"])
def post_data(sourceid):
    return handlePostOfData(sourceid, request.get_data())

def generateDataHandler(dict):
    dict = request.get_json()
    queue_name = dict["queuename"]
    incident_ID = dict["incidentid"]
    source_endpoint = dict["endpoint"]
    if "pollperiod" in dict:
        pollperiod = dict["pollperiod"]
    else:
        pollperiod=None
    return DataHandler(queue_name, incident_ID, source_endpoint, pollperiod)

@app.route("/EDImanager/register", methods=["POST"])
def register_handler():
    dict = request.get_json()
    handler=generateDataHandler(dict)
    source_endpoint=handler.getSourceEndpoint()
    if handler.isPollHandler():
        if not isHandlerAlreadyRegistered(handler, pull_registered_handlers):
            pull_registered_handlers.append(handler)
            handler.schedule()
            return jsonify({"status": 200, "msg": "Handler registered"})
        else:
            return jsonify({"status": 400, "msg": "Handler already registered for polling"})
    else:
        if source_endpoint not in push_registered_handlers:
            push_registered_handlers[source_endpoint]=[]
        if not isHandlerAlreadyRegistered(handler, push_registered_handlers[source_endpoint]):
            push_registered_handlers[source_endpoint].append(handler)        
            return jsonify({"status": 200, "msg": "Handler registered"})
        else:
            return jsonify({"status": 400, "msg": "Handler already registered for push"})

@app.route("/EDImanager/remove", methods=["POST"])
def remove_handler():
    dict = request.get_json()
    remove_handler=generateDataHandler(dict)
    handler_removed=False
    for handler in pull_registered_handlers:
        if remove_handler == handler:
            pull_registered_handlers.remove(handler)
            handler.cancel()
            handler_removed=True
    source_endpoint=remove_handler.getSourceEndpoint()
    if source_endpoint in push_registered_handlers:        
        for handler in push_registered_handlers[source_endpoint]:
            if (remove_handler == handler):
                push_registered_handlers[source_endpoint].remove(handler)
                handler_removed=True

    if handler_removed:                
        return jsonify({"status": 200, "msg": "Handler removed"})
    else:
        return jsonify({"status": 400, "msg": "No existing handler registered"})

@app.route("/EDImanager/list/<endpoint>", methods=["GET"])
def list_handlers_withep(endpoint):
    built_up_json_src=[]
    for handler in pull_registered_handlers:
        if handler.getSourceEndpoint==endpoint:
            built_up_json_src.extend(handler.generateJSON())
    if endpoint in push_registered_handlers:
        built_up_json_src.extend(buildDescriptionOfHandlers(push_registered_handlers[endpoint]))
    return json.dumps(built_up_json_src)    

@app.route("/EDImanager/list", methods=["GET"])
def list_handlers():
    built_up_json_src=buildDescriptionOfHandlers(pull_registered_handlers)    
    for value in push_registered_handlers.values():
        built_up_json_src.extend(buildDescriptionOfHandlers(value))
    return json.dumps(built_up_json_src)

def buildDescriptionOfHandlers(handler_list):
    json_to_return=[]
    for handler in handler_list:
        json_to_return.append(handler.generateJSON())
    return json_to_return

if __name__ == "__main__":
    poll_scheduler.start()
    app.run(host="0.0.0.0", port=5501)