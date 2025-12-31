"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, Trash2, Upload, Send, ArrowLeft, Loader2, CheckCircle, XCircle, StopCircle, Wrench, FileSearch } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronRight } from 'lucide-react'; 

// ===============================
// Tipos
// ===============================
type Project = {
  id: number;
  user_id: number;
  title: string;
  description: string;
  llm_prompt: string;
};

type UploadedFile = {
  filename: string;
  chunks_count: number;
  created_at: string;
};

type FilesResponse = {
  files: UploadedFile[];
  total_files: number;
  total_chunks: number;
};

type ChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
};

type ToolCall = {
  tool_name: string;
  tool_id: string;
  args: Record<string, any>;
};

type ToolResult = {
  tool_name: string;
  content: string;
};

// ===============================
// Componente interno que usa useSearchParams
// ===============================
function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("id");
  
  // PROJETO - ARQUIVOS
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [filesLoading, setFilesLoading] = useState(true);
  const [deletingFile, setDeletingFile] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // CHAT
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null); 
  const [expandedToolResults, setExpandedToolResults] = useState<Set<string>>(new Set());

  // Scroll automático para o final
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll quando mensagens mudarem
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Toggle de tool results
  const toggleToolResult = (messageIdx: number, resultIdx: number) => {
    const key = `${messageIdx}-${resultIdx}`;
    setExpandedToolResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  // ===============================
  // Função para buscar arquivos do projeto
  // ===============================
  const fetchProjectFiles = async () => {
    if (!projectId) return;

    try {
      setFilesLoading(true);
      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const response = await fetch(`http://localhost:8000/chat/files/${projectId}`, {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }
        throw new Error("Erro ao carregar arquivos");
      }

      const data: FilesResponse = await response.json();
      setUploadedFiles(data.files || []);
      
    } catch (err) {
      console.error("Erro ao buscar arquivos:", err);
      setUploadedFiles([]);
    } finally {
      setFilesLoading(false);
    }
  };

  // ===============================
  // Função de upload de arquivo PDF
  // ===============================
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    
    if (!file) return;

    // Validação do tipo de arquivo
    if (file.type !== 'application/pdf') {
      setUploadStatus('error');
      setUploadMessage('Apenas arquivos PDF são permitidos.');
      return;
    }

    // Validação do tamanho (opcional - máximo 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setUploadStatus('error');
      setUploadMessage('O arquivo deve ter no máximo 10MB.');
      return;
    }

    if (!projectId) {
      setUploadStatus('error');
      setUploadMessage('ID do projeto não encontrado.');
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadStatus('idle');
      setUploadMessage('');

      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/login");
        return;
      }

      // Simula progresso de upload
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const formData = new FormData();
      formData.append('uploaded_file', file);

      const response = await fetch(`http://localhost:8000/chat/upload/${projectId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Erro no upload: ${response.status}`);
      }

      setUploadStatus('success');
      setUploadMessage('Arquivo enviado com sucesso!');
      
      // Recarrega a lista de arquivos após upload bem-sucedido
      await fetchProjectFiles();
      
      // Limpa o input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

    } catch (err) {
      console.error('Erro no upload:', err);
      setUploadStatus('error');
      setUploadMessage(err instanceof Error ? err.message : 'Erro desconhecido no upload');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      
      // Limpa a mensagem após 5 segundos
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadMessage('');
      }, 5000);
    }
  };

  // ===============================
  // Função para deletar arquivo
  // ===============================
  const handleDeleteFile = async (filename: string) => {
    if (!projectId) return;

    try {
      setDeletingFile(filename);
      
      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const response = await fetch(`http://localhost:8000/chat/files/${projectId}/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Erro ao deletar arquivo: ${response.status}`);
      }

      // Remove o arquivo da lista local
      setUploadedFiles(prev => prev.filter(file => file.filename !== filename));
      
      console.log("Arquivo deletado com sucesso:", filename);

    } catch (err) {
      console.error('Erro ao deletar arquivo:', err);
      setUploadStatus('error');
      setUploadMessage(err instanceof Error ? err.message : 'Erro desconhecido ao deletar arquivo');
      
      // Limpa a mensagem após 5 segundos
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadMessage('');
      }, 5000);
    } finally {
      setDeletingFile(null);
    }
  };

  // ===============================
  // Função para abrir seletor de arquivo
  // ===============================
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  // ===============================
  // Busca dados do projeto via API
  // ===============================
  useEffect(() => {
    const fetchProject = async () => {
      // Verifica se há ID na URL
      if (!projectId) {
        setError("Projeto não encontrado");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const token = localStorage.getItem("access_token");

        if (!token) {
          router.push("/login");
          return;
        }

        // Busca todos os projetos e filtra pelo ID
        const response = await fetch("http://localhost:8000/projects", {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("token_type");
            router.push("/login");
            return;
          }
          throw new Error("Erro ao carregar projeto");
        }

        const data = await response.json();
        
        // Encontra o projeto pelo ID
        const foundProject = data.projects.find(
          (p: Project) => p.id === parseInt(projectId)
        );

        if (!foundProject) {
          setError("Projeto não encontrado");
        } else {
          setProject(foundProject);
          // Busca arquivos do projeto após carregar os dados do projeto
          await fetchProjectFiles();
        }

      } catch (err) {
        console.error("Erro ao buscar projeto:", err);
        setError(err instanceof Error ? err.message : "Erro desconhecido");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProject();
  }, [projectId, router]);

  
  // ===============================
  // CHAT
  // ===============================
  const sendMessage = async () => {
    if (!input.trim() || !projectId) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const userMessage = input;
    
    // Adiciona mensagem do usuário e placeholder para o assistente
    setMessages(prev => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "", toolCalls: [], toolResults: [] },
    ]);

    setInput("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // ✅ Acumuladores locais
    let accumulatedContent = "";
    let accumulatedToolCalls: ToolCall[] = [];
    let accumulatedToolResults: ToolResult[] = [];

    try {
      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: Number(projectId),
          query: userMessage,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Erro na requisição: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Stream não suportado pelo navegador");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        let boundary = buffer.indexOf("\n\n");
        
        while (boundary !== -1) {
          const message = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          
          const lines = message.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const jsonStr = line.slice(6).trim();
              
              if (!jsonStr) continue;
              
              try {
                const data = JSON.parse(jsonStr);

                switch (data.type) {
                  case "token":
                    // ✅ Acumula localmente
                    accumulatedContent += data.content;
                    
                    // ✅ Atualiza o estado de uma vez
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg?.role === "assistant") {
                        lastMsg.content = accumulatedContent;
                        lastMsg.toolCalls = accumulatedToolCalls;
                        lastMsg.toolResults = accumulatedToolResults;
                      }
                      return updated;
                    });
                    break;

                  case "tool_call":
                    accumulatedToolCalls.push({
                      tool_name: data.tool_name,
                      tool_id: data.tool_id,
                      args: data.args,
                    });
                    
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg?.role === "assistant") {
                        lastMsg.content = accumulatedContent;
                        lastMsg.toolCalls = [...accumulatedToolCalls];
                        lastMsg.toolResults = accumulatedToolResults;
                      }
                      return updated;
                    });
                    break;

                  case "tool_result":
                    accumulatedToolResults.push({
                      tool_name: data.tool_name,
                      content: data.content,
                    });
                    
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg?.role === "assistant") {
                        lastMsg.content = accumulatedContent;
                        lastMsg.toolCalls = accumulatedToolCalls;
                        lastMsg.toolResults = [...accumulatedToolResults];
                      }
                      return updated;
                    });
                    break;

                  case "done":
                    console.log("Streaming concluído");
                    break;

                  case "error":
                    accumulatedContent = `❌ Erro: ${data.message}`;
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg?.role === "assistant") {
                        lastMsg.content = accumulatedContent;
                      }
                      return updated;
                    });
                    break;
                }
              } catch (parseError) {
                console.error("Erro ao parsear JSON:", jsonStr, parseError);
              }
            }
          }
          
          boundary = buffer.indexOf("\n\n");
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        console.error("Erro no streaming:", err);
        
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg?.role === "assistant") {
            lastMsg.content = `❌ Erro: ${err.message}`;
          }
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  // STOP STREAMING
  const stopStreaming = () => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Carregando projeto...</span>
      </div>
    );
  }

  // Error state
  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-destructive">{error || "Projeto não encontrado"}</p>
        <Link href="/projects">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar para Projetos
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-72 border-r bg-muted/30 flex flex-col h-full">
        {/* Project Info */}
        <div className="p-4 border-b shrink-0">
          <Link href="/projects" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-3">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
          <h2 className="font-semibold text-lg">{project.title}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {project.description || "Sem descrição"}
          </p>
          <p className="text-xs text-muted-foreground/50 mt-2">
            Ref: #{project.id}
          </p>
        </div>

        {/* Files List */}
        <div className="flex-1 p-4 overflow-hidden min-h-0">
          <h3 className="text-sm font-medium mb-3">Arquivos PDF</h3>
          <ScrollArea className="h-full">
            <div className="space-y-2 pr-4">
              {filesLoading ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground mr-2" />
                  <span className="text-sm text-muted-foreground">Carregando...</span>
                </div>
              ) : uploadedFiles.length > 0 ? (
                uploadedFiles.map((file, index) => (
                  <div
                    key={`${file.filename}-${index}`}
                    className="flex items-center justify-between p-2 rounded-md bg-background hover:bg-accent/50 group"
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <span className="text-sm truncate block">{file.filename}</span>
                        <span className="text-xs text-muted-foreground">{file.chunks_count} chunks</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handleDeleteFile(file.filename)}
                      disabled={deletingFile === file.filename}
                    >
                      {deletingFile === file.filename ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Trash2 className="h-3 w-3 text-destructive" />
                      )}
                    </Button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Nenhum arquivo enviado ainda
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Upload Section */}
        <div className="p-4 border-t shrink-0 space-y-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <Button
            onClick={triggerFileInput}
            disabled={isUploading}
            variant="outline"
            className="w-full"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Enviando... {uploadProgress}%
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload PDF
              </>
            )}
          </Button>

          {/* Upload Status */}
          {uploadStatus !== 'idle' && (
            <div className={`flex items-center gap-2 text-sm p-2 rounded ${
              uploadStatus === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300' :
              'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
            }`}>
              {uploadStatus === 'success' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <XCircle className="h-4 w-4" />
              )}
              <span className="text-xs">{uploadMessage}</span>
            </div>
          )}
        </div>
      </aside>

      
      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full">
        {/* Chat Messages */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="max-w-4xl mx-auto space-y-4 p-4">
              {messages.map((msg, idx) => (
                <div key={idx}>
                  {/* Mensagem do Usuário */}
                  {msg.role === "user" && (
                    <Card className="py-0 bg-gray-200 ml-auto max-w-[50%]">
                      <CardContent className="p-3 text-sm font-bold text-gray-900 whitespace-pre-wrap">
                        {msg.content}
                      </CardContent>
                    </Card>
                  )}

                  {/* Mensagem do Assistente */}
                  {msg.role === "assistant" && (
                    <div className="space-y-2">
                      {/* Tool Calls - ACIMA da resposta */}
                      {msg.toolCalls && msg.toolCalls.length > 0 && (
                        <div className="space-y-1">
                          {msg.toolCalls.map((tool, toolIdx) => (
                            <div
                              key={toolIdx}
                              className="flex items-center gap-2 text-xs text-muted-foreground bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-2 rounded"
                            >
                              <Wrench className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                              <span>
                                Executando: <strong className="text-amber-700 dark:text-amber-300">{tool.tool_name}</strong>
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Tool Results - ACIMA da resposta, com toggle */}
                      {msg.toolResults && msg.toolResults.length > 0 && (
                        <div className="space-y-1">
                          {msg.toolResults.map((result, resultIdx) => {
                            const key = `${idx}-${resultIdx}`;
                            const isExpanded = expandedToolResults.has(key);
                            
                            return (
                              <div
                                key={resultIdx}
                                className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded overflow-hidden"
                              >
                                {/* Header clicável */}
                                <button
                                  onClick={() => toggleToolResult(idx, resultIdx)}
                                  className="w-full flex items-center justify-between gap-2 text-xs p-2 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <FileSearch className="h-3 w-3 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                                    <span className="font-medium text-blue-700 dark:text-blue-300">
                                      {result.tool_name}
                                    </span>
                                  </div>
                                  {isExpanded ? (
                                    <ChevronDown className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                                  ) : (
                                    <ChevronRight className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                                  )}
                                </button>

                                {/* Conteúdo expansível */}
                                {isExpanded && (
                                  <div className="px-2 pb-2 text-xs text-muted-foreground border-t border-blue-200 dark:border-blue-800 pt-2">
                                    <pre className="whitespace-pre-wrap font-mono text-xs">
                                      {result.content}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Resposta Final - COM MARKDOWN */}
                      {msg.content && (
                        <Card className="bg-background">
                          <CardContent className="p-3 text-sm prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown
                              components={{
                                // Customiza elementos específicos se necessário
                                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                                li: ({ children }) => <li className="mb-1">{children}</li>,
                                code: ({ inline, children, ...props }: any) => 
                                  inline ? (
                                    <code className="bg-muted px-1 py-0.5 rounded text-xs" {...props}>
                                      {children}
                                    </code>
                                  ) : (
                                    <code className="block bg-muted p-2 rounded text-xs overflow-x-auto" {...props}>
                                      {children}
                                    </code>
                                  ),
                                pre: ({ children }) => <pre className="bg-muted p-2 rounded overflow-x-auto mb-2">{children}</pre>,
                                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-4 border-muted pl-3 italic my-2">
                                    {children}
                                  </blockquote>
                                ),
                                a: ({ children, href }) => (
                                  <a href={href} className="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
                                    {children}
                                  </a>
                                ),
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {isStreaming && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Gerando resposta...
                </div>
              )}

              {/* Elemento invisível para scroll */}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Input Area - mantém igual */}
        <div className="border-t p-4 shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Digite sua pergunta..."
                disabled={isStreaming}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />

              <Button
                size="icon"
                className="h-[60px] w-[60px]"
                onClick={isStreaming ? stopStreaming : sendMessage}
              >
                {isStreaming ? (
                  <StopCircle className="h-5 w-5" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>

            {uploadedFiles.length === 0 && (
              <p className="text-xs text-muted-foreground mt-2 text-center">
                ⚠️ Nenhum documento enviado. Faça upload de PDFs para começar a conversar.
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ===============================
// Componente Principal com Suspense
// ===============================
export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen overflow-hidden">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
