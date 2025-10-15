// mobile/src/components/MessageBubble.tsx
import React from "react";
import { View, Text } from "react-native";

export default function MessageBubble({ text, isUser }: { text: string; isUser?: boolean }) {
  return (
    <View style={{
      backgroundColor: isUser ? "#2563eb" : "#fff",
      padding: 12,
      borderRadius: 12,
      marginVertical: 6,
      marginHorizontal: 12
    }}>
      <Text style={{ color: isUser ? "#fff" : "#111" }}>{text}</Text>
    </View>
  );
}
