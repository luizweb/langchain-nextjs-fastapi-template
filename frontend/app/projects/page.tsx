"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardAction,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Empty,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from "@/components/ui/empty";
import { FileText, Plus, MoreHorizontal, FolderOpen, Loader2 } from "lucide-react";
import Link from "next/link";

// ===============================
// DADOS PLACEHOLDER (COMENTADO)
// ===============================
// const placeholderProjects: Project[] = [
//   {
//     id: 1,
//     title: "Projeto E-commerce",
//     description: "Sistema de loja virtual com carrinho de compras e pagamentos.",
//     fileCount: 24,
//   },
//   {
//     id: 2,
//     title: "App de Finanças",
//     description: "Aplicativo para controle de gastos e investimentos pessoais.",
//     fileCount: 18,
//   },
//   {
//     id: 3,
//     title: "Dashboard Analytics",
//     description: "Painel de visualização de dados e métricas em tempo real.",
//     fileCount: 32,
//   },
//   {
//     id: 4,
//     title: "Blog Pessoal",
//     description: "Site de blog com sistema de posts e comentários.",
//     fileCount: 12,
//   },
// ];

// ===============================
// Tipo conforme resposta da API
// GET /projects retorna: { projects: [...] }
// ===============================
type Project = {
  id: number;
  user_id: number;
  title: string;
  description: string;
  llm_prompt: string;
};

// Tipo para resposta da API
type ApiResponse = {
  projects: Project[];
};

// Tipo para resposta da API de arquivos
type FilesResponse = {
  files: any[];
  total_files: number;
  total_chunks: number;
};

// Tipo para armazenar quantidade de arquivos por projeto
type ProjectFilesCount = {
  [projectId: number]: number;
};

