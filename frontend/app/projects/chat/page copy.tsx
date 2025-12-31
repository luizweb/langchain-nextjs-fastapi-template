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
  role: 'user' | 'assistant';
  content: string;
};

type Document = {
  filename: string;
  similarity: string;
  content: string;
};

type ToolInfo = {
  name: string;
  args: any;
};

type Metadata = {
  tools_used: ToolInfo[];
  total_tokens: number;
  documents_count: number;
  documents: Document[];
  query: string;
  project_id: number;
};

// ===============================
// Componente interno que usa useSearchParams
// ===============================
function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("id");
  
  // Estados do projeto
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

  // ===============================
  // Estados para o Chat
  // ===============================
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [toolsExecuting, setToolsExecuting] = useState<ToolInfo[]>([]);
  const [documentsRetrieved, setDocumentsRetrieved] = useState<Document[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para última mensagem
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages, currentResponse]);

  // ===============================
  // Função para enviar mensagem de chat
  // ===============================
  const sendChatMessage = async (query: string) => {
    if (!query.trim() || !projectId) return;

    // Adiciona mensagem do usuário
    const userMessage: ChatMessage = { role: 'user', content: query.trim() };
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setCurrentResponse('');
    setMetadata(null);
    setToolsExecuting([]);
    setDocumentsRetrieved([]);
    setIsChatLoading(true);

    // Cria AbortController para cancelar se necessário
    abortControllerRef.current = new AbortController();

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const response = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: query.trim(),
          project_id: parseInt(projectId)
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }
        throw new Error(`Erro ao enviar mensagem: ${response.status}`);
      }

      // Processa o stream SSE
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Stream não disponível');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Guarda a última linha incompleta

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'content':
                  // Adiciona texto à resposta atual
                  accumulatedResponse += data.data;
                  setCurrentResponse(accumulatedResponse);
                  break;

                case 'tool_start':
                  // Mostra que uma ferramenta está sendo executada
                  setToolsExecuting(prev => [...prev, data.data]);
                  break;

                case 'documents':
                  // Mostra documentos encontrados
                  setDocumentsRetrieved(data.data);
                  break;

                case 'metadata':
                  // Salva metadados finais
                  setMetadata(data.data);
                  break;

                case 'done':
                  // Finaliza e adiciona resposta completa
                  setChatMessages(prev => [...prev, {
                    role: 'assistant',
                    content: accumulatedResponse
                  }]);
                  setCurrentResponse('');
                  setIsChatLoading(false);
                  break;

                case 'error':
                  console.error('Erro:', data.data.message);
                  setIsChatLoading(false);
                  setCurrentResponse('');
                  // Adiciona mensagem de erro
                  setChatMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `❌ Erro: ${data.data.message}`
                  }]);
                  break;
              }
            } catch (parseError) {
              console.error('Erro ao parsear evento SSE:', parseError, line);
            }
          }
        }
      }

    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Erro ao enviar mensagem:', error);
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: `❌ Erro ao enviar mensagem: ${error.message}`
        }]);
      }
      setIsChatLoading(false);
      setCurrentResponse('');
    }
  };

  // ===============================
  // Função para cancelar requisição
  // ===============================
  const cancelChatRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsChatLoading(false);
      setCurrentResponse('');
      setToolsExecuting([]);
    }
  };

  // ===============================
  // Função para lidar com Enter no input
  // ===============================
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage(currentMessage);
    }
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
        <ScrollArea className="flex-1 p-4" ref={chatScrollRef}>
          <div className="max-w-4xl mx-auto space-y-4">
            {chatMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <FileSearch className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Comece a conversar</h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  Faça perguntas sobre os documentos do seu projeto. O assistente irá buscar informações relevantes para te ajudar.
                </p>
              </div>
            ) : (
              <>
                {chatMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}

                {/* Current Response (Streaming) */}
                {currentResponse && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-lg p-4 bg-muted">
                      <p className="text-sm whitespace-pre-wrap">
                        {currentResponse}
                        <span className="inline-block w-2 h-4 bg-foreground ml-1 animate-pulse"></span>
                      </p>
                    </div>
                  </div>
                )}

                {/* Tools Executing */}
                {toolsExecuting.length > 0 && isChatLoading && (
                  <div className="flex justify-start">
                    <Card className="max-w-[80%]">
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                          <Wrench className="h-4 w-4 text-blue-500 animate-pulse" />
                          <span className="text-sm text-muted-foreground">
                            Buscando documentos: <strong>{toolsExecuting[0]?.args?.query}</strong>
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Documents Retrieved */}
                {documentsRetrieved.length > 0 && (
                  <div className="flex justify-start">
                    <Card className="max-w-[80%]">
                      <CardContent className="p-3 space-y-2">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium">
                            {documentsRetrieved.length} documento(s) encontrado(s)
                          </span>
                        </div>
                        {documentsRetrieved.map((doc, idx) => (
                          <div key={idx} className="border-l-2 border-green-500 pl-2 py-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium">{doc.filename}</span>
                              <Badge variant="secondary" className="text-xs">
                                {doc.similarity}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {doc.content}
                            </p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Metadata */}
                {metadata && (
                  <div className="flex justify-center">
                    <div className="text-xs text-muted-foreground flex items-center gap-4">
                      <span>📊 {metadata.total_tokens} tokens</span>
                      <span>📄 {metadata.documents_count} documentos</span>
                      <span>🔧 {metadata.tools_used.length} ferramentas</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4 shrink-0">
          <div className="max-w-4xl mx-auto">
            {isChatLoading && (
              <div className="mb-2 flex justify-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={cancelChatRequest}
                >
                  <StopCircle className="h-4 w-4 mr-2" />
                  Parar geração
                </Button>
              </div>
            )}
            
            <div className="flex gap-2">
              <Textarea
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Digite sua mensagem... (Shift+Enter para nova linha)"
                className="min-h-[60px] max-h-[200px] resize-none"
                disabled={isChatLoading}
              />
              <Button
                onClick={() => sendChatMessage(currentMessage)}
                disabled={!currentMessage.trim() || isChatLoading}
                size="icon"
                className="h-[60px] w-[60px]"
              >
                {isChatLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
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
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}