import React, { useState, useEffect, useRef } from "react";
import { Joystick } from "react-joystick-component";
import { Input } from "./components/ui";

export default function BotController() {
  const [playerId, setPlayerId] = useState("");
  const [connected, setConnected] = useState(false);
  const [velocity, setVelocity] = useState({ linear: 0, angular: 0 });
  const [videoFeed1, setVideoFeed1] = useState("");
  const [videoFeed2, setVideoFeed2] = useState("");
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8081");

    socketRef.current.onopen = () => {
      setConnected(true);
      console.log("WebSocket connected");
    };

    socketRef.current.onmessage = (event) => {
      try {
        let parsedData = JSON.parse(event.data);
        console.log(parsedData.data);
        // console.log("First Parsed Data:", parsedData);

        if (typeof parsedData === "string") {
          parsedData = JSON.parse(parsedData);
        }

        // console.log("Final Data Type:", parsedData?.data); // Should now work

        if (parsedData.type === "cvframe1" && parsedData?.data) {
          // Ensure it's a valid base64 string

          const base64Image = `data:image/jpeg;base64,${parsedData?.data}`;
          //    console.log(base64Image);
          console.log("Data Type:", parsedData?.data);
          setVideoFeed1(base64Image);
        }

        if (parsedData.type === "cvframe2" && parsedData?.data) {
          // Ensure it's a valid base64 string

          const base64Image = `data:image/jpeg;base64,${parsedData?.data}`;
          //    console.log(base64Image);
          // console.log("Data Type:", parsedData?.type);
          setVideoFeed2(base64Image);
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }
    };

    socketRef.current.onclose = () => {
      setConnected(false);
      console.log("WebSocket disconnected");
    };

    socketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  const sendCommand = (lin, ang) => {
    if (!connected || !socketRef.current) return;

    const command = {
      player_id: playerId,
      velocity: [lin, ang],
      actions: {},
    };

    socketRef.current.send(JSON.stringify(command));
    setVelocity({ linear: lin, angular: ang });
  };

  const handleConnect = () => {
    if (playerId.trim() && socketRef.current) {
      const connectMessage = {
        player_id: playerId,
      };
      socketRef.current.send(JSON.stringify(connectMessage));
    }
  };

  const VideoFeed = ({ src, label }) => (
    <div className="w-full" style={{ aspectRatio: "16/9" }}>
      {src ? (
        <img
          src={src}
          alt={`${label} Feed`}
          className="w-full h-full object-cover rounded-lg"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-800 rounded-lg text-gray-500 text-xl">
          No {label.toLowerCase()} feed available
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Video Feeds Row */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <VideoFeed src={videoFeed1} label="Primary" />
        <VideoFeed src={videoFeed2} label="Secondary" />
      </div>

      {/* Controls Section */}
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Connection Controls */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-bold mb-4">Connection</h2>
          <div className="space-y-4">
            <Input
              placeholder="Enter Player ID"
              value={playerId}
              onChange={(e) => setPlayerId(e.target.value)}
              className="w-full bg-gray-700 border-gray-600"
            />
            <button
              onClick={handleConnect}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              disabled={!playerId.trim()}
            >
              Connect
            </button>
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  connected ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span>{connected ? "Connected" : "Disconnected"}</span>
            </div>
          </div>
        </div>

        {/* Center: Joystick */}
        <div className="bg-gray-800 p-6 rounded-lg flex flex-col items-center">
          <h2 className="text-xl font-bold mb-4">Controls</h2>
          <div className="relative">
            <Joystick
              size={150}
              baseColor="#374151"
              stickColor={connected ? "#3B82F6" : "#6B7280"}
              baseShape="square"
              stickShape="rectangle"
              move={(e) => sendCommand(e.y, e.x)}
              stop={() => sendCommand(0, 0)}
              disabled={!connected}
            />
          </div>
        </div>

        {/* Right: Status */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-bold mb-4">Status</h2>
          <div className="space-y-2">
            <p>
              Linear Velocity:{" "}
              <span className="font-mono">{velocity.linear.toFixed(2)}</span>
            </p>
            <p>
              Angular Velocity:{" "}
              <span className="font-mono">{velocity.angular.toFixed(2)}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