export default function ProjectsPage() {
  const router = useRouter();
  
  // ===============================
  // Estado para verificação de autenticação
  // ===============================
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  
  // ===============================
  // Estados para dados da API
  // ===============================
  const [projects, setProjects] = useState<Project[]>([]);
  const [filesCount, setFilesCount] = useState<ProjectFilesCount>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // ===============================
  // Estados para modais e formulários
  // ===============================
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);

  // ===============================
  // Verificação de autenticação
  // Redireciona para /login se não houver token
  // ===============================
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    
    if (!token) {
      // Não está logado, redireciona para login
      router.push("/login");
    } else {
      // Está logado, permite acesso
      setIsAuthChecking(false);
    }
  }, [router]);

  // ===============================
  // Função para buscar quantidade de arquivos de um projeto
  // ===============================
  const fetchProjectFilesCount = async (projectId: number) => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      const response = await fetch(`${API_URL}/chat/files/${projectId}`, {
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
        return; // Não marca como erro, apenas não atualiza o count
      }

      const data: FilesResponse = await response.json();
      setFilesCount(prev => ({
        ...prev,
        [projectId]: data.total_files || 0
      }));

    } catch (err) {
      console.error(`Erro ao buscar arquivos do projeto ${projectId}:`, err);
      // Define count como 0 em caso de erro
      setFilesCount(prev => ({
        ...prev,
        [projectId]: 0
      }));
    }
  };

  // ===============================
  // Função para buscar quantidade de arquivos de todos os projetos
  // ===============================
  const fetchAllProjectsFilesCount = async (projectsList: Project[]) => {
    setFilesLoading(true);
    try {
      const promises = projectsList.map(project => fetchProjectFilesCount(project.id));
      await Promise.allSettled(promises);
    } finally {
      setFilesLoading(false);
    }
  };

  // ===============================
  // Busca projetos da API quando autenticado
  // ===============================
  useEffect(() => {
    if (isAuthChecking) return;

    const fetchProjects = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const token = localStorage.getItem("access_token");

        const response = await fetch(`${API_URL}/projects`, {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401) {
            // Token inválido ou expirado
            localStorage.removeItem("access_token");
            localStorage.removeItem("token_type");
            router.push("/login");
            return;
          }
          throw new Error(`Erro ao carregar projetos: ${response.status}`);
        }

        const data: ApiResponse = await response.json();
        setProjects(data.projects);
        
        // Busca quantidade de arquivos para cada projeto
        await fetchAllProjectsFilesCount(data.projects);

      } catch (err) {
        console.error("Erro ao buscar projetos:", err);
        setError(err instanceof Error ? err.message : "Erro desconhecido");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, [isAuthChecking, router]);

  // Mostra loading enquanto verifica autenticação
  if (isAuthChecking) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Verificando autenticação...</span>
      </div>
    );
  }

  const handleEditClick = (e: React.MouseEvent, project: Project) => {
    e.preventDefault();
    e.stopPropagation();
    setEditTitle(project.title);
    setEditDescription(project.description);
    setEditingProject(project);
  };

  // ===============================
  // Função para salvar edição (PUT)
  // ===============================
  const handleSave = async () => {
    if (!editingProject) return;

    try {
      setIsSaving(true);
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch(`${API_URL}/projects/${editingProject.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: editTitle,
          description: editDescription,
          llm_prompt: editingProject.llm_prompt || "",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao atualizar projeto");
      }

      const updatedProject = await response.json();

      // Atualiza o projeto na lista
      setProjects(projects.map(p => 
        p.id === editingProject.id ? updatedProject : p
      ));
      
      console.log("Projeto atualizado com sucesso:", updatedProject);
      setEditingProject(null);

    } catch (err) {
      console.error("Erro ao salvar projeto:", err);
      setError(err instanceof Error ? err.message : "Erro ao atualizar projeto");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, project: Project) => {
    e.preventDefault();
    e.stopPropagation();
    setDeletingProject(project);
  };

  // ===============================
  // Função para excluir projeto (DELETE)
  // ===============================
  const handleConfirmDelete = async () => {
    if (!deletingProject) return;

    try {
      setIsDeleting(true);
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch(`${API_URL}/projects/${deletingProject.id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao excluir projeto");
      }

      // Remove o projeto da lista
      setProjects(projects.filter(p => p.id !== deletingProject.id));
      
      // Remove a contagem de arquivos do projeto excluído
      setFilesCount(prev => {
        const newCount = { ...prev };
        delete newCount[deletingProject.id];
        return newCount;
      });
      
      console.log("Projeto excluído com sucesso:", deletingProject);
      setDeletingProject(null);

    } catch (err) {
      console.error("Erro ao excluir projeto:", err);
      setError(err instanceof Error ? err.message : "Erro ao excluir projeto");
      setDeletingProject(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // ===============================
  // Função para criar projeto (POST)
  // ===============================
  const handleCreateProject = async () => {
    if (!newTitle.trim()) return;

    try {
      setIsCreating(true);
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch(`${API_URL}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: newTitle,
          description: newDescription,
          llm_prompt: "",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao criar projeto");
      }

      const newProject = await response.json();
      
      // Adiciona o novo projeto à lista
      setProjects([...projects, newProject]);
      
      // Busca quantidade de arquivos para o novo projeto
      await fetchProjectFilesCount(newProject.id);
      
      console.log("Projeto criado com sucesso:", newProject);
      setNewTitle("");
      setNewDescription("");
      setIsCreateModalOpen(false);

    } catch (err) {
      console.error("Erro ao criar projeto:", err);
      setError(err instanceof Error ? err.message : "Erro ao criar projeto");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Meus Projetos</h1>
        <Button onClick={() => setIsCreateModalOpen(true)} className="cursor-pointer">
          <Plus className="h-4 w-4 mr-2" />
          Novo Projeto
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Carregando projetos...</span>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex items-center justify-center py-12 text-destructive">
          <p>Erro: {error}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && projects.length === 0 && (
        <Empty className="border min-h-[400px]">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <FolderOpen className="h-6 w-6" />
            </EmptyMedia>
            <EmptyTitle>Nenhum projeto encontrado</EmptyTitle>
            <EmptyDescription>
              Você ainda não criou nenhum projeto. Comece criando seu primeiro projeto para organizar seus arquivos.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Criar Primeiro Projeto
            </Button>
          </EmptyContent>
        </Empty>
      )}

      {/* Projects grid */}
      {!isLoading && !error && projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {projects.map((project) => (
            <Link href={`/projects/chat?id=${project.id}`} key={project.id}>
            <Card className="py-4 cursor-pointer hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{project.title}</CardTitle>
                <CardDescription className="text-xs line-clamp-2">
                  {project.description || "Sem descrição"}
                </CardDescription>
                <CardAction>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.preventDefault()}>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => handleEditClick(e, project)}>
                        Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-destructive" 
                        onClick={(e) => handleDeleteClick(e, project)}
                      >
                        Excluir
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardAction>
              </CardHeader>
              <CardContent className="py-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span>
                    {filesLoading ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin inline mr-1" />
                        Carregando...
                      </>
                    ) : (
                      `${filesCount[project.id] || 0} arquivo${(filesCount[project.id] || 0) !== 1 ? 's' : ''}`
                    )}
                  </span>
                </div>
              </CardContent>
            </Card>
            </Link>
          ))}
        </div>
      )}

      {/* AlertDialog de Exclusão */}
      <AlertDialog open={!!deletingProject} onOpenChange={(open) => !open && setDeletingProject(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Projeto</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir o projeto <strong>"{deletingProject?.title}"</strong>?
              Esta ação não pode ser desfeita e todos os arquivos associados serão removidos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Excluindo...
                </>
              ) : (
                "Excluir"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Criação */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Novo Projeto</DialogTitle>
            <DialogDescription>
              Crie um novo projeto para organizar seus arquivos.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="newTitle">Título</Label>
              <Input
                id="newTitle"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Nome do projeto"
                disabled={isCreating}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newDescription">Descrição</Label>
              <Textarea
                id="newDescription"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Descreva seu projeto"
                rows={3}
                disabled={isCreating}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)} disabled={isCreating}>
              Cancelar
            </Button>
            <Button onClick={handleCreateProject} disabled={isCreating || !newTitle.trim()}>
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                "Criar Projeto"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Edição */}
      <Dialog open={!!editingProject} onOpenChange={(open) => !open && setEditingProject(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Projeto</DialogTitle>
            <DialogDescription>
              Atualize as informações do seu projeto.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">Título</Label>
              <Input
                id="title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="Nome do projeto"
                disabled={isSaving}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Descrição</Label>
              <Textarea
                id="description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Descreva seu projeto"
                rows={3}
                disabled={isSaving}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingProject(null)} disabled={isSaving}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : (
                "Salvar Alterações"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
