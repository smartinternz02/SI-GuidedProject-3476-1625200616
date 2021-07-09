import cv2
import numpy as np
import wiotp.sdk.device
import playsound
import random
import datetime
import ibm_boto3
import time
from ibm_botocore.client import Config, ClientError
#cloudant db
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc

stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

myConfig={
    "identity":{
        "orgId":"h8hazz",
        "typeId":"IOTdevice",
        "deviceId":"1001"
    },
    "auth":{
        "token":"1234567890"

    }
}

clientx=wiotp.sdk.device.DeviceClient(config=myConfig, logHandlers=None)
clientx.connect()

# This is how you authenticate.
metadata = (('authorization', 'Key 83727a951ba743a7a9cdb5ef43b20ab1'),)

COS_ENDPOINT= "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID="SMJxiYSCZMfvBCZGmziBjNWBwIUMKlkLWiq7kPq5pgtk"
COS_AUTH_ENDPOINT="https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/ec51d848d56a4315a195eac64a73a058:dd8894be-a232-43f4-b2c1-a9edefc8d3ac::",
clientdb=Cloudant("apikey-v2-23p0i2j8e7g6gkps50q3po7a58yngzigkfheraedl10u","e15afd6e9f04035a381a83b620a6f287",
                  url="https://apikey-v2-23p0i2j8e7g6gkps50q3po7a58yngzigkfheraedl10u:e15afd6e9f04035a381a83b620a6f287@7bb92285-7884-4652-9c40-ddabe949b4fc-bluemix.cloudantnosqldb.appdomain.cloud")
clientdb.connect()
#create resource
cos=ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))

        
def myCommandCallback(cmd):
        print("Command received: %s" % cmd.data)
        command=cmd.data['command']
        print(command)
        if(command=='lighton'):
            print("LIGHT ON IS RECEIVED")
        elif(command=='lightoff'):
            print("LIGHT OFF IS RECEIVED")
        elif(command=='motoron'):
            print("MOTOR IS ON")
        elif(command=='motoroff'):
            print("MOTOR OFF IS RECEIVED")
            

database_name="crop"
my_databse=clientdb.create_database(database_name)
if my_databse.exists():
    print(f"'{database_name}' successfully created.")
    
cap=cv2.VideoCapture('animal.mp4')
if(cap.isOpened()==True):
    print("file opened")
else:
    print("file not found")
    
while(cap.isOpened()):
    ret,frame=cap.read()
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    imS=cv2.resize(frame, (960,540))
    detect=False
    cv2.imwrite("ex.jpg",imS)
    with open("D:/IOT/ex.jpg","rb") as f:
        file_bytes=f.read()
        
    #model ID of a publicity available general model
    request = service_pb2.PostModelOutputsRequest(
        # This is the model ID of a publicly available General model. You may use any other public or custom model ID.
        model_id='aaa03c23b3724a16a56b629203edc62c',
        inputs=[
          resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))
        ])
    response = stub.PostModelOutputs(request, metadata=metadata)

    if response.status.code != status_code_pb2.SUCCESS:
       raise Exception("Request failed, status code: " + str(response.status.code))
    #print(response)
    for concept in response.outputs[0].data.concepts:
        #print(concept)
        if(concept.value>0.9):
            if(concept.name=="animal"):
                print("Alert! Alert! Animal Detected")
                playsound.playsound('sound.mp3')
                picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
                cv2.imwrite(picname+'.jpg',frame)
                multi_part_upload('icrop',picname+'.jpg',picname+'.jpg')
                json_document={"link":COS_ENDPOINT+'/'+'icrop'+'/'+picname+'.jpg'}
                new_document=my_databse.create_document(json_document)
                if new_document.exists():
                    print("Document successfully created")
                time.sleep(5)
                detect=True
    moist=random.randint(0,100)
    humidity=random.randint(100,200)
    myData={'Animal':detect,'moisture':moist,'humidity':humidity}
    print(myData)
    if(humidity!=None):
        clientx.publishEvent(eventId="status",  msgFormat="json",  data=myData,  qos=0,  onPublish=None)
        print("Publish Ok..")
    clientx.commandCallback=myCommandCallback
    cv2.imshow('frame',imS)
    if cv2.waitKey(1) & 0xFF==ord('q'):
     break
clientx.disconnect()
cap.release()
cv2.destroyAllWindows()
