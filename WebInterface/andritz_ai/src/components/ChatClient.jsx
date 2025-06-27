"use client";

import { motion } from 'framer-motion';
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import React, { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import "../app/globals.css";
import dotenv from 'dotenv';
import path from 'path'

export default function Chatbot({ email }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const socketRef = useRef(null);
    const containerRef = useRef(null);
    const lastUserMessageRef = useRef(null);
    const heartbeatInterval = useRef(null);
    const { data: session, status } = useSession();
    const router = useRouter();
    const didConnectRef = useRef(false);

    useEffect(() => {
        async function sendHeartbeat() {
            try {
                await fetch("/api/presence", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ userEmail: email }),
                });
            } catch (err) {
                console.error("Erro ao enviar heartbeat:", err);
            }
        }

        sendHeartbeat();

        heartbeatInterval.current = setInterval(() => {
            sendHeartbeat();
        }, 30 * 1000);

        const handleBeforeUnload = async () => {
            try {
                if (heartbeatInterval.current) clearInterval(heartbeatInterval.current);
                window.removeEventListener("beforeunload", handleBeforeUnload);

                await fetch("/api/presence/logout", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ userEmail: email }),
                });
            } catch (err) {
                console.error("Erro no logout (beforeunload):", err);
            }
        };
        window.addEventListener("beforeunload", handleBeforeUnload);
    }, [email]);

    const handleLogout = () => {
        signOut({ callbackUrl: "/" });
    };

    useEffect(() => {
        if (status === "loading") return;
        if (!session) {
            router.push(`/api/auth/signin?callbackUrl=/chat`);
        }
    }, [session, status, router]);

    useEffect(() => {
        if (!containerRef.current || !lastUserMessageRef.current) return;

        lastUserMessageRef.current.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    }, [messages]);

    useEffect(() => {
        const userId = email;
        fetch(`${process.env.NEXT_PUBLIC_API_C_DEV}/logs/toggle`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ toggle: false, userId }),
        })
            .then(res => res.json())
            .then(data => console.log("Toggle reset no servidor:", data))
            .catch(err => console.error("Erro ao resetar toggle no servidor:", err));
    }, []);

    const lastUserIndex = messages
        .map(msg => msg.sender)
        .lastIndexOf('user');

    const connectWebSocket = () => {
        const userId = email;
        if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
            socketRef.current.close();
        }

        const wsUrl = `ws://localhost:5148/ws?userId=${encodeURIComponent(userId)}`;

        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log("Conexão WebSocket estabelecida com sucesso!");
        };

        ws.onmessage = (event) => {
            let dataObject;
            try {
                dataObject = JSON.parse(event.data);
            } catch (e) {
                console.error("ERRO FATAL: O dado recebido não é um JSON válido! Verifique o backend.", e);
                return;
            }

            if (dataObject && typeof dataObject === 'object' && 'lastLog' in dataObject) {
                const { lastLog } = dataObject;

                if (lastLog !== null && lastLog !== undefined) {
                    setMessages(prev => [...prev, { text: lastLog, sender: 'bot', time: new Date().toISOString() }]);
                } else {
                    console.warn("AVISO: A chave 'lastLog' veio com valor nulo ou indefinido.");
                }

            } else {
                console.error("ERRO FATAL: O objeto recebido NÃO CONTÉM a chave 'lastLog'");
                console.log("Objeto recebido:", dataObject);
            }
        };

        ws.onclose = (e) => {
            if (!e.wasClean) {
                setTimeout(connectWebSocket, 2000);
            }
        };

        ws.onerror = (errorEvent) => {
            console.error("[ERRO DE CONEXÃO WEBSOCKET]", errorEvent);
        };
    };

    useEffect(() => {
        if (!didConnectRef.current) {
            didConnectRef.current = true;
            connectWebSocket();
        }
        return () => {
            socketRef.current?.close();
        };
    }, [email]);

    const sendMessage = async () => {
        if (!input.trim()) return;
        const userId = email;
        setLoading(true);

        const textToSend = input;
        setMessages((prev) => [
            ...prev,
            { text: textToSend, sender: "user", time: new Date().toISOString() },
        ]);
        setInput("");

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_C_DEV}/logs/user`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ log: textToSend, userId }),
            });
        } catch (err) {
            console.error("Erro ao enviar log do usuário:", err);
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const CODE_DELIM = '```';

    const parseInlineBold = (text) => {
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, i) => {
            const m = part.match(/^\*\*(.+)\*\*$/);
            return m
                ? <strong key={i}>{m[1]}</strong>
                : <React.Fragment key={i}>{part}</React.Fragment>;
        });
    };

    const renderContent = (text) => {
        const parts = text.split(CODE_DELIM);

        return parts.map((part, idx) => {
            if (idx % 2 === 1) {
                const code = part.replace(/^\w+\n/, '');
                return (
                    <pre
                        key={idx}
                        className="overflow-x-auto rounded-md p-2 bg-gray-900"
                    >
                        <code className="font-mono text-gray-200">
                            {code}
                        </code>
                    </pre>
                );
            }

            const lines = part.split(/\r?\n/);

            return (
                <React.Fragment key={idx}>
                    {lines.map((rawLine, i) => {
                        const line = rawLine.trim();
                        if (!line) {
                            return <br key={i} />;
                        }

                        if (line.startsWith('### ')) {
                            const content = line.slice(4).trim();
                            return (
                                <h3
                                    key={i}
                                    className="text-2xl font-bold mt-6 mb-2"
                                >
                                    {parseInlineBold(content)}
                                </h3>
                            );
                        }

                        if (line.startsWith('#### ')) {
                            const content = line.slice(5).trim();
                            return (
                                <h4
                                    key={i}
                                    className="text-xl font-bold mt-4 mb-1"
                                >
                                    {parseInlineBold(content)}
                                </h4>
                            );
                        }

                        if (line.startsWith('*** ')) {
                            const content = line.slice(4).trim();
                            return (
                                <p key={i} className="font-medium">
                                    <strong>{content}</strong>
                                </p>
                            );
                        }

                        if (/^[-*]\s+/.test(line)) {
                            const marker = line.slice(0, line.indexOf(' ') + 1);
                            const content = line.slice(marker.length);
                            return (
                                <p key={i} className="whitespace-pre-wrap font-medium">
                                    {marker}{parseInlineBold(content)}
                                </p>
                            );
                        }

                        return (
                            <p key={i} className="whitespace-pre-wrap font-medium">
                                {parseInlineBold(line)}
                            </p>
                        );
                    })}
                </React.Fragment>
            );
        });
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{
                opacity: 1,
                transition: { delay: 2, duration: 0.4, ease: "easeIn" },
            }}
            className="relative min-h-screen min-w-screen flex items-center justify-center p-6 w-full h-full">
            <div className="absolute inset-0 -z-10"></div>

            <div className="flex flex-col h-full w-full p-6 rounded-lg overflow-auto">

                <div className="flex justify-between text-center relative mb-6">

                    

                    <div className="flex items-center text-center">
                        <button
                            onClick={handleLogout}
                            className="text-sm text-white px-3 py-1 border border-slate-900 button-logout"
                        >
                            Sair
                        </button>
                    </div>
                </div>

                <div className="flex justify-center items-center relative w-full circle-container">
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                </div>

                <div className="flex flex-col gap-4 flex-1">
                    <Card className="h-[75vh] w-full bg-transparent border-none shadow-none rounded-md overflow-hidden animate-border card-with-background">

                        <CardContent
                            ref={containerRef}
                            className="h-full overflow-y-auto p-4 space-y-3"
                        >
                            {messages.map((msg, i) => {
                                const isLastUser = msg.sender === 'user' && i === lastUserIndex;

                                return (
                                    <div
                                        key={i}
                                        ref={isLastUser ? lastUserMessageRef : undefined}
                                        className={`p-3 rounded-md shadow-sm break-words max-w-fit font-bold
                                        ${msg.sender === 'user'
                                                ? 'bg-[#3498db] text-white self-end ml-auto'
                                                : 'bot-reponse-bg text-gray-300 self-start'
                                            }`}
                                    >
                                        {renderContent(msg.text)}
                                    </div>
                                );
                            })}
                        </CardContent>
                    </Card>

                    <div className="flex flex-wrap items-center gap-2 w-full">
                        <Input
                            as="textarea"
                            rows={4}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Digite sua mensagem..."
                            className={`
                            flex-1 min-w-0 px-4 py-2 h-12 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 pulse-shadow
                                ${input
                                    ? 'bg-white text-[#006db0]'
                                    : 'text-white'
                                }
                            `}
                        />

                    </div>
                </div>
            </div>
        </motion.div >
    );
}