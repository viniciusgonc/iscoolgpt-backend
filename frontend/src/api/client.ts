// frontend/src/api/client.ts

export type ProviderOption = "fusion" | "gemini" | "huggingface";

export type ProviderAnswer = {
  provider: string;
  answer: string;
};

export type AggregatedResponse = {
  final_answer: string;
  answers: ProviderAnswer[];
};

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Faz POST /ask no backend FastAPI.
 *
 * question: pergunta do usuário
 * provider: "gemini" | "huggingface" | "fusion"
 * token: opcional (no futuro, Google ID token)
 */
export async function askIsCoolGPT(
  question: string,
  provider: ProviderOption,
  token?: string
): Promise<AggregatedResponse> {
  const providers =
    provider === "fusion" ? ["fusion"] : [provider]; // respeita sua lógica do aggregator

  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      providers,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status}: ${txt.slice(0, 200)}`);
  }

  return res.json();
}
