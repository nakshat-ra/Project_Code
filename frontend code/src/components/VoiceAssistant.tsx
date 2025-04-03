'use client';
import { Room } from 'livekit-client';

import {
  ControlBar,
  GridLayout,
  LiveKitRoom,
  ParticipantTile,
  RoomAudioRenderer,
  useTracks,
} from '@livekit/components-react';
import { DisconnectButton } from "@livekit/components-react";
import '@livekit/components-styles';

import { useEffect, useState } from 'react';
import { Track } from 'livekit-client';
// import SimpleVoiceAssistance from './SimpleVoiceAssistance';
import SimpleVoiceAssistance from './SimpleVoiceAssistance2';

interface VoiceAssistantProps {
  setShowVoiceAssistant: (show: boolean) => void;
}

const VoiceAssistant = ({ setShowVoiceAssistant }: VoiceAssistantProps) =>  {
  // TODO: get user input for room and name

  const name = 'quickstart-user';
  // const room = new Room();
  const livekitUrl = "";
  
  const [token, setToken] = useState("");
  const [roomName, setRoomName] = useState("");

  // const url = "https://livekitwebapp-abddetfvdfg2gaar.eastus2-01.azurewebsites.net"
  const url = "http://127.0.0.1:8000"
  // const url = "https://serverforwindowvm2-dghvd3dkebd4excq.eastus2-01.azurewebsites.net"

  useEffect(() => {
    const fetchToken = async () => {
      try {
        console.log("run");
        const response = await fetch(`${url}/getToken`);
        const data = await response.json();
        setRoomName(data.room_name);  
        setToken(data.token);
        // console.log()
      } catch (error) {
        alert("Something went wrong..")
        console.error("Error fetching token:", error);
      }
    };
  
    fetchToken(); // Call the async function inside useEffect
  }, []); 

  const onDisconnect = async ()=> {
    setShowVoiceAssistant(false)
    const response = await fetch(`${url}/deleteRoom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ room_name: roomName }),
      });
    
      if (response.ok) {
        console.log('Room deleted successfully');
      } else {
        console.error('Failed to delete room');
      }
    console.log(" here ")
  }

  return (
    <div className='h-[90%] border-1 border-solid border-gray-500 rounded-sm m-1 p-2 bg-white w-full'>
    <LiveKitRoom
      serverUrl={livekitUrl}
      token = {token}
      video={false}
      connect={true}
      audio={true}
      onDisconnected={onDisconnect}
      data-lk-theme="default"
      className='flex h-12 justify-center'
      style={{ 
        backgroundColor: 'white',
        '--lk-background-color': 'white'
      } as React.CSSProperties}
    >
      {/* <DisconnectButton className='h-20'>Leave room</DisconnectButton> */}

      <RoomAudioRenderer />
      <SimpleVoiceAssistance/>
    </LiveKitRoom>
    </div>
  );
}

function MyVideoConference() {
  // `useTracks` returns all camera and screen share tracks. If a user
  // joins without a published camera track, a placeholder track is returned.
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false },
  );
  return (
    <GridLayout tracks={tracks} style={{ height: 'calc(100vh - var(--lk-control-bar-height))' }}>
      {/* The GridLayout accepts zero or one child. The child is used
      as a template to render all passed in tracks. */}
      <ParticipantTile />
    </GridLayout>
  );
}
// const VoiceAssistant = () => {
//   return (
//     <div>
//         video Assistant

//     </div>
//   )
// }

export default VoiceAssistant