import { useState } from "react";
import type { KeyboardEvent } from "react";

import { askIsCoolGPT } from "./api/client";
import type { ProviderOption, AggregatedResponse } from "./api/client";

type Message = {
  role: "user" | "assistant";
  content: string;
  // Quando for uma resposta do modo fusion, guardamos o payload completo
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

  const handleSend = async () => {
    if (!question.trim() || loading) return;

    setError(null);

    const userContent = question.trim();
    const userMsg: Message = { role: "user", content: userContent };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      // aqui no futuro entra o token do Google
      const token: string | undefined = undefined;

      const resp = await askIsCoolGPT(userContent, provider, token);

      // para modo fusion, queremos guardar as respostas individuais
      let assistantMsg: Message;
      if (provider === "fusion") {
        assistantMsg = {
          role: "assistant",
          content: resp.final_answer,
          fusionMeta: resp,
        };
      } else {
        // nos modos simples usamos só a final_answer mesmo
        assistantMsg = {
          role: "assistant",
          content: resp.final_answer || resp.answers?.[0]?.answer || "",
        };
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      console.error(err);

      const message =
        err instanceof Error
          ? err.message
          : "Erro ao chamar o IsCoolGPT.";

      setError(message);

      const assistantMsg: Message = {
        role: "assistant",
        content:
          "Ocorreu um erro ao tentar responder. Tente novamente em alguns instantes.",
      };
      setMessages((prev) => [...prev, assistantMsg]);
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
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
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

        <div className="text-xs text-slate-400">
          (Login com Google entra aqui depois)
        </div>
      </header>

      {/* Conteúdo principal */}
      <main className="flex-1 flex flex-col max-w-4xl w-full mx-auto px-4 py-4 gap-4">
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
        <div className="flex-1 overflow-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col gap-3">
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
            const hasFusion = !!m.fusionMeta && m.fusionMeta.answers?.length > 0;

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
                          : "bg-slate-800 text-slate-100 rounded-bl-sm"
                      }
                    `}
                  >
                    {m.content}
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

        {/* Input */}
        <div className="border border-slate-800 rounded-2xl bg-slate-900/80 p-3 flex flex-col gap-2">
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
