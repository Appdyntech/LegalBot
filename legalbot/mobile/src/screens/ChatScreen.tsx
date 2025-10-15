// mobile/src/screens/ChatScreen.tsx
import React, { useState } from "react";
import { View, TextInput, Button, Text, ScrollView } from "react-native";
import MessageBubble from "../components/MessageBubble";
import { sendChat } from "../api/chat";

export default function ChatScreen() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);

  async function handleSend() {
    if (!q || q.trim() === "") return;
    setLoading(true);
    try {
      const resp = await sendChat({
        query: q,
        kb: "digitized_docs",
        top_k: 4
      });
      setAnswer(resp.answer);
      setSources(resp.sources || []);
    } catch (err) {
      console.error(err);
      setAnswer("[error] Unable to get response");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView style={{ flex: 1, paddingTop: 16 }}>
        {answer && <MessageBubble text={answer} />}
        {sources.map((s, idx) => (
          <View key={idx} style={{ paddingHorizontal: 12 }}>
            <Text style={{ fontSize: 12, color: "#6b7280" }}>{s.source}</Text>
            <Text style={{ marginBottom: 8 }}>{s.snippet}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={{ padding: 12 }}>
        <TextInput
          placeholder="Ask a legal question..."
          multiline
          style={{ borderWidth: 1, borderColor: "#d1d5db", borderRadius: 8, padding: 8, minHeight: 80 }}
          value={q}
          onChangeText={setQ}
        />
        <View style={{ marginTop: 8 }}>
          <Button title={loading ? "Thinking..." : "Send"} onPress={handleSend} disabled={loading} />
        </View>
      </View>
    </View>
  );
}
