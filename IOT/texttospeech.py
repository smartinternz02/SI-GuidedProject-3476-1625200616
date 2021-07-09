from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import playsound
authenticator=IAMAuthenticator('9yVyfbwuj3xpp5SdTAoAAVUs4e4V2SE0_j-DDr-yrrGA')
text_to_speech=TextToSpeechV1(
    authenticator=authenticator
)
text_to_speech.set_service_url("https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/instances/a5f75cd2-401f-4661-8733-f737cbe21499")
with open('sound.mp3','wb')as audio_file:
    audio_file.write(
        text_to_speech.synthesize(
            'oh no Alert!Alert! Animal Detected.',
            voice='en-US_AllisonV3Voice',
            accept='audio/mp3'
        ).get_result().connect)
playsound.playsound('sound.mp3')
