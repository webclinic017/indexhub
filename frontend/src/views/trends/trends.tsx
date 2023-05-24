import React from "react";
import ChatContextProvider from "./chat/chat_context";
import TrendsDashboard from "./trends_dashboard";

export default function Trends() {
    return (
        <ChatContextProvider>
            <TrendsDashboard />
        </ChatContextProvider>
    );
}
