"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Bot, Sparkles, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";

// ===============================
// Types
// ===============================
type LLMProvider = {
  name: string;
  models: string[];
};

type LLMProvidersResponse = {
  providers: LLMProvider[];
  default_provider: string;
  default_model: string;
};

type LLMSelection = {
  provider: string;
  model: string;
};

// ===============================
// Props
// ===============================
interface LLMSelectorProps {
  onSelectionChange: (selection: LLMSelection) => void;
  apiUrl?: string;
  token?: string;
}

// ===============================
// Provider display names
// ===============================
const PROVIDER_NAMES: Record<string, string> = {
  ollama: "Ollama",
  openai: "OpenAI",
  serpro: "Serpro",
};

// ===============================
// Provider badges
// ===============================
const PROVIDER_COLORS: Record<string, string> = {
  ollama: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20",
  openai: "bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20",
  serpro: "bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20",
};

// ===============================
// Component
// ===============================
export function LLMSelector({ onSelectionChange, apiUrl = "http://localhost:8000", token }: LLMSelectorProps) {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch providers on mount
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${apiUrl}/chat/providers`, { headers });

        if (!response.ok) {
          throw new Error(`Erro ao carregar providers: ${response.status}`);
        }

        const data: LLMProvidersResponse = await response.json();
        setProviders(data.providers);

        // Load from localStorage or use defaults
        const savedProvider = localStorage.getItem("llm_provider");
        const savedModel = localStorage.getItem("llm_model");

        const initialProvider = savedProvider || data.default_provider;
        const initialModel = savedModel || data.default_model;

        setSelectedProvider(initialProvider);
        setSelectedModel(initialModel);

        // Notify parent
        onSelectionChange({
          provider: initialProvider,
          model: initialModel,
        });
      } catch (err) {
        console.error("Erro ao buscar providers:", err);
        setError(err instanceof Error ? err.message : "Erro desconhecido");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProviders();
  }, [apiUrl, token]);

  // Handle provider change
  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);

    // Auto-select first model of new provider
    const providerData = providers.find((p) => p.name === provider);
    const firstModel = providerData?.models[0] || "";
    setSelectedModel(firstModel);

    // Save to localStorage
    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("llm_model", firstModel);

    // Notify parent
    onSelectionChange({
      provider,
      model: firstModel,
    });
  };

  // Handle model change
  const handleModelChange = (model: string) => {
    setSelectedModel(model);

    // Save to localStorage
    localStorage.setItem("llm_model", model);

    // Notify parent
    onSelectionChange({
      provider: selectedProvider,
      model,
    });
  };

  // Get available models for selected provider
  const availableModels = providers.find((p) => p.name === selectedProvider)?.models || [];

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-1.5">
          <Bot className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground">Modelos LLM</span>
        </div>
        <div className="flex items-center justify-center h-9 px-3 border border-dashed rounded-md bg-muted/30">
          <Loader2 className="h-3 w-3 animate-spin" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-1.5">
          <Bot className="h-3.5 w-3.5 text-destructive" />
          <span className="text-xs font-medium text-muted-foreground">Modelos LLM</span>
        </div>
        <div className="flex items-center justify-center h-9 px-3 border border-destructive/50 rounded-md bg-destructive/5">
          <span className="text-xs text-destructive">⚠️ Erro</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Label */}
      <div className="flex items-center gap-1.5">
        <Bot className="h-3.5 w-3.5 text-primary" />
        <span className="text-xs font-medium text-muted-foreground">Modelos LLM</span>
      </div>

      {/* Provider Selector */}
      <Select value={selectedProvider} onValueChange={handleProviderChange}>
        <SelectTrigger className="h-9">
          <SelectValue>
            {selectedProvider && (
              <Badge
                variant="outline"
                className={`text-xs px-1.5 py-0.5 ${PROVIDER_COLORS[selectedProvider] || ""}`}
              >
                {PROVIDER_NAMES[selectedProvider] || selectedProvider}
              </Badge>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {providers.map((provider) => (
            <SelectItem key={provider.name} value={provider.name}>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={`text-xs ${PROVIDER_COLORS[provider.name] || ""}`}
                >
                  {PROVIDER_NAMES[provider.name] || provider.name}
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Model Selector */}
      <Select value={selectedModel} onValueChange={handleModelChange}>
        <SelectTrigger className="h-9">
          <SelectValue>
            {selectedModel && (
              <span className="text-xs font-mono truncate">{selectedModel}</span>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {availableModels.map((model) => (
            <SelectItem key={model} value={model}>
              <span className="font-mono text-xs">{model}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
