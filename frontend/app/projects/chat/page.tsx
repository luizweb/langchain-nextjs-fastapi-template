"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, Trash2, Upload, Send, ArrowLeft, Loader2, CheckCircle, XCircle, StopCircle, Wrench, FileSearch, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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

type ChatMessage = {
  role: "user" | "assistant";
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
// Constantes
// ===============================
const API_URL = "http://localhost:8000";
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// ===============================
// Hook de autenticação
// ===============================
const useAuth = () => {
  const router = useRouter();

  const getToken = () => localStorage.getItem("access_token");

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    router.push("/login");
  };

  const checkAuth = async (response: Response) => {
    if (response.status === 401) {
      logout();
      return false;
    }
    return true;
  };

  return { getToken, logout, checkAuth };
};

// ===============================
// Componente interno que usa useSearchParams
// ===============================
function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("id");
  const { getToken, logout, checkAuth } = useAuth();

  // Estados do projeto e arquivos
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(true);

  // Estados de upload
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Estados de exclusão
  const [deletingFile, setDeletingFile] = useState<string | null>(null);
  const [fileToDelete, setFileToDelete] = useState<string | null>(null);

  // Estados do chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [expandedToolResults, setExpandedToolResults] = useState<Set<string>>(new Set());
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ===============================
  // Funções auxiliares
  // ===============================
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const showMessage = (status: 'success' | 'error', message: string, duration = 3000) => {
    setUploadStatus(status);
    setUploadMessage(message);
    setTimeout(() => {
      setUploadStatus('idle');
      setUploadMessage('');
    }, duration);
  };

  const toggleToolResult = (messageIdx: number, resultIdx: number) => {
    const key = `${messageIdx}-${resultIdx}`;
    setExpandedToolResults(prev => {
      const newSet = new Set(prev);
      newSet.has(key) ? newSet.delete(key) : newSet.add(key);
      return newSet;
    });
  };

  // ===============================
  // API: Buscar arquivos do projeto
  // ===============================
  const fetchProjectFiles = async () => {
    if (!projectId) return;

    try {
      setFilesLoading(true);
      const token = getToken();
      if (!token) return logout();

      const response = await fetch(`${API_URL}/chat/files/${projectId}`, {
        headers: { "Authorization": `Bearer ${token}` },
      });

      if (!(await checkAuth(response))) return;
      if (!response.ok) throw new Error("Erro ao carregar arquivos");

      const data = await response.json();
      setUploadedFiles(data.files || []);
    } catch (err) {
      console.error("Erro ao buscar arquivos:", err);
      setUploadedFiles([]);
    } finally {
      setFilesLoading(false);
    }
  };

  // ===============================
  // API: Upload de arquivo
  // ===============================
  const uploadFile = async (file: File) => {
    if (file.type !== 'application/pdf') {
      return showMessage('error', 'Apenas arquivos PDF são permitidos.', 5000);
    }

    if (file.size > MAX_FILE_SIZE) {
      return showMessage('error', 'O arquivo deve ter no máximo 10MB.', 5000);
    }

    if (!projectId) {
      return showMessage('error', 'ID do projeto não encontrado.');
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadStatus('idle');

      const token = getToken();
      if (!token) return logout();

      const progressInterval = setInterval(() => {
        setUploadProgress(prev => prev >= 90 ? 90 : prev + 10);
      }, 200);

      const formData = new FormData();
      formData.append('uploaded_file', file);

      const response = await fetch(`${API_URL}/chat/upload/${projectId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!(await checkAuth(response))) return;
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Erro no upload: ${response.status}`);
      }

      showMessage('success', 'Arquivo enviado com sucesso!', 5000);
      await fetchProjectFiles();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Erro no upload:', err);
      showMessage('error', err instanceof Error ? err.message : 'Erro desconhecido no upload', 5000);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // ===============================
  // Handlers de drag & drop
  // ===============================
  const handleDragEvents = (e: React.DragEvent, isDragging: boolean) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragleave' && e.currentTarget !== e.target) return;
    setIsDragging(isDragging);
  };

  const handleDrop = async (e: React.DragEvent) => {
    handleDragEvents(e, false);
    const file = e.dataTransfer.files?.[0];
    if (file) await uploadFile(file);
  };

  // ===============================
  // API: Deletar arquivo
  // ===============================
  const handleDeleteFile = async () => {
    if (!fileToDelete || !projectId) return;

    try {
      setDeletingFile(fileToDelete);
      const token = getToken();
      if (!token) return logout();

      const response = await fetch(
        `${API_URL}/chat/files/${projectId}/${encodeURIComponent(fileToDelete)}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (!(await checkAuth(response))) return;
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Erro ao deletar arquivo: ${response.status}`);
      }

      setUploadedFiles(prev => prev.filter(file => file.filename !== fileToDelete));
      showMessage('success', 'Arquivo deletado com sucesso!');
    } catch (err) {
      console.error('Erro ao deletar arquivo:', err);
      showMessage('error', err instanceof Error ? err.message : 'Erro desconhecido ao deletar arquivo');
    } finally {
      setDeletingFile(null);
      setFileToDelete(null);
    }
  };

  // ===============================
  // API: Enviar mensagem do chat
  // ===============================
  const sendMessage = async () => {
    if (!input.trim() || !projectId) return;

    const token = getToken();
    if (!token) return logout();

    const userMessage = input;
    setMessages(prev => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "", toolCalls: [], toolResults: [] },
    ]);
    setInput("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let accumulatedContent = "";
    let accumulatedToolCalls: ToolCall[] = [];
    let accumulatedToolResults: ToolResult[] = [];

    const updateLastMessage = () => {
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
    };

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
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

      if (!response.ok) throw new Error(`Erro na requisição: ${response.status}`);
      if (!response.body) throw new Error("Stream não suportado pelo navegador");

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
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const data = JSON.parse(jsonStr);

              switch (data.type) {
                case "token":
                  accumulatedContent += data.content;
                  updateLastMessage();
                  break;
                case "tool_call":
                  accumulatedToolCalls.push({
                    tool_name: data.tool_name,
                    tool_id: data.tool_id,
                    args: data.args,
                  });
                  updateLastMessage();
                  break;
                case "tool_result":
                  accumulatedToolResults.push({
                    tool_name: data.tool_name,
                    content: data.content,
                  });
                  updateLastMessage();
                  break;
                case "error":
                  accumulatedContent = `❌ Erro: ${data.message}`;
                  updateLastMessage();
                  break;
              }
            } catch (parseError) {
              console.error("Erro ao parsear JSON:", jsonStr, parseError);
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

  // ===============================
  // Buscar projeto ao montar
  // ===============================
  useEffect(() => {
    const fetchProject = async () => {
      if (!projectId) {
        setError("Projeto não encontrado");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const token = getToken();
        if (!token) return logout();

        const response = await fetch(`${API_URL}/projects`, {
          headers: { "Authorization": `Bearer ${token}` },
        });

        if (!(await checkAuth(response))) return;
        if (!response.ok) throw new Error("Erro ao carregar projeto");

        const data = await response.json();
        const foundProject = data.projects.find((p: Project) => p.id === parseInt(projectId));

        if (!foundProject) {
          setError("Projeto não encontrado");
        } else {
          setProject(foundProject);
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
  }, [projectId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ===============================
  // Estados de carregamento e erro
  // ===============================
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Carregando projeto...</span>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
        <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
          <XCircle className="h-8 w-8 text-destructive" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold">Projeto não encontrado</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            {error || "Este projeto não existe ou você não tem permissão para acessá-lo. Verifique o link ou escolha outro projeto da sua lista."}
          </p>
        </div>
        <Link href="/projects">
          <Button>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Ver meus projetos
          </Button>
        </Link>
      </div>
    );
  }

  // ===============================
  // Render principal
  // ===============================
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
                      onClick={() => setFileToDelete(file.filename)}
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
            onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
            className="hidden"
          />

          <div
            onDragEnter={(e) => handleDragEvents(e, true)}
            onDragLeave={(e) => handleDragEvents(e, false)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
            className={`
              relative border-2 border-dashed rounded-lg p-4 transition-all cursor-pointer
              ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/50'}
              ${isUploading ? 'cursor-not-allowed opacity-60' : ''}
            `}
          >
            <div className="flex flex-col items-center gap-2 text-center pointer-events-none">
              {isUploading ? (
                <>
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <div className="w-full space-y-1">
                    <p className="text-xs font-medium">Enviando arquivo...</p>
                    <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all duration-300 ease-out"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">{uploadProgress}%</p>
                  </div>
                </>
              ) : (
                <>
                  <Upload className={`h-6 w-6 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
                  <div>
                    <p className="text-sm font-medium">
                      {isDragging ? 'Solte o arquivo aqui' : 'Clique ou arraste um PDF'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Máximo 10MB</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {uploadStatus !== 'idle' && (
            <div className={`flex items-center gap-2 text-sm p-2 rounded animate-in fade-in slide-in-from-top-2 ${
              uploadStatus === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300' :
              'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
            }`}>
              {uploadStatus === 'success' ? (
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 flex-shrink-0" />
              )}
              <span className="text-xs">{uploadMessage}</span>
            </div>
          )}
        </div>
      </aside>

      {/* Diálogo de Confirmação de Exclusão */}
      {fileToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in">
          <div className="bg-background border rounded-lg p-6 max-w-md w-full mx-4 animate-in zoom-in-95 duration-200">
            <h3 className="text-lg font-semibold mb-2">Confirmar exclusão</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Tem certeza que deseja deletar <span className="font-medium text-foreground">{fileToDelete}</span>?
              Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setFileToDelete(null)} disabled={!!deletingFile}>
                Cancelar
              </Button>
              <Button variant="destructive" onClick={handleDeleteFile} disabled={!!deletingFile}>
                {deletingFile ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Deletando...
                  </>
                ) : (
                  'Deletar'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full">
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="max-w-4xl mx-auto space-y-4 p-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-12">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <Send className="h-8 w-8 text-primary" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold">Pronto para conversar!</h3>
                    <p className="text-sm text-muted-foreground max-w-md">
                      {uploadedFiles.length > 0
                        ? `Faça perguntas sobre os ${uploadedFiles.length} documento${uploadedFiles.length > 1 ? 's' : ''} carregado${uploadedFiles.length > 1 ? 's' : ''} ou converse sobre qualquer assunto.`
                        : 'Você pode fazer perguntas sobre qualquer assunto. Para consultar documentos específicos, faça upload de PDFs na barra lateral.'
                      }
                    </p>
                  </div>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div key={idx}>
                  {msg.role === "user" && (
                    <Card className="py-0 bg-gray-200 ml-auto max-w-[50%]">
                      <CardContent className="p-3 text-sm font-bold text-gray-900 whitespace-pre-wrap">
                        {msg.content}
                      </CardContent>
                    </Card>
                  )}

                  {msg.role === "assistant" && (
                    <div className="space-y-2">
                      {msg.toolCalls && msg.toolCalls.length > 0 && (
                        <div className="space-y-1">
                          {msg.toolCalls.map((tool, toolIdx) => (
                            <div
                              key={toolIdx}
                              className="flex items-center gap-2 text-xs bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-2 rounded"
                            >
                              <Wrench className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                              <span>
                                Executando: <strong className="text-amber-700 dark:text-amber-300">{tool.tool_name}</strong>
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

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

                      {msg.content && (
                        <Card className="bg-background">
                          <CardContent className="p-3 text-sm prose prose-sm dark:prose-invert max-w-none prose-table:text-sm">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
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

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        <div className="border-t p-4 shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  uploadedFiles.length > 0
                    ? "Pergunte sobre os documentos ou qualquer outro assunto..."
                    : "Digite sua pergunta..."
                }
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
                onClick={isStreaming ? () => abortControllerRef.current?.abort() : sendMessage}
              >
                {isStreaming ? (
                  <StopCircle className="h-5 w-5" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>

            {uploadedFiles.length === 0 && messages.length > 0 && (
              <p className="text-xs text-muted-foreground mt-2 text-center">
                💡 Dica: Faça upload de PDFs para consultar documentos específicos
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}