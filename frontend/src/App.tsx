import { useState, useRef, useEffect } from "react";
import type { KeyboardEvent } from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { askIsCoolGPT } from "./api/client";
import type { ProviderOption, AggregatedResponse } from "./api/client";

type Message = {
  role: "user" | "assistant";
  content: string;
  fusionMeta?: AggregatedResponse;
};

const PROVIDERS: ProviderOption[] = ["fusion", "gemini", "huggingface"];

function App() {
  const [provider, setProvider] = useState<ProviderOption>("fusion");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openFusionIndex, setOpenFusionIndex] = useState<number | null>(null);

  // ---- controle de scroll ----
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const isAtBottomRef = useRef(true);

  useEffect(() => {
    isAtBottomRef.current = isAtBottom;
  }, [isAtBottom]);

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    const el = chatContainerRef.current;
    if (!el) return;
    el.scrollTo({
      top: el.scrollHeight,
      behavior,
    });
  };

  const handleScroll = () => {
    const el = chatContainerRef.current;
    if (!el) return;

    // threshold maior pra considerar "ainda estou no fundo"
    const threshold = 100; // px de tolerância
    const atBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;

    setIsAtBottom(atBottom);
    if (atBottom) {
      setUnreadCount(0);
    }
  };

  // ---- efeito de digitação da resposta do bot ----
  const streamAssistantMessage = (msg: Message) => {
    const fullText = msg.content;
    const baseMsg: Message = { ...msg, content: "" };

    // adiciona a mensagem vazia primeiro
    setMessages((prev) => [...prev, baseMsg]);

    // se o usuário não está no fim, conta como "nova"
    if (!isAtBottomRef.current) {
      setUnreadCount((prev) => prev + 1);
    }

    let index = 0;
    // velocidade rápida (como antes)
    const step = 3; // caracteres por "tick"
    const intervalMs = 15;

    const intervalId = window.setInterval(() => {
      index += step;
      if (index >= fullText.length) {
        index = fullText.length;
      }
      const slice = fullText.slice(0, index);

      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        const last = updated[lastIndex];
        updated[lastIndex] = { ...last, content: slice };
        return updated;
      });

      // se o usuário está no fim, acompanha a digitação
      // mas não em TODO tick pra não brigar com o scroll manual
      if (isAtBottomRef.current && index % 5 === 0) {
        scrollToBottom("auto");
      }

      if (index >= fullText.length) {
        window.clearInterval(intervalId);
      }
    }, intervalMs);
  };

  const handleSend = async () => {
    if (!question.trim() || loading) return;

    setError(null);

    const userContent = question.trim();
    const userMsg: Message = { role: "user", content: userContent };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    // ao enviar, força ir pro fim do chat
    setTimeout(() => {
      scrollToBottom("smooth");
      setIsAtBottom(true);
      setUnreadCount(0);
    }, 0);

    try {
      const token: string | undefined = undefined;

      const resp = await askIsCoolGPT(userContent, provider, token);

      let assistantMsg: Message;
      if (provider === "fusion") {
        assistantMsg = {
          role: "assistant",
          content: resp.final_answer,
          fusionMeta: resp,
        };
      } else {
        assistantMsg = {
          role: "assistant",
          content: resp.final_answer || resp.answers?.[0]?.answer || "",
        };
      }

      // aqui entra o efeito "máquina de escrever"
      streamAssistantMessage(assistantMsg);
    } catch (err: unknown) {
      console.error(err);

      const message =
        err instanceof Error ? err.message : "Erro ao chamar o IsCoolGPT.";

      setError(message);

      const assistantMsg: Message = {
        role: "assistant",
        content:
          "Ocorreu um erro ao tentar responder. Tente novamente em alguns instantes.",
      };

      // erro não precisa digitar char a char
      setMessages((prev) => [...prev, assistantMsg]);

      if (isAtBottomRef.current) {
        setTimeout(() => scrollToBottom("smooth"), 0);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleFusionDetails = (idx: number) => {
    setOpenFusionIndex((current) => (current === idx ? null : idx));
  };

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Topbar */}
      <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-sky-400 font-bold">
            iG
          </span>
          <div className="flex flex-col">
            <span className="font-semibold">IsCoolGPT</span>
            <span className="text-xs text-slate-400">
              Assistente para estudos de Cloud
            </span>
          </div>
        </div>

      </header>

      {/* Conteúdo principal */}
      <main className="flex-1 flex flex-col max-w-5xl w-full mx-auto px-4 py-10 gap-10">
        {/* Seletor de providers */}
        <div className="flex gap-2 flex-wrap justify-center">
          {PROVIDERS.map((p) => (
            <button
              key={p}
              onClick={() => setProvider(p)}
              className={`px-3 py-1.5 rounded-full border text-sm capitalize transition
                ${
                  provider === p
                    ? "bg-indigo-500 border-indigo-400 text-white shadow"
                    : "border-slate-700 text-slate-300 hover:border-slate-500"
                }
              `}
            >
              {p === "fusion" ? "Fusion (Gemini + HF)" : p}
            </button>
          ))}
        </div>

        {/* Banner de erro */}
        {error && (
          <div className="border border-red-500/60 bg-red-500/10 text-red-200 text-sm px-3 py-2 rounded-xl">
            {error}
          </div>
        )}

        {/* Área do chat */}
        <div className="relative">
          <div
            ref={chatContainerRef}
            onScroll={handleScroll}
            className="custom-scrollbar rounded-md border border-slate-800 bg-slate-900/60 p-4 pb-10 flex flex-col gap-3
               h-[60vh] overflow-y-auto"
          >
            {messages.length === 0 && (
              <div className="text-center text-sm text-slate-500 mt-10">
                Comece perguntando algo como:
                <div className="mt-2 text-slate-300">
                  “Explique EC2 de forma simples” ou “Diferença entre S3 e EBS”
                </div>
              </div>
            )}

            {messages.map((m, idx) => {
              const isUser = m.role === "user";
              const hasFusion =
                !!m.fusionMeta && m.fusionMeta.answers?.length > 0;

              return (
                <div
                  key={idx}
                  className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                >
                  <div className="flex flex-col gap-1 max-w-[80%]">
                    <div
                      className={`rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap
                        ${
                          isUser
                            ? "bg-indigo-500 text-white rounded-br-sm"
                            : "bg-slate-800 text-slate-100 rounded-l-2x1"
                        }
                      `}
                    >
                      {isUser ? (
                        m.content
                      ) : (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: (props) => (
                              <p className="mb-1 leading-relaxed" {...props} />
                            ),
                            ul: (props) => (
                              <ul
                                className="list-disc pl-5 mb-1"
                                {...props}
                              />
                            ),
                            ol: (props) => (
                              <ol
                                className="list-decimal pl-5 mb-1"
                                {...props}
                              />
                            ),
                            li: (props) => <li className="mb-0.5" {...props} />,
                            strong: (props) => (
                              <strong className="font-semibold" {...props} />
                            ),
                            code: (props) => (
                              <code
                                className="rounded bg-slate-900/70 px-1 py-0.5 text-xs font-mono"
                                {...props}
                              />
                            ),
                          }}
                        >
                          {m.content}
                        </ReactMarkdown>
                      )}
                    </div>

                    {/* Detalhes do Fusion */}
                    {!isUser && hasFusion && (
                      <div className="text-xs text-slate-400">
                        <button
                          onClick={() => toggleFusionDetails(idx)}
                          className="underline underline-offset-2 hover:text-slate-200 transition"
                        >
                          {openFusionIndex === idx
                            ? "Esconder respostas individuais"
                            : "Ver respostas individuais (Gemini / HuggingFace)"}
                        </button>

                        {openFusionIndex === idx && (
                          <div className="mt-2 border border-slate-700 rounded-xl bg-slate-900/80 p-2 flex flex-col gap-2">
                            {m.fusionMeta!.answers.map((ans) => (
                              <div
                                key={ans.provider}
                                className="border border-slate-700/70 rounded-lg p-2"
                              >
                                <div className="text-[11px] uppercase text-slate-400 mb-1">
                                  {ans.provider}
                                </div>
                                <div className="text-xs text-slate-200 whitespace-pre-wrap">
                                  {ans.answer}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
                  IsCoolGPT está pensando...
                </div>
              </div>
            )}
          </div>

          {/* Botão "scroll to bottom" estilo WhatsApp */}
          {!isAtBottom && messages.length > 0 && (
            <button
              onClick={() => {
                scrollToBottom("smooth");
                setIsAtBottom(true);
                setUnreadCount(0);
              }}
              className="absolute bottom-3 right-3 rounded-full bg-slate-900/90 border border-slate-700 px-3 py-1.5 text-xs flex items-center gap-1 shadow-md hover:bg-slate-800 transition"
            >
              <span className="text-lg leading-none">ᐯ</span>
              {unreadCount > 0 && (
                <span className="text-[10px] bg-indigo-500 text-white rounded-full px-1.5 py-0.5">
                  {unreadCount}
                </span>
              )}
            </button>
          )}
        </div>

        {/* Input */}
        <div className="border border-slate-800 rounded-md bg-slate-900/80 p-4 flex flex-col gap-3 w-full max-w-5xl mx-auto">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            placeholder="Pergunte algo sobre AWS, GCP ou Azure..."
            className="bg-transparent resize-none outline-none text-sm text-slate-100 placeholder:text-slate-500"
          />
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500">
              Shift + Enter para nova linha
            </span>
            <button
              onClick={handleSend}
              disabled={!question.trim() || loading}
              className="inline-flex items-center gap-1 rounded-full bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-1.5 text-sm font-medium transition"
            >
              Enviar
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
